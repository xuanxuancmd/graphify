# Plan: 提交阶段图谱更新能力补齐

> 关联:`spec.md` §8(提交阶段整体方案)。本文梳理**提交阶段(hook 自动)与目标态的差异**,每步是可独立执行、可验证的原子改动。
>
> 执行顺序:C-Gap-2 → C-Gap-3。两者独立,C-Gap-2 是纯文档化(零代码改动),C-Gap-3 需改 `_rebuild_code` 核心逻辑。

---

## 差异点汇总

| C-Gap | 描述 | 影响 | 优先级 | 需编码? | 状态 |
|---|---|---|---|---|---|
| C-Gap-2 | markdown 跑过 Tier2 LLM 后被 hook 跳过(semantic_doc_set 排除) | 改了已跑 LLM 的 .md,hook 不更新 Tier1 节点 | 中 | 否(文档化现状) | ✅ 已文档化(spec.md §8.4) |
| C-Gap-3 | ddd / 外部解析器需 code_index,hook 不传 | commit 改了 ddd 文档,hook 不更新 ddd 节点 | 高 | 是(改 _rebuild_code) | ✅ 已实现 |

**按需扩展(非 Gap)**:普通 yaml/yml 的 Tier1 提取器是按需的——框架已支持通过 `_DISPATCH` 注册任意扩展名的提取器,用户按需编写即可,不内置具体实现。详见 `spec.md` §8.6。

**不在范围内**(明确不做的):

| 不做项 | 理由 |
|---|---|
| 文件内增量(diff 级) | 配置文件 KB 级全量解析 < 10ms,获取/传递 diff 成本可能超过解析本身;md 逐行正则 500 行 < 50ms;瓶颈在 Tier2 LLM 非 Tier1 解析 |
| 处理器增量接口(extract_incremental) | content hash 缓存已避免无效解析;处理器层全量解析是合理设计选择 |
| Tier2 LLM 自动触发 | hook 保持快速(纯本地),Tier2 语义提取留给手动触发 |

---

## C-Gap-2: markdown 跑过 Tier2 LLM 后被 hook 跳过

### 现状

`graphify/watch.py:1246-1294`: 如果 .md 文件已跑过 Tier2 LLM(有语义节点),被加入 `semantic_doc_files`,从 `extract_targets` 排除。

```python
# watch.py:1308-1324
semantic_doc_set = {Path(os.path.abspath(p)) for p in semantic_doc_files}
wanted: list[Path] = []
for raw in changed_paths:
    ...
    tracked = next((cand for cand in candidates if cand.exists() and cand in code_set), None)
    if tracked is not None:
        if tracked not in wanted and tracked not in semantic_doc_set:  # ← 排除
            wanted.append(tracked)
        continue
```

**原因**(`watch.py:1232`):避免 AST heading 节点与 LLM 语义节点重复,导致 4 倍图膨胀。

**影响**:一旦 .md 跑过 `graphify extract`(Tier2),后续 commit 改了该 .md,hook 不会自动更新 Tier1 节点(page/heading)。需手动 `graphify extract --update`。

### 目标

两个可选方案:

| 方案 | 描述 | 优缺点 |
|---|---|---|
| A: 接受现状 | hook 不处理有语义层的 .md,明确文档化 | 简单,但改了 md 的 heading 结构后 hook 不更新 |
| B: 按 node_kind 区分共存 | Tier1 heading 节点和 Tier2 语义节点按 node_kind 区分,允许共存 | 更精确,但需改 reconcile 逻辑避免重复 |

**推荐方案 A**:接受现状,在文档中明确说明。理由:
- 改了 md heading 结构是低频操作,手动 `graphify extract --update` 可接受
- 方案 B 的 reconcile 改动复杂,ROI 低
- heading 节点与语义节点的"4 倍膨胀"是真实问题,不轻易打破

### 改动(方案 A:文档化)

**文件**: `docs/extending-extractors/spec.md` §8.4(已写入)

**文件**: `graphify/watch.py` — 在 `semantic_doc_files` 排除处加注释

```python
# watch.py:1308
# 已跑过 Tier2 LLM 的 .md 不再 Tier1 快扫 (#1915):
# 避免 heading 节点与语义节点重复导致 4 倍图膨胀。
# 改了这类 .md 的 heading 结构后,需手动 `graphify extract --update` 刷新。
semantic_doc_set = {Path(os.path.abspath(p)) for p in semantic_doc_files}
```

### 验证(方案 A)

```bash
# 1. 首次全量提取(含 Tier2)
uv run graphify extract tests/fixtures/docs/sample.md --backend <backend>

# 2. 修改 sample.md 的 heading
sed -i 's/# Title/# New Title/' tests/fixtures/docs/sample.md

# 3. 模拟 hook
uv run python -c "
from graphify.watch import _rebuild_code
from pathlib import Path
_rebuild_code(Path('.'), changed_paths=[Path('tests/fixtures/docs/sample.md')])
"
# 预期: sample.md 被 semantic_doc_set 排除, Tier1 heading 不更新

# 4. 手动更新
uv run graphify extract . --update
# 预期: sample.md 的 Tier1 heading 更新
```

---

## C-Gap-3: ddd / 外部解析器需 code_index,hook 不传

### 现状

`graphify/watch.py:1454-1462`:

```python
result = extract(
    extract_targets,
    cache_root=watch_root,
    resolution_context_nodes=resolution_context_nodes or None,
    resolution_context_edges=resolution_context_edges or None,
) if extract_targets else {...}
```

**不传 `code_index`**。而 `try_external_extractors` 只在 `code_index is not None` 时被调用(`extract.py:5825`):

```python
if code_index is not None:
    from graphify.extractors.registry import try_external_extractors
    ...
```

ddd 需要 code_index 做 code-anchor 匹配(`ddd.py:847` `_build_code_indices`)。

**影响**:commit 改了 ddd 文档,hook 不更新 ddd 节点。需手动 `graphify extract --update`。

### 目标

让 ddd 等外部解析器在 commit 阶段能跑(传入 code_index)。

### 改动

#### 步骤 1:在 _rebuild_code 中先跑代码 AST,再跑文档

**文件**: `graphify/watch.py`

**位置**: `_rebuild_code` 函数(`watch.py:1086-1672`),`extract_targets` 确定后、调 `extract()` 前。

**当前流程**:
```
extract_targets = [代码文件 + 有提取器的文档文件]
result = extract(extract_targets)  ← 不传 code_index
```

**改动后流程**:
```
# 分离代码文件和文档文件
code_targets = [p for p in extract_targets if p.suffix.lower() in _CODE_EXTENSIONS]
doc_targets = [p for p in extract_targets if p.suffix.lower() not in _CODE_EXTENSIONS]

# 先跑代码 AST
code_result = extract(code_targets, cache_root=watch_root, ...) if code_targets else {empty}

# 再跑文档, 传 code_index
doc_result = extract(doc_targets, cache_root=watch_root, code_index={"nodes": code_result["nodes"]}, ...) if doc_targets else {empty}

# 合并
result = {
    "nodes": code_result["nodes"] + doc_result["nodes"],
    "edges": code_result["edges"] + doc_result["edges"],
    ...
}
```

**伪代码**:

```python
# watch.py — _rebuild_code 内, 替换 extract(extract_targets, ...) 调用

commit = _git_head(cwd=watch_root)

# 分离代码和文档
_CODE_EXTS = set(_CODE_EXTENSIONS)  # detect.py 的 CODE_EXTENSIONS
code_targets = [p for p in extract_targets if p.suffix.lower() in _CODE_EXTS]
doc_targets = [p for p in extract_targets if p.suffix.lower() not in _CODE_EXTS]

# 阶段 1: 代码 AST
if code_targets:
    code_result = extract(
        code_targets,
        cache_root=watch_root,
        resolution_context_nodes=resolution_context_nodes or None,
        resolution_context_edges=resolution_context_edges or None,
    )
else:
    code_result = {"nodes": [], "edges": [], "hyperedges": [],
                   "input_tokens": 0, "output_tokens": 0}

# 阶段 2: 文档(含外部解析器), 传 code_index
if doc_targets:
    doc_result = extract(
        doc_targets,
        cache_root=watch_root,
        code_index={"nodes": code_result["nodes"]},
        # 文档不需要 resolution_context (那是代码符号解析用的)
    )
else:
    doc_result = {"nodes": [], "edges": [], "hyperedges": [],
                  "input_tokens": 0, "output_tokens": 0}

# 合并
result = {
    "nodes": list(code_result.get("nodes", [])) + list(doc_result.get("nodes", [])),
    "edges": list(code_result.get("edges", [])) + list(doc_result.get("edges", [])),
    "hyperedges": list(doc_result.get("hyperedges", [])),
    "input_tokens": code_result.get("input_tokens", 0) + doc_result.get("input_tokens", 0),
    "output_tokens": code_result.get("output_tokens", 0) + doc_result.get("output_tokens", 0),
    "failed_sources": list(code_result.get("failed_sources") or []) + list(doc_result.get("failed_sources") or []),
    "suppress_llm_files": doc_result.get("suppress_llm_files", set()),
}
```

#### 步骤 2:处理 ddd 的跨文件 pending_edges

ddd 的 `pending_edges`(`ddd.py:884`)需要全局节点索引做二次解析(`ddd.py:776` `_resolve_pending_edges`)。当前 `extract()` 内部已处理(`extract.py:5858-5862`),但如果 ddd 文件引用了**未变文件**的 concept_id,需要未变文件的节点参与解析。

**当前机制**(`watch.py:1390-1451`):`resolution_context_nodes` 传了未变代码文件的 AST 节点,但**不传未变文档文件的节点**。

**改动**:在 `resolution_context` 中也加载未变 ddd 文件的 doc-anchor 节点:

```python
# watch.py — resolution_context 构建处, 补充文档节点
if changed_paths is not None and existing_graph.exists():
    ...
    for node in ctx_graph.get("nodes", []):
        if not node.get("id"):
            continue
        # 现有: 只加载 AST-tier 代码节点
        if not _is_ast_tier(node):
            continue
        # 新增: 也加载 doc-anchor 节点(ddd 等外部解析器产出)
        if node.get("node_kind") == "doc-anchor":
            source_file = node.get("source_file")
            if not source_file or ctx_paths.identity(source_file) not in ctx_live:
                continue
            resolution_context_nodes.append({
                "id": node["id"],
                "label": node.get("label"),
                "source_file": source_file,
                "file_type": node.get("file_type"),
                "concept_id": node.get("concept_id"),  # ddd 跨文件解析需要
                "tags": node.get("tags"),
            })
            continue
        # 原有代码节点逻辑...
```

#### 步骤 3:ddd 解析器的降级处理

如果 hook 阶段 code_index 为空(如只改了 ddd 文件,没改代码),ddd 解析器的 code-anchor 匹配会全部 miss。ddd 应能优雅降级:

**文件**: `graphify/extractors/ddd.py`

**现状**: `extract_ddd` 已处理空 code_index(`ddd.py:843-847`):

```python
code_nodes = []
if code_index:
    raw = code_index.get("nodes", []) if isinstance(code_index, dict) else []
    if isinstance(raw, list):
        code_nodes = [n for n in raw if isinstance(n, dict)]
indices = _build_code_indices(code_nodes)  # 空列表 → 空 indices
```

空 indices 时,`_match_code_anchor` 返回 None,锚点进入 `unmatched`(`ddd.py:488-494`)。**已优雅降级,无需改动**。

### 验证

```bash
# 1. 首次全量提取(建立 code_index)
uv run graphify extract . --backend <backend>

# 2. 修改 ddd 文档(不改代码)
echo "| 聚合根<anchor:ddd> | 描述<anchor:desc> | 代码锚点<anchor:code> |\n| --- | --- | --- |\n| OrderAG | 订单聚合根 | OrderService.create |" >> docs/ddd/domain-model.md

# 3. 模拟 hook
uv run python -c "
from graphify.watch import _rebuild_code
from pathlib import Path
_rebuild_code(Path('.'), changed_paths=[Path('docs/ddd/domain-model.md')])
"
# 预期: ddd 文档被处理, doc-anchor 节点更新, code-anchor 匹配到 OrderService.create

# 4. 验证 graph.json 含新 ddd 节点
uv run graphify query "OrderAG"
# 应命中 doc-anchor 节点, tags 含 ["ddd","aggregate_root","domain-model"]
```

---

## 执行顺序与依赖

```
C-Gap-2 (md 语义层排除)  ← 文档化, 无代码改动
    │
    │  (独立)
    │
C-Gap-3 (hook 传 code_index)  ← 需改 _rebuild_code 核心逻辑
```

**建议顺序**:
1. 先做 C-Gap-2(纯文档化,零风险)
2. 再做 C-Gap-3(改 `_rebuild_code` 核心逻辑,需充分测试)

---

## 不在范围内的设计决策

以下明确**不做**,记录理由:

| 不做项 | 理由 |
|---|---|
| 文件内增量(diff 级解析) | 配置文件 KB 级全量解析 < 10ms;md 逐行正则 500 行 < 50ms;content hash 缓存已避免无效解析;获取/传递 diff 成本可能超过解析本身 |
| `extract_incremental` 接口 | 处理器层全量解析是合理设计;增加增量接口会提高解析器开发门槛,ROI 低 |
| Tier2 LLM 在 hook 自动触发 | hook 保持纯本地、秒级完成;Tier2 需 API key 且慢,留给手动触发 |
| markdown heading 与语义节点共存 | 方案 B 的 reconcile 改动复杂,4 倍膨胀是真实问题,ROI 低;接受 hook 不更新有语义层的 md |
| 内置 yaml 提取器 | 按需扩展:框架已支持通过 `_DISPATCH` 注册任意扩展名提取器,用户按需编写即可,不内置具体实现 |
