# Spec: DDD 文档自定义解析器 + 解析器优先级机制

## 1. 背景与问题

graphify 当前对 `.md` 文档采用双轨提取：

- **Tier 1（AST/正则）**：`graphify/extractors/markdown.py` 逐行 regex，仅产出 file 节点（`node_kind: "page"`）+ heading 节点 + `contains`/`references` 边。`references` 仅解析 `[text](./other.md)` 和 `[[wikilink]]`，**只做 doc↔doc**（`markdown.py:219` 拒绝非 doc 扩展名）。
- **Tier 2（LLM 语义）**：`graphify/llm.py:475-505` 的 `_EXTRACTION_SYSTEM` prompt + `extraction-spec.md`，提取 `document`/`concept`/`rationale` 节点 + `references`/`cites`/`conceptually_related_to` 等边。但 LLM 对代码节点盲视（`cli.py:3382` `semantic_files = doc_files + paper_files + image_files`），且 `_out_of_scope`（`llm.py:2741`）丢弃跨文件归属的节点。

**问题**：DDD 文档有结构化的术语表（限界上下文 / 聚合根 / 领域事件 / 不变式 / 业务流程等），当前 markdown 提取器不识别这些 DDD 概念，把它们当普通 heading 处理；LLM 提取虽能抓"named concepts"但不区分 DDD 类型，且 `file_type` 是封闭 6 值枚举（`build.py:856`），DDD 术语全部塌缩为 `concept`。

**目标**：增加一个 DDD 专用文档解析器，从 DDD 文档白名单中提取结构化 DDD 概念节点 + 代码锚点关联边，并且让 graphify 优先调用外部扩展解析器、不可解析时回退到默认 markdown 提取器。同时支持配置"外部解析器处理后是否仍让通用 graphify 文档解析器再处理一遍"。

## 2. 设计目标

| 目标 | 描述 |
|---|---|
| **G1 解析器优先级机制** | graphify 处理 `.md` 时，优先尝试外部扩展解析器；外部解析器返回"不可处理"时，回退到默认 `extract_markdown` |
| **G2 DDD 解析器** | 针对符合白名单的 DDD 文档（5 类 + 2 个特殊文件），提取 DDD 概念节点 + `describes`（doc→code）/ `related`/ `categorized_under`/ `cites` 边 |
| **G3 代码 AST 优先** | 文档解析前，先完成代码 AST 提取，DDD 解析器的代码锚点匹配能引用已抽取的 code 节点索引 |
| **G4 可配置合并策略** | 外部解析器可声明三种合并模式（`merge`/`replace`/`supplement_only`），控制外部处理后是否仍跑默认 markdown + LLM Tier 2 |
| **G5 通用节点建模 + tags 检索** | DDD 节点字段全部通用（无 `ddd_*` 前缀字段）；DDD 类型信息编码进通用 `tags` 列表字段；`tags` 参与 graphify 字符串检索 |
| **G6 与 upstream 解耦** | 核心改动以独立模块形式注入，不动 `_DISPATCH` 的既有条目，不修改 `markdown.py` / `build.py` / `dedup.py` / `llm.py`；仅对 `serve.py` 做一处 `tags` 拼接的加法改动 |

## 3. DDD 文档白名单

参考 `C:\wanglong\Understand-Anything\understand-anything-plugin\skills\understand-ddd\parse-ddd-tables.mjs` 的实现。

### 3.1 白名单文件名（按文件名匹配，不依赖路径）

| 文件名 | 解析器 | 产出 |
|---|---|---|
| `context-map.md` | `parseContextMap` | BC 节点（限界上下文表）+ `related` 边（业务关系表）+ glossary 节点（统一语言表） |
| `technical-constraints.md` | `parseTechnicalConstraints` | TC 约束节点（`### TC-xxx:` 标题）+ `describes` 边（`**代码锚点**:` 前缀）+ `categorized_under` 边（`**适用范围**:` 前缀） |
| 以下 5 类文件名之一 | `parseTaggedFile`（标签表解析器） | doc-anchor 节点 + `describes`/`related`/`categorized_under`/`cites` 边 |

### 3.2 标签表 5 类白名单

匹配文件名（不区分大小写，含路径片段即触发）：

| 关键词 | DDD 类型 |
|---|---|
| `business-flow` | 业务流程 |
| `invariants` | 业务不变式 |
| `contracts` | 业务契约 |
| `domain-events` | 领域事件 |
| `domain-model` | 领域模型 / 聚合协作 |

> 匹配规则：文件名（含相对路径片段）包含上述任一关键词，且表格头含 `<anchor:ddd>` 标签列。

### 3.3 标签表三列约定

白名单产物的表格必须含三列标签（要么三列全有，要么三列全无）：

| 标签 | 列名约定 | 内容 |
|---|---|---|
| `<anchor:ddd>` | 列名即 DDD 概念类型（如"聚合根"/"领域事件"/"不变式"），**业务术语**，非代码类名 | 该概念的 ID 或名称 |
| `<anchor:code>` | "代码锚点" | 代码锚点字符串，**仅支持三类格式**：`类名` / `类名.函数名` / `POST:/path` |
| `<anchor:desc>` | "说明" | 该概念的描述文字 |

### 3.4 边类型与权重

| 边类型 | 方向 | 来源 | 权重 |
|---|---|---|---|
| `describes` | doc-anchor → code node（双向） | `<anchor:code>` 列匹配到 code 节点 | 0.8 |
| `related` | doc-anchor ↔ doc-anchor（双向） | 从/到列 或 源聚合/目标聚合 | 0.5 |
| `categorized_under` | doc-anchor → doc-anchor（前向） | 归属聚合/操作的聚合 | 0.6 |
| `cites` | doc-anchor → doc-anchor（前向） | 对端 BC | 0.7 |

## 4. 节点与边的 graphify 适配

### 4.1 节点 shape（全通用字段 + tags 编码 DDD 类型）

graphify 的 `file_type` 是封闭 6 值枚举（`build.py:856`），不引入新值。DDD 节点统一映射，**所有字段通用，无 `ddd_*` 前缀字段**：

```json
{
  "id": "docanchor_docs_order_domain-model_AG-01",
  "label": "订单服务",
  "file_type": "concept",
  "source_file": "docs/features/order/domain-model.md",
  "source_location": "L42",
  "node_kind": "doc-anchor",
  "desc": "处理下单",
  "concept_id": "AG-01",
  "tags": ["ddd", "aggregate_root", "domain-model"]
}
```

**字段说明**：

| 字段 | 通用 | 值/含义 |
|---|---|---|
| `id` | ✅ | `docanchor_{stem}_{concept_id}`，下划线连接，符合 graphify `[a-z0-9_]` id 规范（`llm.py:493`） |
| `label` | ✅ | 业务术语（如"订单服务"），查询主匹配字段 |
| `file_type` | ✅ | 固定 `"concept"`（不破坏 closed enum，与 LLM concept 节点同类） |
| `source_file` | ✅ | 文档相对路径 |
| `source_location` | ✅ | `L42` 行号 |
| `node_kind` | ✅ | `"doc-anchor"`（复用 markdown.py 既有 `node_kind` escape hatch 模式，与 `page`/`heading` 并列；任何外部解析器的结构化锚点节点都可用此值） |
| `desc` | ✅ | `<anchor:desc>` 列内容（概念描述） |
| `concept_id` | ✅ | 原始概念 ID（如 `AG-01`、`BC-01`），保留原值不做 normalize，用于全局边解析（§4.4） |
| `tags` | ✅ | **通用分类标签列表**。DDD 解析器填充 `["ddd", "<ddd_type>", "<doc_category>"]`；其他外部解析器可填充自己的 tag。参与 graphify 字符串检索（§4.5） |

**DDD 类型编码进 tags**：
- `<anchor:ddd>` 列名（如"聚合根"）→ 推断成机器可读值（`aggregate_root`）→ `tags[1]`
- 文档类别（来自文件名关键词，如 `domain-model`）→ `tags[2]`
- `ddd` 标记 → `tags[0]`
- 不再使用 `ddd_type` / `ddd_doc_category` 独立字段——合并进通用 `tags`

### 4.2 边 shape（适配 graphify edge schema）

graphify edge schema 要求 `relation` 来自封闭集合（`llm.py:504`）。DDD 4 种边的映射：

| DDD 边 | graphify `relation` | 说明 |
|---|---|---|
| `describes` | `references` | doc→code 关联，复用 graphify 既有 `references` 边类型（`markdown.py:349` 已用） |
| `related` | `conceptually_related_to` | doc↔doc 概念关联，复用 LLM 既有边类型（`llm.py:504`） |
| `categorized_under` | `conceptually_related_to` | doc→doc 归属，复用 |
| `cites` | `cites` | doc→doc 引用，复用 LLM 既有 `cites`（`extraction-spec.md:64`） |

边完整 shape：
```json
{
  "source": "docanchor_docs_order_domain-model_AG-01",
  "target": "src_order_order_service:OrderService",
  "relation": "references",
  "confidence": "EXTRACTED",
  "confidence_score": 1.0,
  "source_file": "docs/features/order/domain-model.md",
  "source_location": "L15",
  "weight": 0.8
}
```

### 4.3 代码锚点匹配（依赖 G3：AST 优先）

DDD 文档的 `<anchor:code>` 列填代码锚点字符串（`类名` / `类名.函数名` / `POST:/path`）。匹配逻辑参考 `ddd-code-matcher.mjs`：

| 锚点格式 | 匹配优先级 | 匹配方式 |
|---|---|---|
| 文件名.扩展名（如 `register_plugin.rs`） | 0 | fileIndex 查 basename，优先 `file` 类型 |
| snake_case `file.method`（如 `mirror_source_task.poll`） | 1 | fileIndex 查 file hint，再在该 file 节点找 `function` 类型 + name 匹配 |
| PascalCase.method（如 `MirrorMaker.start`） | 2 | nameIndex 查 class，再在同 filePath 找 function + name |
| PascalCase（如 `MirrorSourceTask`） | 3 | nameIndex 查 class，优先 `class` 类型 |
| `METHOD /path`（如 `POST /connectors`） | 4 | endpointIndex 查 path |
| `METHOD:/path`（如 `POST:/connectors`） | 5 | endpointIndex 查 path |
| 裸路径（如 `/connectors`） | 6 | endpointIndex 查 path |

**索引构建**：从已抽取的 AST 节点构建三个索引：
- `fileIndex`：basename（无扩展名）→ GraphNode[]
- `nameIndex`：node label → GraphNode[]
- `endpointIndex`：endpoint 节点 path → GraphNode

**匹配失败处理**：记录到 `unmatched` 列表，不阻塞解析，输出到 `.graph/ddd-unmatched.json` 供人工排查。

### 4.4 全局边解析（concept_id 索引）

`related`/`categorized_under`/`cites` 边的 source/target 在解析时不一定已知（引用其他行的 concept_id 或 name），需两阶段解析：

- **Phase 1（per-file）**：各文件收集 nodes + pending edges，pending edges 记录 `sourceRef`/`targetRef`（原始 concept_id 或 name 字符串）
- **Phase 2（global）**：跨所有文件构建 `{concept_id → node}` + `{name → node}` 全局索引
- **Phase 3（resolve）**：用全局索引解析 pending edges 的 `sourceRef`/`targetRef` 到具体 node id

**索引 key**：直接用节点的 `concept_id` 字段（原始值，如 `"AG-01"`）和 `label` 字段（业务术语），**不做 normalize**——与 pending edge 里的 ref 原值一致匹配。参考 `parse-ddd-tables.mjs:579-665` 的 `buildGlobalNodeIndex` + `resolveRef` 逻辑（.mjs 用 colon 分隔 id，Python 版用独立 `concept_id` 字段避免 id normalize 问题）。

### 4.5 tags 参与字符串检索（G5）

graphify 的查询打分器 `_score_query`（`serve.py:462-629`）对每个节点的 `_node_search_text`（`serve.py:322-356`）做 3 层词法匹配。当前 `_node_search_text` 拼接 `norm_label + label_tokens + nid + source_file + source_tokens`。

**修改**：在 `_node_search_text` 里追加拼接 `tags`（join 成空格分隔字符串），让 `tags` 里的值（如 `aggregate_root`、`domain-model`）参与 substring/prefix/exact 匹配。

**效果**：
- `graphify query "aggregate_root"` → substring 命中所有 tags 含 `aggregate_root` 的 doc-anchor 节点
- `graphify query "domain-model"` → 命中 domain-model 文档类别的节点
- `graphify query "ddd"` → 命中所有 DDD 节点（tags 含 `ddd` 标记）

**改动范围**：`serve.py:322-356` 的 `_node_search_text` 函数加一行拼接 `tags`。这是加法改动，不修改既有 3 层匹配逻辑。

## 5. 解析器优先级机制（G1）+ 可配置合并策略（G4）

### 5.1 注册表设计

新建 `graphify/extractors/registry.py`（独立模块，不修改 `extract.py` 的 `_DISPATCH`）：

```python
# graphify/extractors/registry.py
"""External extractor registry — opt-in extension point for .md doc parsing.

External extractors registered here are tried BEFORE the default extract_markdown.
An extractor returns None to signal "not my file, fall back to default".
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Protocol


class DocExtractor(Protocol):
    def __call__(self, path: Path, *, root: Path, code_index: dict | None = None) -> "ExtractionResult | None":
        """Return ExtractionResult or None to fall back to default."""
        ...


@dataclass
class ExtractionResult:
    """声明式返回：外部解析器产出的节点/边 + 合并策略。"""
    nodes: list[dict]
    edges: list[dict]
    hyperedges: list[dict] = field(default_factory=list)

    # G4 合并策略
    merge_mode: str = "merge"  # "merge" | "replace" | "supplement_only"
    #   merge:          外部 + 默认 extract_markdown 合并（保留 page/heading 节点）
    #   replace:        外部替代默认 markdown（跳过 extract_markdown），但 LLM Tier 2 仍跑
    #   supplement_only: 只用外部结果，跳过默认 markdown + 跳过 LLM Tier 2
    suppress_llm: bool = False  # True = 不对该文件跑 LLM Tier 2（对 replace/supplement_only 生效）

    # 附加元数据
    unmatched: list[dict] = field(default_factory=list)


_REGISTRY: list[Callable] = []

def register_doc_extractor(fn: Callable) -> Callable:
    """Decorator to register an external doc extractor."""
    if fn not in _REGISTRY:
        _REGISTRY.append(fn)
    return fn

def try_external_extractors(
    path: Path, *, root: Path, code_index: dict | None = None
) -> ExtractionResult | None:
    """Try registered extractors in order; return first non-None result, or None."""
    for fn in _REGISTRY:
        result = fn(path, root=root, code_index=code_index)
        if result is not None:
            return result
    return None
```

### 5.2 三种合并模式详解

graphify 对 `.md` 文档有三个解析层：

| 层 | 产出 | 触发条件 |
|---|---|---|
| **外部解析器**（如 DDD） | doc-anchor 节点 + describes/related 边 | 白名单匹配 |
| **默认 markdown 解析器**（Tier 1） | page/heading 节点 + contains/references 边 | 默认对每个 .md 跑 |
| **LLM 语义提取**（Tier 2） | concept/rationale/document 节点 + semantic 边 | `cli.py:3382` 把 doc 文件加入 `semantic_files` |

#### `merge` 模式（DDD 推荐默认）

外部 + 默认 markdown **都跑**，结果合并。三层都产出，互补：

```
产出节点:
  - doc-anchor "订单服务" (外部脚本)      ← DDD 结构化锚点
  - page "domain-model" (markdown)         ← 文件层级
  - heading "聚合根" (markdown)            ← 章节结构
  - concept "订单聚合根" (LLM Tier 2)     ← 语义概念
  - rationale "采用 Saga 模式" (LLM Tier 2) ← 设计理由
```

**适用**：DDD 文档（doc-anchor 结构化 + page/heading 层级 + LLM 语义补充都有价值）。

#### `replace` 模式

外部跑，**跳过默认 markdown**，但 LLM Tier 2 仍跑（除非 `suppress_llm=True`）：

```
产出节点:
  - doc-anchor "订单服务" (外部脚本)
  - concept "订单聚合根" (LLM Tier 2)

跳过:
  - page / heading 节点 (不跑 markdown 解析器)
```

**适用**：某文档类型不需要 page/heading 章节层级，但要 LLM 语义补充。

#### `supplement_only` 模式

**只跑外部解析器**，跳过默认 markdown + 跳过 LLM Tier 2：

```
产出节点:
  - doc-anchor "订单服务" (外部脚本)

跳过:
  - page / heading (不跑 markdown)
  - concept / rationale (不跑 LLM Tier 2)
```

**适用**：外部解析器完全自包含，不需要 graphify 任何原生解析能力。如：已结构化的 YAML/JSON 配置文件解析器，不需要 markdown heading 也不需要 LLM 语义提取。

### 5.3 注入点（不修改 `_DISPATCH`）

graphify 的 `extract()` 函数用 `per_file` 槽位 + `_extract_single_file`（subprocess）或 `_extract_sequential`（主进程）分发。subprocess worker 的 args 不含 `code_index`，且节点列表 pickle 开销大。

**注入方案：doc 阶段在主进程跑**（规避 subprocess pickle）：

- `extract()` 在并行/subprocess 分发前，**先在主进程**对每个 `.md` 文件调 `try_external_extractors(path, root=root, code_index=code_index)`
- 返回 `ExtractionResult` 的文件：按 `merge_mode` 处理（merge 时合并默认 markdown），产出 `(nodes, edges, suppress_llm: bool)` 填入对应 `per_file` 槽位
- 返回 `None` 的文件：归入 `per_file` 走原有 dispatch（subprocess 或 sequential 跑 `extract_markdown`）
- `extract()` 返回值新增 `suppress_llm_files: set[str]`，cli.py 构造 `semantic_files` 时排除

**`code_index` 传递**：`extract()` 签名加 `code_index: dict | None = None` 可选参数。cli.py 两阶段调用——先 `extract(code_files)` 产出 code 节点，再 `extract(doc_files, code_index={"nodes": code_result["nodes"]})`。

具体注入方式见 plan.md 的 §3.2。

## 6. LLM Tier 2 与去重

### 6.1 LLM Tier 2 是什么

graphify 把 `.md`/`.pdf`/`.png` 等非代码文件发给 LLM（`cli.py:3382` 的 `semantic_files`），用 `_EXTRACTION_SYSTEM` prompt（`llm.py:475-505`）提取**文档散文里的语义概念和关系**——这是 Tier 1 正则解析器抓不到的：

| LLM 提取的节点类型 | 例子 |
|---|---|
| `concept` | "订单聚合根"、"支付流程"——文档里提到的概念 |
| `rationale` | "采用 Saga 模式因为最终一致性可接受"——设计理由 |
| `document` | 文档本身的元节点 |

| LLM 提取的边类型 | 例子 |
|---|---|
| `references` | 文档 A 引用文档 B |
| `cites` | 文档引用 ADR/RFC |
| `conceptually_related_to` | 两个概念相关 |
| `semantically_similar_to` | 两个概念解决相同问题 |

### 6.2 当前 LLM Tier 2 对 DDD 的局限

graphify 默认的 `_EXTRACTION_SYSTEM` prompt 是**通用的**（"extract named concepts, entities, citations"），**不知道 DDD 术语体系**。对 DDD 文档跑 Tier 2 会：

- ✅ 抓到一些概念（"订单聚合根"、"Saga 模式"）
- ❌ 不知道这些是 DDD 的哪个类型（Aggregate Root？Domain Event？不变式？）
- ❌ 不会主动按 DDD 术语体系分类提取
- ❌ 全部塌缩为 `file_type="concept"`，丢失 DDD 类型语义

### 6.3 去重：复用 graphify 原生机制

**不引入自定义去重逻辑**。脚本产出的 doc-anchor 节点（`file_type="concept"`）和 LLM 产出的 concept 节点（`file_type="concept"`）走 graphify 原生三层去重：

| 层 | 机制 | 对 DDD 的效果 |
|---|---|---|
| **ghost-merge**（`build.py:979-1069`） | 按 `(source_file, label)` 去重，AST 节点优先 | 脚本与 LLM 节点同 key 时，先到先得——**多数情况下 label 不同**（脚本用业务术语，LLM 用原文 token），不冲突 |
| **`deduplicate_entities`**（`dedup.py:503`） | 精确 + 模糊合并 | `concept` 类型可跨文件合并，合理 |
| **`_doc_twin_remap`**（`build.py:766`） | markdown + LLM 的 `_doc` 节点合并 | 只碰 `file_type="document"`，不影响 DDD `concept` 节点 |

**预期行为**：
- 大多数 DDD 概念：脚本的 doc-anchor label（业务术语，如"订单服务"）与 LLM 的 concept label（原文 token，如"OrderService"）**不同** → 两者独立存在，graph 同时保留结构化锚点 + 语义概念，互补
- 偶尔相同 label：graphify ghost-merge 先到先得，可能丢失一方的专属字段——**接受此权衡**，因为 graph 结构（doc-anchor 节点 + describes 边 + tags）保留主要价值

## 7. 代码 AST 优先（G3）

### 7.1 当前流程的问题

当前 `extract()` 对一个目录里所有文件并行 AST 提取（`ProcessPoolExecutor`），doc 文件也走 AST markdown 提取（Tier 1）+ 后续 LLM 语义提取（Tier 2）。DDD 解析器需要 code 节点索引来做锚点匹配，但若 doc 和 code 在同一批并行提取，doc 解析时 code 节点尚未全部产出。

### 7.2 调整：两阶段提取

```
阶段 1: 提取所有 code 文件（.py/.ts/.go/...）AST → 产出 code 节点 + 边
阶段 2: 提取所有 doc 文件（.md/...）
  2a: 在主进程对每个 .md 调 try_external_extractors，传入阶段 1 的 code_index
  2b: 按 ExtractionResult.merge_mode 决定是否跑默认 markdown + 是否标记跳过 LLM Tier 2
  2c: 外部返回 None 的 .md 归入既有 dispatch 走默认 extract_markdown
  2d: 后续 LLM 语义提取（Tier 2）跳过被标记 suppress_llm 的文件
```

**注意**：`merge` 模式下外部产出与默认 `extract_markdown` 产出**合并**而非替代——DDD 解析器产出 doc-anchor 节点 + describes/related 边，`extract_markdown` 产出 page/heading 节点 + contains/references 边，两者互补。

## 8. 非目标

- 不扩展 `file_type` 封闭枚举（不新增 `aggregate`/`bounded_context` 等类型）
- 不修改 `markdown.py` / `build.py` / `dedup.py` / `llm.py` 既有行为
- 不引入自定义去重逻辑（复用 graphify 原生 ghost-merge + dedup）
- 不实现 DDD 专用 LLM prompt（可选增强，非 MVP）
- 不处理非白名单的 `.md` 文件（普通 md 仍走默认 `extract_markdown` + LLM）
- 不实现 DDD 概念的语义检索（那是特性 2 的范围）
- 不在 `graphify query` / `explain` 文本输出里展示 `tags`/`desc` 等 DDD 字段（这些字段存于 `graph.json`，参与检索打分但不渲染到文本输出；可通过 MCP `get_node` 工具按 label/ID 查询访问）

## 9. 验收标准

| ID | 标准 | 验证方式 |
|---|---|---|
| AC1 | 白名单 7 类 DDD 文档被 DDD 解析器处理，非白名单 `.md` 走默认 `extract_markdown` | 跑 `graphify extract ./ddd-docs/`，检查 `graph.json` 中白名单文件的节点 `node_kind=="doc-anchor"`，非白名单的仍为 `"page"`/`"heading"` |
| AC2 | DDD 节点携带 `desc`/`concept_id`/`tags` 属性，存于 `graph.json` | 用 MCP `get_node` 工具或直接读 `graph.json` 验证字段存在 |
| AC3 | `<anchor:code>` 列匹配到真实 code 节点时，产出 `references` 边（doc-anchor → code） | `graphify query "OrderService"` 返回子图含 doc-anchor 节点 + code 节点 + 连接边 |
| AC4 | 未匹配的代码锚点记录到 `.graph/ddd-unmatched.json` | 文件存在，含 docPath/conceptId/anchor/reason |
| AC5 | 代码 AST 先于 doc 提取完成，DDD 解析器能引用 code_index | 单元测试 mock code_index，验证 DDD 解析器拿到非空索引 |
| AC6 | 外部解析器返回 None 时，回退到默认 `extract_markdown` | 单元测试：注册一个永远返回 None 的解析器，验证 fallback |
| AC7 | `merge_mode="merge"` 时，doc-anchor + page/heading 节点都存在 | 跑 DDD fixture，graph.json 含两类 node_kind |
| AC8 | `merge_mode="supplement_only"` + `suppress_llm=True` 时，该文件不跑 LLM Tier 2 | 单元测试 + 集成验证 `semantic_files` 集合排除了该文件 |
| AC9 | doc↔doc 边（related/categorized_under/cites）正确解析 | 单元测试：构造跨文件 concept_id 引用，验证 pending edge 解析成功 |
| AC10 | `tags` 参与字符串检索 | `graphify query "aggregate_root"` 命中 tags 含 `aggregate_root` 的节点 |
| AC11 | 改动不修改 `markdown.py` / `build.py` / `dedup.py` / `_DISPATCH` 既有条目 | `git diff` 这些文件为空 |
| AC12 | 回 upstream 时，删掉外部解析器模块 + 注册表 + 注入点 + serve.py 的 tags 拼接，graphify 行为不变 | 删除后跑 `pytest tests/ -q` 全绿 |

## 10. 风险

| 风险 | 缓解 |
|---|---|
| DDD 解析器的代码锚点匹配 false positive（如 `Order` 匹配到错误的 `OrderService`） | 参考 `ddd-code-matcher.mjs` 的严格优先级匹配，仅精确匹配（无 fuzzy fallback）；unmatched 记录便于人工排查 |
| 两阶段提取降低并行度（code 先于 doc） | code AST 提取本身仍是 `ProcessPoolExecutor` 并行；doc 阶段在 code 完成后启动，doc 在主进程顺序处理（doc 是 I/O 轻量，不走 tree-sitter，主进程足够） |
| 脚本与 LLM 产出同 `(source_file, label)` 的 concept 节点，ghost-merge 先到先得可能丢失 DDD 专属字段 | 接受此权衡：多数场景 label 不同不冲突；偶尔冲突时 graph 结构（doc-anchor 节点 + describes 边 + tags）仍保留主要价值 |
| doc↔doc 边的 concept_id 引用跨文件未解析 | §4.4 两阶段全局索引解析；单元测试覆盖跨文件引用 |
| `tags` 字段与 graphify 既有节点字段不冲突 | `tags` 是新字段，graphify 不识别但不拒绝；存于 graph.json 不影响 build/dedup；`serve.py` 的 `_node_search_text` 拼接是加法改动 |
| `<anchor:ddd>` 列名推断成 ddd_type 可能失败（自定义术语） | 推断失败时 tags 填 `"concept"` 兜底；原始列名信息可通过 `label`（业务术语）间接保留 |
