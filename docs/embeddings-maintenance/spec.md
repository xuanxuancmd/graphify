# Spec: Embeddings 数据生成与维护机制

> **关联**：`docs/hybrid-semantic-search/Embedding.md`（后端配置）、`docs/hybrid-semantic-search/spec.md`（打分架构与存储格式）、`docs/retrieval-overall-design/spec.md`（检索双循环）、`docs/retrieval-overall-design/vector-tier-redesign-spec.md`（向量分层权重）
> **适用范围**：embedding sidecar 的生成、持久化、加载、staleness 检测、刷新全生命周期，以及 graph.json 与 sidecar 之间的一致性保证
> **不在范围**：向量打分公式、分层权重、检索召回架构（见关联文档）

---

## 1. 目标

定义 embedding sidecar 从生成到消费的完整维护机制，保证：

1. **查询永不崩溃** — sidecar 陈旧、损坏、空、维度漂移时，查询降级为纯词法，不抛异常
2. **最小刷新成本** — 增量更新只重 embed 变更节点，全量重建仅在必要时触发
3. **可检测的 staleness** — SessionStart hook 与 query 路径都能识别陈旧 sidecar
4. **确定性 provenance** — sidecar 携带 graph_commit / model / dim / node_count，供 staleness 与一致性判断

---

## 2. 机制全景

```
┌─────────────────────────────────────────────────────────────────────┐
│  ① build 生成         graph.json 产出后触发 build_embeddings()       │
│     │                  → generate_embeddings_incremental             │
│     │                  → 全量 or 增量（git diff 决定）                │
│     ▼                                                                │
│  ② 持久化             embedding.npy / .index.json / .meta.json      │
│     │                  (固定文件名, meta 记录 graph_commit)            │
│     ▼                                                                │
│  ③ query 加载         HybridScorer._load → load_embedding_sidecar    │
│     │                  glob *.npy 取 mtime最新, 校验形状与维度         │
│     │                  空/退化/损坏 → 返回 None (降级纯词法)            │
│     ▼                                                                │
│  ④ query 打分         vector_scores → cosine_similarity              │
│     │                  维度不匹配 → 触发异步全量重建 + 降级纯词法        │
│     │                  (cosine_similarity 保留维度守卫作最后防线)        │
│     ▼                                                                │
│  ⑤ staleness 检测     graphify check (SessionStart hook)             │
│     │                  → _check_single_project                       │
│     │                  commit 比对 / mtime 比对 / 非 git 落 node-count │
│     ▼                                                                │
│  ⑥ 刷新触发           post-commit hook / extract / update /          │
│                        watch / SessionStart check / 每日定时任务      │
│                        (Windows schtasks / WSL schtasks.exe / cron)  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. 环节 ① build 生成

### 3.1 统一入口

`build_embeddings()`（`graphify/embeddings.py`）是所有 build 路径的共享入口，被以下调用方共同引用：

| 调用方 | 路径 |
|---|---|
| `graphify .` / `graphify extract .` | `cli.py` extract 命令 |
| `graphify update <path>` | `cli.py` update 命令 |
| git post-commit hook | `watch.py` `_rebuild_code` |
| `--watch` 文件保存 | `watch.py` `_rebuild_code` |
| graphify skill | SKILL.md Step 5.5 |

集中入口避免路径漂移：desc 变更无论经哪条路径触发，都会刷新 sidecar。

### 3.2 增量决策树

`generate_embeddings_incremental()` 的决策：

| 条件 | 动作 |
|---|---|
| `full=True`（定时任务） | 全量重建 |
| 无 sidecar / 损坏 / 不可读 | 全量重建 |
| 模型变更（meta.model != config model） | 全量重建（维度可能不同） |
| `matrix.shape[1] != existing_dim` | 全量重建（维度不一致） |
| git diff 可用且变更节点 > 50% `to_embed` | 全量重建（增量不划算） |
| git diff 可用且变更节点 ≤ 50% | 增量：`git diff <old_commit>..HEAD -- graph.json` 找变更 node_id，精确比对 desc 后 re-embed |
| **非 git 项目**（`old_commit` 为空） | **降级增量**：集合比对，只 re-embed 新增节点 + 移除已删除节点；**desc 变更漏检**（见 §7.3 盲区） |
| 无变更（`to_embed` 为空且无删除） | 仅刷新 meta 的 `graph_commit`，不重新 embed |

增量路径只重新 embed **desc/rationale 实际变化**的节点（用 `_extract_embed_text_from_git_version` 精确比对，而非仅看 node_id 出现在 diff 中）。未变更节点保留原向量；删除节点从索引中移除。

### 3.3 文本源

`_node_embed_text(node)` 的 fallback 链：

```
desc（docstring / 正文首段）
  ↓ 为空时
rationale（LLM Tier 2 抽取的设计动机）
  ↓ 为空时
返回 "" → 节点被跳过，不进 sidecar 索引
```

**不向量化的字段**：`norm_label` / `nid` / `source_file` / `source_tokens` — 路径信息只走词法 tier，避免目录结构巧合污染 cosine 相似度。

### 3.4 空语料处理

当所有节点都无 desc/rationale（`not embeddable`）时：
- 写 `.meta.json`（`node_count=0`, `dim=0`），让 staleness 检测知道 build 曾尝试
- **不写** `.npy` / `.index.json` — loader 找不到 npy 即返回 None，`HybridScorer.available=False`，查询降级纯词法
- 不写退化占位矩阵（如 `(0,1)` shape）—— 这种形状会通过 `ndim==2` 检查被当可用，在 matmul 处崩溃

---

## 4. 环节 ② 持久化

### 4.1 文件布局

```
<graph_dir>/embeddings/
├── embedding.npy            # np.ndarray((N, D), dtype=float32) — N=节点数, D=embedding 维度
├── embedding.index.json     # {"node_ids": [...], "model": "...", "dim": D}
└── embedding.meta.json      # {"generated_at", "node_count", "dim", "model", "backend", "graph_commit"}
```

文件名固定为 `embedding.*`（非 model-slugged）。实际模型名存在 `.meta.json` 和 `.index.json` 内部。loader 按 mtime 取最新 npy，兼容历史遗留的 model-slugged 文件。

### 4.2 meta provenance

`_write_sidecar_meta()` 写入的字段：

| 字段 | 来源 | 用途 |
|---|---|---|
| `generated_at` | UTC ISO timestamp | 审计 |
| `node_count` | len(embeddable nodes) | staleness 检测（非 git 项目） |
| `dim` | embeddings.shape[1] | 一致性校验 |
| `model` | 实际使用的 embedding model | 模型漂移检测 |
| `backend` | embedding backend 名称 | 审计 |
| `graph_commit` | graph.json 的 `built_at_commit` 或 `git HEAD` | **staleness 检测的权威信号** |

`graph_commit` 为空时（graph.json 不被 git 跟踪），staleness 检测降级为 node-count + mtime 比对。

### 4.3 写入方式

`np.save()` + `write_text()` 直接覆盖。当前无 temp+rename 原子写——重建在 npy 写完后、index 写前崩溃会留下不一致的 sidecar 对。loader 的形状校验（§5）能挡住这类残缺文件使其不进查询路径。

---

## 5. 环节 ③ query 加载

### 5.1 loader 校验链

`load_embedding_sidecar(graph_dir)` 的校验顺序，任一失败返回 None（`HybridScorer.available=False`，降级纯词法）：

| # | 校验 | 失败原因 | 行为 |
|---|---|---|---|
| 1 | `embeddings/` 目录存在 | 未配置 backend / 首次运行 | 返回 None |
| 2 | glob `*.npy` 非空 | 无 sidecar | 返回 None |
| 3 | 对应 `.index.json` 存在 | 残缺写入 | 返回 None |
| 4 | `matrix.ndim == 2` | 损坏文件 | 返回 None |
| 5 | `matrix.shape[0] > 0` | 空 sidecar（无 embeddable 节点） | 返回 None |
| 6 | `matrix.shape[1] > 1` | 退化占位矩阵（dim=0/1） | 返回 None |

> 校验 5 和 6 防止退化 sidecar 被当可用后在 matmul 处崩溃。一个 `(0,1)` 的占位矩阵 `ndim==2` 能通过校验 4，但被校验 5（0 行）或校验 6（dim=1）拦截。

### 5.2 HybridScorer 可用性

`HybridScorer.available` 为 True 的条件：

```
matrix is not None
  AND id_to_row is not None
    AND embed_backend 已配置
```

当 `available=False` 时，`vector_scores()` 返回 None，`_score_query` 跳过向量 tier，纯词法运行。

### 5.3 加载时机

`_GraphContextCache._load_entry()`（`serve.py`）在 graph 加载时 eager warm `HybridScorer`（与 trigram 索引并行预热），挂到 `G.graph["_hybrid_scorer"]`。graph 的缓存键是 `(st_mtime_ns, st_size)`，graph.json 变更后自动重建 context（含重新加载 sidecar）。

---

## 6. 环节 ④ query 打分

### 6.1 维度守卫与自愈

`HybridScorer.vector_scores()` 在 matmul 前校验维度——这是检测 sidecar 数据有问题的主检测点：

```python
# embed query 后、cosine_similarity 前
if self._matrix.shape[0] == 0 or self._matrix.shape[1] != q_vec.shape[0]:
    # 数据有问题（sidecar 陈旧 / 模型漂移 / 损坏）
    # → 异步触发全量重建（自愈）
    _trigger_async_rebuild(self._graph_dir)
    # → 当前查询降级为纯词法
    return None
```

维度不匹配时执行两件事：
1. **异步触发重建** — `_trigger_async_rebuild()`（`embeddings.py`）detach 一个 `graphify check --no-check` 后台子进程，调用 `generate_embeddings_incremental(full=False)` 即**增量重建**。`generate_embeddings_incremental` 内部检测到模型变更/无 sidecar/损坏时自动升级为全量（见 §3.2 决策树）。进程内去重（`_TRIGGERED_REBUILDS` set）保证同一 graph_dir 只触发一次，避免连续查询引发重建风暴
2. **当前查询降级** — 返回 None，`_score_query` 跳过向量 tier，纯词法运行

**设计意图**：维度不匹配说明 sidecar 数据有问题，不应静默降级了事——应主动触发修复。当前查询降级继续，下次查询（重建完成后）就能用到新 sidecar。用户无需手动跑 `graphify .`。

### 6.2 最后一道防线：`cosine_similarity` 守卫

`cosine_similarity(query_vec, matrix)` 保留独立的维度守卫作为防御性最后防线：

```python
if matrix.shape[0] == 0 or matrix.shape[1] != query_vec.shape[0]:
    return np.zeros(matrix.shape[0], dtype=np.float32)
```

万一 `vector_scores` 的检测被绕过（理论上不会，但防御性编程），这里返回全零而非抛 ValueError。

### 6.3 query 模型选择

`vector_scores()` 使用 `self._embed_model or self._model` 作为 query embedding 的模型：
- `self._embed_model`：来自 graphifyrc 的 `embed_model`（config 覆盖）
- `self._model`：sidecar `.index.json` 记录的 build 时模型

当 config 模型与 sidecar 模型不一致时，query 用 config 模型 embed，维度可能与 sidecar 矩阵不符 → 被 §6.1 的维度守卫拦截 → 触发异步全量重建 + 降级纯词法。重建后 sidecar 用 config 模型重新生成，下次查询自愈。

---

## 7. 环节 ⑤ staleness 检测

### 7.1 检测算法

`_check_single_project()`（`cli.py`）的 staleness 判定：

```python
stale = (
    (meta_commit and graph_commit and meta_commit != graph_commit)      # ① commit 不等
    or (graph_is_newer and meta_commit == graph_commit)                 # ② graph 新但同 commit
    or (not meta_commit and not graph_commit
        and meta_node_count != graph_node_count)                        # ③ 非 git + 节点数变
    or (graph_is_newer and not meta_commit and not graph_commit)        # ④ 非 git + graph 新
)
```

| 分支 | 覆盖场景 |
|---|---|
| ① commit 不等 | 新 commit、git pull |
| ② graph 新但同 commit | `graphify update` / 失败的 embedding 刷新（同 commit 下 graph.json 被重建但 sidecar 未刷新） |
| ③ 非 git + 节点数变 | 非 git 项目节点增删 |
| ④ 非 git + graph 新 | 非 git 项目 mtime 兜底 |

### 7.2 快路径

- **无 sidecar** → 需要生成（不走 commit 比对）
- **meta mtime >= graph mtime** → fresh，直接返回（<1ms）

### 7.3 已知盲区

| 盲区 | 影响 | 缓解 |
|---|---|---|
| 非 git + 节点数不变（仅 desc 变更） | 漏检 | 分支 ④ 的 mtime 信号部分覆盖（graph 新即视为陈旧） |
| SessionStart detach 异步刷新未完成时 query | 命中陈旧 sidecar | loader 校验 + 维度守卫保证不崩溃，仅向量 tier 暂时失效 |
| `graphify query` 命令本身不调 staleness 检测 | hook 未跑时永远不检测 | 维度守卫保证不崩溃；用户可手动跑 `graphify check` |

---

## 8. 环节 ⑥ 刷新触发器

### 8.1 触发器总览

| 触发器 | 路径 | 模式 | 同步/异步 |
|---|---|---|---|
| `graphify .` / `graphify extract .` | `cli.py` extract → `build_embeddings` | 增量（或全量） | 同步 |
| `graphify update <path>` | `cli.py` update → `build_embeddings` | 增量 | 同步 |
| git post-commit hook | hook → `watch.py` `_rebuild_code` → `build_embeddings` | 增量 | 同步（hook 内） |
| `graphify <path> --watch` | `watch.py` 文件保存 → `_rebuild_code` → `build_embeddings` | 增量 | 同步 |
| SessionStart hook | `graphify check` → `_check_single_project(detach=True)` | 检测+增量刷新 | **异步 detach** |
| 检测到坏数据（维度不匹配） | `vector_scores` → `_trigger_async_rebuild` → `graphify check --no-check` | 增量（自动升级全量） | **异步 detach** |
| 每日定时任务 | `graphify check --all` → 检测 staleness，陈旧则全量重建 | 全量（仅陈旧项目） | 同步（定时触发） |

SessionStart 路径与维度不匹配自愈路径都用 detach 到后台子进程（写入 `~/.cache/graphify-embedding-refresh.log`），不阻塞会话。

### 8.2 每日定时任务：三平台注册机制

`graphify install` 自动注册一个全局定时任务（任务名 `graphify-daily`），每天在 0:00~5:59 之间的随机时刻执行 `graphify check --all`，遍历活跃项目列表做全量重建，作为增量刷新的兜底对齐。随机时间分散团队负载，避免多人同时命中 embedding API。

注册命令：`graphify schedule`（install 时自动调用），子命令 `--status` 查询、`--unregister` 移除。

三平台注册机制（`_schedule_register`，`cli.py`）：

| 平台 | 注册方式 | 命令 |
|---|---|---|
| **Windows 原生** | Windows Task Scheduler（`schtasks`） | `schtasks /create /tn graphify-daily /tr cmd /c "graphify check --all >> log 2>&1" /sc daily /st HH:MM /f` |
| **WSL** | Windows Task Scheduler via interop（`schtasks.exe`） | `schtasks.exe /create /tn graphify-daily /tr "wsl.exe -e bash -lc 'graphify check --all >> log 2>&1'" /sc daily /st HH:MM /f` |
| **POSIX（Linux/macOS）** | cron | `crontab` 写入 `MM HH * * * graphify check --all >> log 2>&1  # graphify-daily` |

**WSL 特殊处理**：WSL 的 cron 服务默认不运行，所以用 Windows Task Scheduler（`schtasks.exe` via interop）注册，任务通过 `wsl.exe -e bash -lc` 重新进入 WSL 执行 `graphify check --all`——与原生 Windows 和原生 cron 走同一个 Python 入口，只有注册机制不同。

**POSIX cron 去重**：写入 crontab 时先读现有内容，过滤掉带 `# graphify-daily` marker **或** 包含 `graphify check --all` 命令字符串的旧行（双重过滤），再追加新行，避免重复注册。`unregister` 用同样的双重过滤移除。

**unregister / status** 三平台各有对应：
- Windows/WSL：`schtasks /delete /tn graphify-daily /f` 和 `schtasks /query /tn graphify-daily`
- POSIX：`crontab` 过滤 marker 行重写

### 8.3 活跃项目列表

`graphify check`（SessionStart hook 路径）每次运行时会 `_touch_active_project(cwd)`，把当前项目目录记录到活跃项目列表。每日定时任务的 `graphify check --all` 遍历这个列表，对每个项目检查 staleness，陈旧则全量重建。这保证定时任务只刷新用户实际在用的项目，而非全盘扫描磁盘。

---

## 9. 一致性约束

sidecar 的三个文件之间，以及 sidecar 与 graph.json 之间，应满足以下约束。loader 已校验标注 ✅ 的项；其余项由 build 路径的正确性保证（当前无运行时校验）。

| 约束 | 校验位置 | 失败后果 |
|---|---|---|
| `matrix.shape[0] == len(index.node_ids)` | ❌ | id_to_row 越界或漏行 |
| `matrix.shape[1] == index.dim` | ❌ | dim 元数据失真 |
| `matrix.shape[1] == meta.dim` | ❌ | meta 元数据失真 |
| `len(index.node_ids) == meta.node_count` | ❌ | 计数失真 |
| `index.model == meta.model` | ❌ | 模型元数据失真 |
| `matrix.shape[0] > 0`（非空） | ✅ loader | 退化 sidecar 被拒 |
| `matrix.shape[1] > 1`（合法维度） | ✅ loader | 退化 sidecar 被拒 |
| `matrix.shape[1] == query_vec.shape[0]`（维度匹配） | ✅ cosine_similarity | 维度不符降级纯词法 |
| sidecar node_id 集合 ⊆ graph.json node_id 集合 | ❌ | 查到已删除节点（向量分仍算，但词法分可能异常） |

> **安全保证**：即便上述未校验的约束被违反，查询也不会崩溃——`cosine_similarity` 的维度守卫是最后一道防线，任何维度异常都降级为纯词法。未校验的约束主要影响召回质量（向量 tier 可能指向陈旧节点），不影响查询安全性。

---

## 10. 降级与自愈链路总览

查询路径在任何一层失败时，逐层降级，永不崩溃。维度不匹配时额外触发异步自愈：

```
query 字符串
  │
  ├─ HybridScorer.available == False
  │   （无 sidecar / loader 返回 None / backend 未配置）
  │   → vector_scores() 返回 None
  │   → _score_query 跳过向量 tier
  │   → 纯词法 3 层 (EXACT/PREFIX/SUBSTRING) + fuzzy
  │
  ├─ query embedding 失败（API 调用失败）
  │   → embed_query() 返回 None
  │   → vector_scores() 返回 None
  │   → 同上降级
  │
  ├─ 维度不匹配（sidecar dim != query dim）★ 自愈路径
  │   → vector_scores() 检测到 shape 不符
  │   → _trigger_async_rebuild() detach 后台全量重建（进程内去重）
  │   → 当前查询返回 None → 纯词法降级
  │   → 后台重建完成后，下次查询自动用到新 sidecar（自愈）
  │   → 用户无需手动干预
  │
  └─ 一切正常
      → 向量 tier 贡献 confidence-gated 分层 bonus
      → 词法 + 向量 + fuzzy 加法叠加
```

**自愈触发器**：`_trigger_async_rebuild()`（`embeddings.py`）detach `graphify check --no-check` 后台子进程，调用 `generate_embeddings_incremental(full=False)` 即增量重建——检测到模型变更/无 sidecar/损坏时自动升级为全量（见 §3.2 决策树）。进程内 `_TRIGGERED_REBUILDS` set 去重——同一 graph_dir 只触发一次，连续查询不会引发重建风暴。

---

## 11. 非目标

- 不改动向量打分公式与分层权重（见 `docs/retrieval-overall-design/vector-tier-redesign-spec.md`）
- 不改动检索双循环架构（见 `docs/retrieval-overall-design/spec.md`）
- 不引入向量数据库（faiss/LanceDB）—— numpy brute-force 在 graphify 规模下足够
- 不改动 embedding 后端配置机制（见 `docs/hybrid-semantic-search/Embedding.md`）
- 不改动 `_node_embed_text` 的文本源策略（desc → rationale → 跳过）
- 不改动固定文件名 `embedding.*`（原子写入与版本管理是未来改进项，非当前机制一部分）

---

## 12. 参考代码位置

| 符号 | 位置 | 环节 |
|---|---|---|
| `build_embeddings` | `graphify/embeddings.py` | ① build |
| `generate_embeddings_for_graph` | `graphify/embeddings.py` | ① 全量 |
| `generate_embeddings_incremental` | `graphify/embeddings.py` | ① 增量 |
| `_node_embed_text` | `graphify/embeddings.py` | ① 文本源 |
| `_sidecar_paths` | `graphify/embeddings.py` | ② 文件名 |
| `_write_sidecar_meta` | `graphify/embeddings.py` | ② meta |
| `load_embedding_sidecar` | `graphify/embeddings.py` | ③ 加载 |
| `cosine_similarity` | `graphify/embeddings.py` | ④ 打分（最后防线维度守卫） |
| `_trigger_async_rebuild` | `graphify/embeddings.py` | ④ 自愈（detach 后台重建） |
| `embed_query` | `graphify/embeddings.py` | ④ query embedding |
| `HybridScorer._load` / `available` / `vector_scores` | `graphify/hybrid_scorer.py` | ③④ |
| `_check_single_project` | `graphify/cli.py` | ⑤ staleness |
| `_do_embedding_refresh` / `_launch_embedding_refresh` | `graphify/cli.py` | ⑥ 刷新 |
| `graphify check` / `graphify check --all` | `graphify/cli.py` | ⑥ 触发 |
| `_schedule_register` / `_schedule_unregister` / `_schedule_status` | `graphify/cli.py` | ⑥ 定时任务（Windows/WSL/POSIX） |
| `_rebuild_code` → `build_embeddings` | `graphify/watch.py` | ⑥ post-commit |
