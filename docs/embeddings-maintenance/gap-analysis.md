# Gap 分析与修复计划：代码 vs spec.md

> **基线**：`docs/embeddings-maintenance/spec.md`（Oracle 审查通过，已修正 M1 + 4 个 Minor）
> **方法**：逐条对照 spec 的每个声明，验证代码是否实现。仅列出 spec 描述为目标但代码未实现的差距（不列 spec 明确标注为"非目标"的项）

---

## Gap 总览

| # | Gap | spec 位置 | 代码现状 | 严重度 | 修复成本 |
|---|---|---|---|---|---|
| G1 | loader 不校验 `matrix.shape[0] == len(node_ids)` | §9 行 1 | loader 只校验 ndim/shape[0]>0/shape[1]>1 | P1 | 低 |
| G2 | loader 不校验 `matrix.shape[1] == index.dim` | §9 行 2 | 同上 | P2 | 低 |
| G3 | loader 不校验 `matrix.shape[1] == meta.dim` | §9 行 3 | loader 不读 meta | P2 | 低 |
| G4 | loader 不校验 `len(node_ids) == meta.node_count` | §9 行 4 | 同上 | P3 | 低 |
| G5 | loader 不校验 `index.model == meta.model` | §9 行 5 | 同上 | P3 | 低 |
| G6 | loader 不校验 sidecar node_id ⊆ graph.json | §9 行 9 | 完全未做 | P1 | 中 |
| G7 | 非 git 项目 desc 变更漏检 | §7.3 盲区 1 | 降级增量只看 new/deleted | P2 | 中 |
| G8 | `graphify query` 不调 staleness 检测 | §7.3 盲区 3 | query 命令零检测 | P2 | 中 |
| G9 | sidecar 写入无原子性 | §4.3 | `np.save`/`write_text` 直接覆盖，9 处（3 npy + 3 index + 3 meta） | P1 | 中 |
| G10 | 增量路径 docstring 错误声明"非 git → 全量" | §3.2（已修正）| `embeddings.py:587-591` docstring 与 spec 矛盾 | P3 | 低 |

---

## 详细分析

### G1: loader 不校验 matrix 行数与 index 长度一致

**spec §9 行 1**：`matrix.shape[0] == len(index.node_ids)` 标注 ❌（未校验）

**代码现状**（`embeddings.py:893-909`）：
```python
matrix = np.load(npy_path)          # 加载矩阵
if matrix.ndim != 2: return None     # 校验 4
if matrix.shape[0] == 0 or matrix.shape[1] <= 1: return None  # 校验 5+6
index_data = json.loads(...)         # 加载 index
node_ids = index_data.get("node_ids", [])
id_to_row = {nid: i for i, nid in enumerate(node_ids)}
return matrix, id_to_row, ...         # 直接返回，不校验 shape[0] == len(node_ids)
```

**影响**：如果 npy 和 index.json 来自不同的 build（写入了 npy 但 index 写入前崩溃），matrix 有 100 行但 node_ids 只有 50 个 → id_to_row 越界或向量 tier 指向错误节点。当前不崩溃——`hybrid_scorer.py:292` 的 `0 <= row < len(sims)` 守卫拦截了行越界，但 score 会被赋给错误的 node_id，召回质量异常。

**修复**：在 loader 返回前加一行校验：
```python
if matrix.shape[0] != len(node_ids):
    return None
```

### G2-G5: loader 不交叉校验 npy / index / meta 三文件一致性

**spec §9 行 2-5**：全部标注 ❌

**代码现状**：loader 只读 npy + index.json，**完全不读 meta.json**。因此无法校验 `dim` / `node_count` / `model` 的三文件一致性。

**影响**：
- G2（`matrix.shape[1] == index.dim`）：index.json 的 dim 字段失真不影响查询（查询用的是 matrix 的实际 shape[1]），但影响 staleness 检测（如果将来有人用 index.dim 做判断）
- G3-G5（meta 一致性）：meta.json 只被 staleness 检测读（`cli.py:1094`），loader 不读，所以 meta 与 npy/index 不一致只影响 staleness 判断准确性

**修复**：loader 可选读 meta 做交叉校验。但考虑 meta 是 staleness 专用文件，query 路径读它会增加 I/O。**建议 G2 在 loader 加一行校验（已有 index_data），G3-G5 不在 loader 做**——改为在 `_write_sidecar_meta` 和 `generate_embeddings_incremental` 写入时保证一致性（build 路径正确性）。

### G6: sidecar 含已删除节点可致查询崩溃

**spec §9 行 9**：sidecar node_id 集合 ⊆ graph.json node_id 集合，标注 ❌

**代码现状**：loader 完全不读 graph.json，只读 sidecar 文件。`HybridScorer` 无 graph node 集合，`vector_scores` 返回 ALL sidecar node_ids（含已删除节点）。

**影响**（严重——可致崩溃，非仅浪费开销）：
1. `hybrid_scorer.py:289-293` — `vector_scores` 返回 ALL sidecar node_ids（含已删除节点）
2. `serve.py:715-725` — Pass 2 对 `vec_sim > 0.40` 的节点执行 `score_by_nid[nid] = ...` → **为已删除节点创建新 key**
3. `serve.py:731` — 排序 lambda 访问 `G.nodes[deleted_nid]` → **KeyError 崩溃**

触发条件：sidecar 含已删除节点 + 该节点与 query 的 cosine sim > 0.40（T4 阈值）。这在 staleness 窗口期（节点删除后 sidecar 未刷新）完全可达。**违反 spec §1 "查询永不崩溃"**。

**修复方案**（两道防线）：
1. `serve.py:716` Pass 2 加 `if nid not in G.nodes(): continue` — 即时防护，阻止已删除节点进入排序
2. `serve.py._load_entry` 传 graph 给 HybridScorer，`vector_scores` 初始化时过滤掉 graph 中不存在的 node_id — 从源头清理

**优先级**：P1（可致崩溃，违反 spec 核心目标）

### G7: 非 git 项目 desc 变更漏检

**spec §7.3 盲区 1**：非 git + 节点数不变（仅 desc 变更）→ 漏检

**代码现状**（`embeddings.py:654-660`）：`_git_diff_changed_node_ids` 返回 None（非 git），fallback 到集合比对，只看 `nid not in id_to_row`（新增）和 `set(id_to_row) - current_ids`（删除），**desc 变更完全漏掉**。

**影响**：非 git 项目用户改了节点 desc，增量刷新不会重新 embed，sidecar 与 graph.json 不同步。staleness 检测的分支 ④（`graph_is_newer and not meta_commit and not graph_commit`）能检测到 graph.json 更新了，但刷新动作是增量——又回到降级增量路径，仍然漏检。

**修复方案**：非 git 项目在增量路径中，对所有 `current_texts` 与 sidecar 中对应的旧文本做**逐节点文本比对**（而非只看 new/deleted）。但这需要逐节点从旧 sidecar 提取文本——sidecar 不存原文，只存向量。**替代方案**：非 git 项目 + 检测到 staleness 时直接走全量（`full=True`），绕过增量的漏检问题。

### G8: `graphify query` 命令不调 staleness 检测

**spec §7.3 盲区 3**：`graphify query` 命令本身不调 staleness 检测，hook 未跑时永远不检测

**代码现状**：`graphify query` 只加载 graph + sidecar，不调 `_check_single_project`。staleness 检测完全依赖 SessionStart hook（`graphify check`）。如果 hook 未跑/被禁用/CLI 直跑，永远不检测。

**影响**：sidecar 陈旧时，query 仍会用陈旧 sidecar（不崩溃——维度守卫保护）。但向量 tier 召回质量下降，用户无感知。

**修复方案**：在 `graphify query` 命令入口加一次轻量 staleness 快检（mtime 比对 meta vs graph），陈旧时打 warning + 同步触发增量刷新（如果变更量小 <1s）或异步触发。

### G9: sidecar 写入无原子性

**spec §4.3**：当前无 temp+rename 原子写

**代码现状**（9 处非原子写入）：
- `embeddings.py:447` — `np.save(paths["npy"], embeddings)`（全量生成）
- `embeddings.py:698` — `np.save(paths["npy"], new_matrix)`（仅删除路径）
- `embeddings.py:742` — `np.save(paths["npy"], new_matrix)`（增量变更路径）
- `embeddings.py:451, 699, 744` — 3 处 `paths["index"].write_text(...)`
- `embeddings.py:485`（被 463/682/704/756 调用）— `_write_sidecar_meta` 的 `paths["meta"].write_text(...)`

全部直接覆盖，无 temp+rename。

**影响**：重建在写 npy 后、写 index.json 前崩溃 → npy 是新的（N' 行），index 是旧的（N 行）→ loader 加载后 shape[0] != len(node_ids) → 如果 G1 修了会被拒，否则进入查询路径可能异常。

**修复方案**：9 处写入改为写 temp 文件 → `os.replace` 原子重命名。`os.replace` 在 Windows 和 POSIX 上都是原子的（Windows 底层 `MoveFileExW` + `MOVEFILE_REPLACE_EXISTING`）。**前提**：temp 文件必须与目标在同一目录（同卷）——跨卷会退化为 copy+delete，失去原子性。

**与 G1 的关系**：G9 防单文件半成品（写入中断），但不保证 3 文件集合原子——npy 写完崩溃、index 未写仍可能不一致。G1 的 `shape[0] == len(node_ids)` 校验是跨文件不一致的兜底安全网。两者互补，都需做。

### G10: docstring 与 spec 矛盾

**spec §3.2**（已修正）：非 git 项目 → 降级增量（非全量）

**代码现状**（`embeddings.py:587-591` docstring）：
```
Falls back to a full rebuild when:
  - graph.json is not tracked by git (no history to diff)
```

**影响**：docstring 声称非 git → 全量，实际代码是降级增量。误导维护者。

**修复**：修正 docstring 与 spec §3.2 对齐。

---

## 修复计划

### Phase 1: 安全防线加固（P1，立即）

| Gap | 修复 | 文件 | 代码量 |
|---|---|---|---|
| G1 | loader 加 `matrix.shape[0] != len(node_ids)` → return None | `embeddings.py:909` 前 | 2 行 |
| G6 | `serve.py:716` Pass 2 加 `if nid not in G.nodes(): continue`（即时防线）；`serve.py._load_entry` 传 graph 给 HybridScorer 过滤已删除 node_id（源头防线） | `serve.py` + `hybrid_scorer.py` | ~25 行 |
| G9 | 9 处写入（3 npy + 3 index + 3 meta）改 temp+`os.replace` 原子写，temp 须同目录 | `embeddings.py:447,451,485,698,699,704,742,744,756` | ~25 行 |
| G10 | 修正 docstring 与 spec §3.2 对齐 | `embeddings.py:587-591` | 3 行 |

**验收**：
- G1：构造 npy 100 行 + index 50 个 node_id 的 sidecar，loader 返回 None
- G6：sidecar 含已删除节点（sim > 0.40），`graphify query` 不崩溃，已删除节点不进排序
- G9：重建进程在 npy 写后 index 写前被杀，重启后 loader 不加载半成品（temp 文件残留，正式文件仍是旧的完整版）
- G10：docstring 与 spec §3.2 一致

### Phase 2: 召回质量保护（P2，近期）

| Gap | 修复 | 文件 | 代码量 |
|---|---|---|---|
| G2 | loader 加 `matrix.shape[1] != index.dim` → return None | `embeddings.py:909` 前 | 2 行 |
| G7 | 非 git 项目 staleness 检测到时走 `full=True`（绕过增量漏检） | `cli.py:1122-1129` | ~5 行 |
| G8 | `graphify query` 入口加 staleness 快检（mtime 比对），陈旧打 warning + 异步触发刷新 | `cli.py` query 命令 | ~15 行 |

**验收**：
- G2：构造 npy dim=384 + index dim=2560 的 sidecar，loader 返回 None
- G7：非 git 项目改 desc 后 `graphify check` 触发全量重建
- G8：hook 未跑时 `graphify query` 仍能检出陈旧并打 warning

### Phase 3: 元数据一致性（P3，可选）

| Gap | 修复 | 文件 | 代码量 |
|---|---|---|---|
| G3-G5 | loader 可选读 meta 做交叉校验，或 build 路径加写入后自校验 | `embeddings.py` | ~10 行 |

**验收**：
- 构造 meta.dim=384 + index.dim=2560 的 sidecar，被识别为不一致

---

## 不修复的项（spec 明确标注为非目标或安全保证已覆盖）

| 项 | 原因 |
|---|---|
| G3-G5 meta 交叉校验在 loader 做 | 增加查询路径 I/O，且 build 路径正确性已保证；仅 staleness 检测读 meta；G3-G5 仍在 Phase 3 build 路径修 |
| 向量数据库（faiss/LanceDB） | spec §11 非目标 |
| 非 git 项目精确 desc 比对 | G7 用 full=True 绕过，不做逐节点文本比对（sidecar 不存原文） |
| sidecar 文件版本管理（多版本保留/回滚） | spec §11 非目标；G9 修的是单次写入原子性（防半成品），不是版本管理 |

> **G9 与版本管理的区分**：G9 通过 temp+`os.replace` 保证**单文件写入**不被中断留下半成品；但它不保留旧版本供回滚。跨文件不一致（npy 新 + index 旧）由 G1 的 `shape[0] == len(node_ids)` 校验兜底——loader 拒绝不一致的 sidecar 对，查询降级纯词法。
