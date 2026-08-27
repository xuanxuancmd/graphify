# Spec: graphify 解析器扩展机制(Tier 1 + Tier 2)

> 关联:`plan.md`(同目录)是差异修复步骤。本文描述**当前已实现的 Tier 1 扩展机制** + **Tier 2 扩展的设计规格(待实现)**。
>
> 处理的文件不限于 doc — 可以是 YAML/JSON/CSV/DDL/Makefile 等任意文件类型。

---

## 1. 背景:graphify 的两层提取

graphify 把一个项目建模成知识图谱,提取分两层:

| 层 | 处理对象 | 引擎 | LLM? | 扩展点现状 |
|---|---|---|---|---|
| **Tier 1** | code(AST)+ markdown(逐行正则)+ 配置 JSON + 包清单 + 外部扩展 | 本地确定性 | ❌ | ✅ 已实现(`registry.py`),但扫描范围受限 |
| **Tier 2** | doc + paper + image 语义提取 | LLM | ✅ | ❌ 无扩展点,全局单一通用 prompt |

**数据流**:

```
文件 → detect() 分类
     → Tier 1: extract() 主进程
       ├─ try_external_extractors(path, root, code_index)  ← Tier 1 扩展点
       │   ├─ 命中 + merge_mode="merge"          → 外部 + 默认 markdown 合并, 进 Tier 2
       │   ├─ 命中 + merge_mode="replace"        → 只用外部, 进 Tier 2 (除非 suppress_llm)
       │   └─ 命中 + merge_mode="supplement_only" → 只用外部, 跳过 Tier 2
       ├─ 未命中 → 走默认 dispatch (AST / extract_markdown / json_config / manifest)
       └→ 返回 nodes/edges + suppress_llm_files
     → Tier 2: llm.py extract_files_direct
       └─ 对 semantic_files 用全局单一 _EXTRACTION_SYSTEM prompt  ← 无扩展点
     → build() → cluster() → export
```

**关键设计**: Tier 1 外部解析器可通过 `merge_mode` + `suppress_llm` 声明是否让文件继续走 Tier 2。这是两层之间的耦合点。

---

## 2. Tier 1 扩展:工具型解析器(已实现)

### 2.1 接口契约

三个公共符号,全在 `graphify/extractors/registry.py`(103 LOC):

```python
class DocExtractor(Protocol):
    def __call__(
        self, path: Path, *, root: Path, code_index: dict[str, list[dict]] | None = None
    ) -> "ExtractionResult | None":
        """返回 ExtractionResult 或 None(回退默认)。"""
        ...

@dataclass
class ExtractionResult:
    nodes: list[dict]           # 产出的节点
    edges: list[dict]           # 已解析的边
    hyperedges: list[dict] = field(default_factory=list)
    merge_mode: str = "merge"          # merge | replace | supplement_only
    suppress_llm: bool = False         # True = 跳过该文件的 LLM Tier 2
    unmatched: list[dict] = field(default_factory=list)       # 未匹配锚点
    pending_edges: list[dict] = field(default_factory=list)   # 跨文件未解析边

def register_doc_extractor(fn) -> fn:  # 装饰器,自注册
    ...

def try_external_extractors(path, *, root, code_index=None) -> ExtractionResult | None:
    ...  # 按注册顺序尝试, 第一个非 None 赢
```

### 2.2 三种合并策略(控制是否跳过 Tier 2)

`ExtractionResult.merge_mode` + `suppress_llm` 让**每个文件独立决定**是否继续跑默认 Tier 1 + Tier 2:

| `merge_mode` | 默认 markdown (Tier 1) | LLM Tier 2 | 适用场景 |
|---|---|---|---|
| `"merge"` (默认, DDD 推荐) | ✅ 跑(合并) | ✅ 跑 | 结构化锚点 + 章节层级 + 语义补充都有价值 |
| `"replace"` | ❌ 跳过 | ✅ 跑(除非 `suppress_llm=True`) | 不需要 page/heading,但要 LLM 语义 |
| `"supplement_only"` | ❌ 跳过 | ❌ 跳过 | 解析器完全自包含(如已结构化 YAML/JSON) |

`suppress_llm` 是 `replace`/`supplement_only` 模式下的额外开关;`merge` 模式下 LLM 总是跑。

> **为什么是文件级而非解析器级**: 同一个解析器对不同文件可以返回不同策略。比如 DDD 解析器对 `context-map.md` 用 `merge`(互补),对完全结构化的 YAML 用 `supplement_only`。

### 2.3 生产集成(已实现)

`graphify/extract.py` 的 `extract()` 函数已集成外部解析器(`extract.py:5719-5873`):

- `extract()` 签名含 `code_index: dict | None = None` 参数
- 主进程对每个文件调 `try_external_extractors(path, root=root, code_index=code_index)`
- 按 `merge_mode` 分流:
  - `merge`: 外部结果 + 默认 `extract_markdown` 合并,边按 `(source, target, relation)` 去重
  - `replace` / `supplement_only`: 只用外部结果
- `suppress_llm=True` 的文件加入 `suppress_llm_files` 集合,cli.py 构造 `semantic_files` 时排除
- `unmatched` 写入 `graphify-out/ddd-unmatched.json` sidecar
- `pending_edges` 透传给 `per_file`,后续做跨文件全局二次解析
- 返回值含 `"suppress_llm_files": suppress_llm_files`(`extract.py:7216`)

**两阶段提取**(已实现): cli.py 的 extract 命令分两阶段:
1. 阶段 1: code AST 并行提取(无 `code_index`),产出 code 节点
2. 阶段 2: doc/其他文件提取,传入 `code_index={"nodes": code_result["nodes"]}`,主进程跑外部解析器

### 2.4 检索集成(已实现)

`graphify/serve.py:328-370` 的 `_node_search_text` 条件拼接 `tags`:

```python
fields = (norm_label, label_tokens, nid_text, source, source_tokens)
tags = data.get("tags")
if isinstance(tags, list) and tags:
    fields += (" ".join(tags),)
```

**关键设计**: tags 只在节点实际携带非空 list 时追加。无 tags 字段的节点产出**字节级一致**的搜索文本(无尾随 NUL,无字段位移),行为与 upstream 完全一致。

`desc` 字段作为 embedding 文本源,参与 vector 检索。`norm_label`/`label_tokens`/`source_file` 参与字符串检索(exact/prefix/substring tier)。

效果:
- `graphify query "aggregate_root"` → 命中 tags 含 `aggregate_root` 的节点
- `graphify query "ddd"` → 命中所有 DDD 节点(tags 含 `ddd`)

### 2.5 节点建模约定

graphify 的 `file_type` 是封闭 6 值枚举(`code`/`document`/`concept`/`rationale`/`paper`/`image`),**不要新增枚举值**。自定义解析器的节点全部使用通用字段:

```python
{
    "id": "myformat_docs_config_xyz",        # _make_id() 生成, 符合 [a-z0-9_]
    "label": "可读名称",                       # 查询主匹配字段, 参与语义检索
    "file_type": "concept",                   # 复用既有枚举值
    "source_file": "docs/config.md",          # 相对 root 的路径
    "source_location": "L42",
    "node_kind": "doc-anchor",               # 与 page/heading 并列的结构化锚点
    "desc": "描述文字",                        # 参与 vector 检索(embedding 文本源)
    "concept_id": "原始 ID",                    # 跨文件边解析用, 保留原值不 normalize
    "tags": ["myformat", "subtype", "category"],  # 通用标签列表, 参与字符串检索
}
```

**关键约定**:
- **不要**用 `myformat_*` 前缀字段 — 全部通用,利于统一检索和去重
- 类型信息编码进 `tags` 列表(如 `["ddd", "aggregate_root", "domain-model"]`)
- `concept_id` 存原始值,不 normalize — 全局边解析靠它

### 2.6 边 shape

```python
{
    "source": "myformat_xxx_node1",
    "target": "src_module_service:MyService",   # 可指向 code 节点(跨类型)
    "relation": "references",                   # 复用 graphify 既有 relation
    "confidence": "EXTRACTED",
    "confidence_score": 1.0,
    "source_file": "docs/config.md",
    "source_location": "L15",
    "weight": 0.8,
}
```

`relation` 必须来自 graphify 既有封闭集合(见 `docs/modeling.md` §2.2)。常用的:
- `references` — doc→code 或 doc→doc 引用
- `cites` — doc→doc 显式引用(ADR/RFC 等)
- `conceptually_related_to` — doc↔doc 概念关联
- `contains` — 层级包含关系

### 2.7 参考实现:DDD 解析器

`graphify/extractors/ddd.py`(888 LOC)是完整参考实现,从 `parse-ddd-tables.mjs` 逐行移植。通过 `@register_doc_extractor` 自注册,注册触发在 `graphify/extractors/__init__.py:18`:

```python
from graphify.extractors import ddd  # noqa: F401  — triggers @register_doc_extractor
```

这一行是"开关"。删掉它,DDD 解析器不注册,graphify 行为与 upstream 完全一致。

**DDD 节点建模**:
- `file_type: "concept"`(不破坏封闭枚举)
- `node_kind: "doc-anchor"`(与 page/heading 并列)
- DDD 类型编码进 `tags: ["ddd", "<ddd_type>", "<doc_category>"]`
- `concept_id` 存原始值(如 `AG-01`),不 normalize

完整设计决策见 `docs/ddd-doc-extractor/spec.md` §4 和 §9(历史文档)。

### 2.8 测试覆盖

`tests/test_ddd_extractor.py`(514 LOC)覆盖:
- 白名单匹配 + 非白名单回退
- 代码锚点匹配(describes 边)
- 跨文件边解析(pending_edges)
- `merge` / `supplement_only` 模式 + `suppress_llm_files` 透传
- tags 检索(含无 tags 节点零干扰、非 list tags 优雅忽略)
- fixture 集成测试

### 2.9 当前限制(Gap)

已实现的 Tier 1 扩展机制有三个限制,见 `plan.md`:

| Gap | 描述 | 影响 |
|---|---|---|
| **Gap-1**: 扫描范围硬编码 | `extract.py:5827` `_DOC_EXTS_FOR_EXTERNAL = {".md", ".mdx", ".qmd", ".skill"}`,只对这些扩展名调 `try_external_extractors` | YAML/JSON/CSV 等文件无法被自定义解析器处理 |
| **Gap-2**: 无自动扫描目录 | 注册靠手动在 `__init__.py` 加 import 行 | 新增解析器需改 graphify 源码,项目级解析器无法独立维护 |
| **Gap-3**: 无项目级目录 | 解析器和内置语言解析器混在 `graphify/extractors/` 同一目录 | 合并 upstream 时 diff 不干净 |

---

## 3. Tier 2 扩展:提示词型解析器(待实现)

### 3.1 设计目标

让用户**不写代码**,通过声明文件定义自定义 LLM 提取 prompt + 输出 schema,graphify Tier 2 加载并按 per-file 路由。

**当前 Tier 2 无扩展点**: `llm.py` 的 `_EXTRACTION_SYSTEM` 是全局单一通用 prompt("extract named concepts, entities, citations..."),不区分文件类型,所有 doc 走同一个 prompt。

### 3.2 声明文件格式

**目录**: `.graph/extension/prompts/`

**格式**: YAML

**示例** (`.graph/extension/prompts/api-spec.yaml`):

```yaml
name: "api-spec-extractor"
description: "从 API 文档提取端点节点 + 请求/响应 schema 边"

# 文件匹配规则 (任一命中即归属)
match:
  extensions: [".yaml", ".yml"]           # 按扩展名
  filenames: ["openapi.yaml", "swagger.yaml"]  # 按文件名
  path_patterns: ["**/api/**"]             # 按 glob 路径
  content_contains: ["openapi:", "swagger:"]  # 按内容包含(可选)

# 命中此声明的文件是否跳过默认通用 prompt
suppress_default_prompt: true

# 自定义 prompt ({content} 占位符替换文件内容)
prompt: |
  你是一个 API 规范解析器。从以下 OpenAPI/Swagger 文档提取:
  1. 每个端点(endpoint)作为节点, file_type="concept", node_kind="doc-anchor"
  2. 端点之间的数据流作为边, relation="references"
  3. 请求/响应 schema 作为节点, file_type="concept"

  输出 JSON schema:
  {
    "nodes": [{"id": "...", "label": "...", "file_type": "concept", ...}],
    "edges": [{"source": "...", "target": "...", "relation": "references", ...}]
  }

  文档内容:
  <untrusted_source>
  {content}
  </untrusted_source>

# 输出 schema 校验 (可选)
output_schema:
  required_node_fields: ["id", "label", "file_type", "source_file"]
  required_edge_fields: ["source", "target", "relation", "confidence", "source_file"]
  valid_relations: ["references", "conceptually_related_to", "cites"]
  valid_confidences: ["EXTRACTED", "INFERRED", "AMBIGUOUS"]
```

### 3.3 prompt registry 设计

**新模块**: `graphify/prompt_registry.py`

核心数据结构:

```python
@dataclass
class PromptSpec:
    name: str
    description: str
    match: dict                    # {extensions, filenames, path_patterns, content_contains}
    prompt: str                    # prompt 模板, {content} 占位符替换文件内容
    suppress_default_prompt: bool = True  # 命中后是否跳过默认通用 prompt
    output_schema: dict | None = None     # 可选输出校验
```

核心函数:
- `load_prompts_from_dir(prompt_dir: Path)` — 扫描 `.graph/extension/prompts/*.yaml` 加载
- `find_prompt(path: Path, root: Path) -> PromptSpec | None` — 查找匹配文件的 prompt spec

### 3.4 Tier 2 集成点

**当前流程** (`cli.py:3809-3833`):
```python
from graphify.llm import _extraction_system as _sem_prompt_for
sem_prompt = _sem_prompt_for(deep=deep_mode)
# 对所有 semantic_files 用同一个 prompt
```

**改动后**:
```python
from graphify.prompt_registry import find_prompt, load_prompts_from_dir

# 1. 启动时加载 prompt registry (一次)
load_prompts_from_dir(Path.cwd() / ".graph" / "extension" / "prompts")

# 2. 对每个 semantic_file 查 registry
for path in semantic_files:
    spec = find_prompt(path, root)
    if spec:
        # 用自定义 prompt, {content} 替换为文件内容
        content = path.read_text(encoding="utf-8", errors="replace")
        prompt = spec.prompt.replace("{content}", content)
        # 调 LLM, 产出 JSON, 校验 output_schema
    else:
        # 用默认通用 prompt (现有逻辑不变)
        prompt = _sem_prompt_for(deep=deep_mode)
```

### 3.5 IDE 会话内 vs headless CLI

**IDE 会话内** (`/graphify .` skill):
- skill 指令识别 `.graph/extension/prompts/` 目录
- 对命中的文件,让 IDE AI 工具按自定义 prompt 提取
- 不需要 API key

**headless CLI** (`graphify extract --backend X`):
- `llm.py` 的 `extract_files_direct` / `_call_llm` 按配置 backend 调 LLM
- 读取 prompt registry,对命中文件用自定义 prompt
- 需要 API key 或 claude-cli

### 3.6 安全

- prompt 模板中的 `{content}` 占位符用文件实际内容替换
- 文件内容包裹在 `<untrusted_source>...</untrusted_source>` 块中(复用 `llm.py` 的注入防御)
- `_INJECTION_SENTINELS` 正则中和 prompt 注入哨兵(复用现有机制)

### 3.7 与 Tier 1 的关系

两层独立,不共用接口:

| 维度 | Tier 1 工具型 | Tier 2 提示词型 |
|---|---|---|
| 形态 | Python 模块 | YAML 声明文件 |
| 注册 | `@register_doc_extractor` | 声明文件放约定目录自动扫描 |
| 执行 | `extract.py` 主进程 | IDE AI 工具 / `llm.py` backend |
| 返回 | `ExtractionResult` dataclass | LLM 产出 JSON(按 schema) |
| git hook 自动触发 | ✅ | ❌(需手动 `/graphify --update`) |
| 适合 | 结构化格式(YAML/JSON/CSV/DDL) | 半结构化文档(需求/API 文档/会议纪要) |

**耦合点**: Tier 1 解析器可通过 `suppress_llm=True` 声明跳过 Tier 2,包括跳过 Tier 2 的自定义 prompt。

---

## 4. 整体架构图

```
┌──────────────────────────────────────────────────────────┐
│  detect()  文件分类: code / document / paper / image      │
└──────────────────────┬───────────────────────────────────┘
                       │
       ┌───────────────┴────────────────┐
       ▼                                ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│  Tier 1 本地提取          │  │  Tier 2 LLM 提取          │
│  (确定性, 无 LLM)         │  │  (语义, 需 LLM)           │
│                          │  │                          │
│ ┌──────────────────────┐ │  │ ┌──────────────────────┐ │
│ │ 内置提取器            │ │  │ │ 默认通用 prompt      │ │
│ │ - AST (code, 37 lang) │ │  │ │ _EXTRACTION_SYSTEM   │ │
│ │ - 正则 (.md)          │ │  │ │ (extraction-spec.md) │ │
│ │ - JSON config         │ │  │ └──────────────────────┘ │
│ │ - 包清单 (manifest)    │ │  │                          │
│ └──────────────────────┘ │  │ ┌──────────────────────┐ │
│                          │  │ │ prompt registry      │ │ ← Gap-4
│ ┌──────────────────────┐ │  │ │ (per-file 自定义     │ │ (待实现)
│ │ Tier 1 扩展 (已实现)  │ │  │ │  prompt + schema)    │ │
│ │ (registry.py)        │ │  │ └──────────────────────┘ │
│ │ - DDD 解析器          │ │  │                          │
│ │ - 自定义解析器         │ │  │ suppress_llm_files 过滤  │
│ └──────────────────────┘ │  │ (Tier 1 声明跳过的文件   │
│                          │  │  不进 Tier 2)            │
│ 扫描目录:                │  │                          │
│ - graphify/extractors/   │  │ 扫描目录:                │
│   (当前混排)              │  │ - .graph/extension/      │ ← Gap-4
│                          │  │   prompts/  (待实现)      │
│ Gap-1: 扫描范围硬编码     │  │                          │
│ Gap-2: 无自动扫描         │  │ 触发方式:                │
│ Gap-3: 无项目级目录       │  │ - IDE /graphify .        │
│                          │  │ - headless graphify      │
│ 触发方式:                │  │   extract --backend X    │
│ - git commit hook 自动   │  │ - git commit 不触发       │
│ - /graphify .            │  │   (需手动 --update)      │
│ - graphify extract       │  │                          │
└──────────────────────────┘  └──────────────────────────┘
```

---

## 5. Gap 汇总

| Gap | 层 | 描述 | 状态 |
|---|---|---|---|
| Gap-1 | Tier 1 | 扫描范围硬编码为 `.md`/`.mdx`/`.qmd`/`.skill`,不支持任意文件类型 | 待实现 |
| Gap-2 | Tier 1 | 无自动扫描目录,注册靠手动 import | 待实现 |
| Gap-3 | Tier 1 | 无项目级目录,解析器和内置混排 | 待实现 |
| Gap-4 | Tier 2 | 无 prompt registry,全局单一通用 prompt | 待实现 |
| Gap-5 | Tier 1 | 当前两阶段(code+配置混合→文档),需改为三阶段(代码→配置文件→文档) | 待实现 |
| Gap-6 | Tier 1 | DDD 代码锚点匹配不支持全限定名、多匹配只取第一个、无置信度标注 | 待实现 |
| Gap-7 | Tier 1 | URL 锚点匹配失效(endpoint_index 几乎为空),需路径规范化 + endpoint 节点产出 | 待实现 |

详见 `plan.md` 的修复步骤。

---

## 6. 回 upstream 策略

Tier 1 扩展点设计为零侵入,回 upstream 时按需删除:

| 场景 | 操作 |
|---|---|
| 合并 upstream 新代码 | 保留 `registry.py` + `ddd.py` + `extract.py` 注入分支 + `serve.py` tags 拼接 + 自动扫描;合并 upstream 其余改动 |
| upstream 也加了类似机制 | 评估是否弃用自己的 registry,迁移到 upstream 机制 |
| 完全回到原始 graphify | 删 `registry.py`、`ddd.py`、`custom/` 目录、`__init__.py` 扫描逻辑、`extract.py` 注入分支、`serve.py` tags 拼接、`prompt_registry.py`、测试、fixture |

---

## 7. 验收标准

| ID | 标准 | 验证方式 | 状态 |
|---|---|---|---|
| AC1 | Tier 1 `ExtractionResult` dataclass + `register_doc_extractor` + `try_external_extractors` 可用 | 单元测试 | ✅ 已实现 |
| AC2 | Tier 1 `extract.py` 主进程注入 + `code_index` + `suppress_llm_files` 透传 | 集成测试 | ✅ 已实现 |
| AC3 | Tier 1 `serve.py` tags 检索(条件拼接,无 tags 零干扰) | `test_tags_retrieval_*` | ✅ 已实现 |
| AC4 | Tier 1 DDD 解析器(888 LOC 参考实现) | fixture 测试 | ✅ 已实现 |
| AC5 | Tier 1 工具型解析器可声明处理任意扩展名(YAML/JSON/CSV) | 写 YAML 解析器测试 | ❌ 待 Gap-1 |
| AC6 | Tier 1 内置目录 `graphify/extractors/custom/` 自动扫描 | 放 .py 自动注册 | ❌ 待 Gap-2 |
| AC7 | Tier 1 项目级目录 `.graph/extension/extractors/` 自动扫描 | 放 .py 自动注册 | ❌ 待 Gap-3 |
| AC8 | Tier 1 项目级优先级 > 内置(同名 prepend) | 同名解析器项目级赢 | ❌ 待 Gap-3 |
| AC9 | Tier 1 单个解析器 import 失败不拖垮启动 | 故意写失败解析器,graphify 正常启动 | ❌ 待 Gap-2 |
| AC10 | Tier 2 prompt registry 加载 `.graph/extension/prompts/*.yaml` | 放 yaml,find_prompt 返回匹配 | ❌ 待 Gap-4 |
| AC11 | Tier 2 命中 prompt spec 的文件用自定义 prompt | mock LLM,验证传入 prompt 是自定义的 | ❌ 待 Gap-4 |
| AC12 | Tier 2 未命中 prompt spec 的文件用默认 prompt | 现有行为不变 | ❌ 待 Gap-4 |
| AC13 | tags 参与字符串检索 | `graphify query "aggregate_root"` 命中 | ✅ 已实现 |
| AC14 | 改动不修改 markdown.py / build.py / dedup.py 既有行为 | git diff 为空 | ✅ 已实现 |

---

## 8. 代码提交阶段的图谱更新方案

> 关联:`plan_commit.md`(同目录)是提交阶段的能力补齐步骤。本节描述**提交阶段图谱更新的整体设计**。

### 8.1 设计原则:文件级增量,不做文件内增量

graphify 的增量模型是**文件级**的:框架告诉处理器"哪些文件变了",处理器对每个文件**全量解析**。不传递 diff 内容,不支持文件内增量解析。

**为什么不做文件内增量**:

| 维度 | 判断 |
|---|---|
| 配置文件大小 | 通常 KB 级,全量解析 < 10ms,获取/传递 diff 的成本可能超过解析本身 |
| md 文档解析 | 逐行正则,500 行 < 50ms,瓶颈不在 Tier1 解析 |
| Tier2 LLM 成本 | LLM 本身就是全量的(整个文件内容发给模型),文件内增量无法减少 LLM 调用成本 |
| content hash 缓存 | 已避免"mtime 变了但内容没变"的无效解析(`cache.py:924`),内容没变根本不调处理器 |
| 实现复杂度 | 文件内增量需要 diff 解析 + 旧节点加载 + 行号映射,ROI 低 |

**结论**:文件级增量(`changed_paths`)+ 内容缓存(content hash)是当前最优方案。处理器层全量解析是合理的设计选择,**不需要为处理器增加文件内增量接口**。

### 8.2 增量信息传递:当前机制

```
git commit
  └─ post-commit hook (hooks.py:307)
      └─ CHANGED=$(git diff --name-only HEAD~1 HEAD)    ← 只取文件名, 不取 diff 内容
      └─ export GRAPHIFY_CHANGED="$CHANGED"
      └─ 后台 Python 进程 (hooks.py:136)
          └─ changed = [Path(f.strip()) for f in changed_raw.splitlines()]
          └─ _rebuild_code(root, changed_paths=changed)   ← 传入 list[Path]
              └─ extract(extract_targets)                   ← 处理器只收到文件路径
```

**入参形式**:`changed_paths: list[Path]` — 仅文件路径列表,无 diff 内容。

**缓存命中**:处理器被调之前,`extract()` 先查 `load_cached(path)`(`extract.py:5884`),content hash 命中则直接复用缓存结果,处理器根本不被调用。

### 8.3 各类文件在提交阶段的处理策略

| 文件类型 | Tier1 提取器 | hook 自动? | 增量机制 | 处理器被调时做什么 |
|---|---|---|---|---|
| 代码 (.py/.ts/…) | ✅ tree-sitter | ✅ | ast_hash + changed_paths | 全量 AST 重解析 |
| package manifest (apm.yml/pyproject.toml) | ✅ extract_package_manifest | ✅ | ast_hash + changed_paths | 全量解析 |
| markdown (.md) | ✅ extract_markdown | ⚠️ 有条件(见下) | ast_hash + changed_paths | 全量逐行正则解析 |
| 普通 yaml (.yaml/.yml) | 按需扩展(框架支持,用户编写) | ✅(接入后自动) | ast_hash + changed_paths | 全量解析 |
| ddd 文档 (.md 白名单) | ✅ extract_ddd | ❌ hook 不跑(需 code_index) | — | — |
| paper/image | ❌ | ❌ | — | — |

### 8.4 markdown 的"有条件"自动处理

post-commit hook(`_rebuild_code`)对 .md 的处理逻辑(`watch.py:1219-1368`):

- **新 .md(从未跑过 LLM)**:✅ 自动跑 `extract_markdown`,生成 page/heading 节点,写 ast_hash
- **已跑过 Tier2 LLM 的 .md**:❌ 被 `semantic_doc_set` 排除(`watch.py:1308-1324`),hook 不再快扫

原因(`watch.py:1232`):避免 AST heading 节点与 LLM 语义节点重复,导致 4 倍图膨胀。

**影响**:一旦 .md 跑过 `graphify extract`(Tier2),后续 commit 改了该 .md,hook 不会自动更新它的 Tier1 节点。需手动 `graphify extract --update` 刷新。

### 8.5 ddd / 外部解析器在提交阶段的限制

ddd 解析器虽纯本地无 LLM,但**不在 post-commit hook 里跑**。根本原因:

- `_rebuild_code` 调 `extract()` 时**不传 `code_index`**(`watch.py:1454-1462`)
- `try_external_extractors` 只在 `code_index is not None` 时被调用(`extract.py:5825`)
- ddd 需要 code_index 做 code-anchor 匹配(`ddd.py:847` `_build_code_indices`)

**影响**:commit 改了 ddd 文档,hook 不更新 ddd 节点。需手动 `graphify extract --update`(它会先跑代码 AST,再传 code_index 给 ddd)。

### 8.6 自定义解析器在提交阶段的接入要求

自定义解析器要在提交阶段被 hook 自动处理,需满足:

1. **注册到 `_DISPATCH` 表**(对于新扩展名)或**通过 `@register_doc_extractor` 注册**(对于 .md 等 DOC 扩展名)
2. **不依赖 `code_index`**(当前 hook 不传 code_index);或接受 hook 阶段降级(不跑 code-anchor 匹配)
3. **处理 `semantic_doc_set` 排除**:如果该文件已跑过 Tier2 LLM,hook 会跳过它

**两种自定义解析器的接入方式**:

| 解析器类型 | 处理对象 | 注册方式 | hook 自动? |
|---|---|---|---|
| 配置文件解析器 (YAML/JSON/CSV) | 新扩展名 | `_DISPATCH[".yaml"] = extract_yaml` | ✅(接入后自动) |
| md 文档解析器 (如 ddd) | .md 白名单子集 | `@register_doc_extractor(extract_xxx)` | ❌(需传 code_index,见 §8.5) |

### 8.7 提交阶段整体流程(目标态)

```
git commit
  └─ post-commit hook
      └─ CHANGED=$(git diff --name-only HEAD~1 HEAD)
      └─ _rebuild_code(root, changed_paths=CHANGED)
          │
          ├─ 1. detect() → 文件分类
          │   └─ 代码 → code_files
          │   └─ 配置文件(有提取器的) → code_files (via _get_extractor)
          │   └─ md(无语义层的) → code_files
          │
          ├─ 2. 增量过滤
          │   └─ changed_paths ∩ code_files → extract_targets
          │   └─ deleted_paths → 标记清理
          │
          ├─ 3. extract(extract_targets)
          │   ├─ load_cached(path) 查 content hash
          │   │   ├─ 命中 → 直接复用,不调处理器
          │   │   └─ 未命中 → 调处理器全量解析
          │   │       ├─ 代码 → tree-sitter AST
          │   │       ├─ 配置文件 → 自定义解析器 (如 extract_yaml)
          │   │       └─ md → extract_markdown / extract_ddd
          │   └─ save_cached() 写缓存
          │
          ├─ 4. _reconcile_existing_graph()
          │   └─ 用新结果替换 changed 文件的旧节点,保留 unchanged 文件的节点
          │
          └─ 5. save_manifest(kind="ast") → 更新 ast_hash

  手动补充 (Tier2):
  graphify extract --update
      └─ detect_incremental(kind="semantic") → 比对 semantic_hash
      └─ 对变化的文件跑 Tier1.5 (ddd, 传 code_index) + Tier2 (LLM)
      └─ save_manifest(kind="both") → 更新 semantic_hash
```

### 8.8 提交阶段 vs 手动更新的职责分工

| 职责 | 提交阶段 (hook 自动) | 手动更新 (graphify extract --update) |
|---|---|---|
| Tier1 代码 AST | ✅ | ✅ |
| Tier1 配置文件(有提取器) | ✅(接入后) | ✅ |
| Tier1 markdown(无语义层) | ✅ | ✅ |
| Tier1 markdown(有语义层) | ❌ 跳过 | ✅ |
| Tier1.5 ddd / 外部解析器(需 code_index) | ❌ | ✅ |
| Tier2 LLM 语义 | ❌ | ✅ |
| manifest hash | ast_hash | semantic_hash + ast_hash |

**设计意图**:hook 保持快速(纯本地,无 LLM,秒级完成),Tier2 语义提取留给手动触发(慢,需 API key)。
