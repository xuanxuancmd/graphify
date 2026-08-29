# Spec: graphify 解析器扩展机制(Tier 1 + Tier 2)

> 关联:`plan.md`(差异修复步骤)、`plan-gap.md`(能力补齐清单)。本文是 Tier 1 + Tier 2 扩展机制的规格文档。

---

## 1. 背景:graphify 的两层提取

graphify 把一个项目建模成知识图谱,提取分两层:

| 层 | 处理对象 | 引擎 | LLM? | 扩展点 |
|---|---|---|---|---|
| **Tier 1** | code(AST)+ markdown(逐行正则)+ 配置 JSON + 包清单 + 外部扩展 | 本地确定性 | ❌ | `registry.py` 工具型解析器 |
| **Tier 2** | doc + paper + image 语义提取 | LLM | ✅ | `prompt_registry.py` 提示词型解析器 |

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
       └─ prompt registry 路由(match.files glob)
         ├─ 匹配 spec 的文件 → 组成一个 chunk + 自定义 prompt(mode=replace/merge)
         └─ 未匹配的文件 → _chunk_within_caps + 默认 _EXTRACTION_SYSTEM
     → build() → cluster() → export
```

**关键设计**: Tier 1 外部解析器可通过 `merge_mode` + `suppress_llm` 声明是否让文件继续走 Tier 2。这是两层之间的耦合点。

---

## 2. Tier 1 扩展:工具型解析器

### 2.1 接口契约

全部公共符号在 `graphify/extractors/registry.py`。

**DocExtractor Protocol** — 解析器函数签名:

- 参数: `path: Path`, `root: Path`, `nodes: list[dict] | None`(已提取的 AST + config 节点,供锚点匹配)
- 返回: `ExtractionResult | None`(`None` = 不是我的文件,回退默认)

**ExtractionResult dataclass** — 解析器产出:

| 字段 | 类型 | 说明 |
|---|---|---|
| `nodes` | `list[dict]` | 产出的节点 |
| `edges` | `list[dict]` | 已解析的边 |
| `hyperedges` | `list[dict]` | 超边(默认空) |
| `merge_mode` | `str` | `merge` / `replace` / `supplement_only`(默认 `merge`) |
| `suppress_llm` | `bool` | `True` = 跳过该文件的 LLM Tier 2(默认 `False`) |
| `unmatched` | `list[dict]` | 未匹配锚点(写入 sidecar 供排查) |
| `pending_edges` | `list[dict]` | 跨文件未解析边(供全局二次解析) |

**register_doc_extractor 装饰器** — 自注册:

| 参数 | 说明 |
|---|---|
| `priority` | `"append"`(内置,后置) / `"prepend"`(项目级,前置优先) |
| `extensions` | 声明认领的文件扩展名集合(如 `{".yaml", ".yml"}`),供 hook/watch 识别 |

**try_external_extractors** — 按注册顺序尝试,第一个非 None 结果胜出。

### 2.2 三种合并策略

`merge_mode` + `suppress_llm` 让**每个文件独立决定**是否继续跑默认 Tier 1 + Tier 2:

| `merge_mode` | 默认 markdown (Tier 1) | LLM Tier 2 | 适用场景 |
|---|---|---|---|
| `merge` (默认) | ✅ 跑(合并) | ✅ 跑 | 结构化锚点 + 章节层级 + 语义补充都有价值 |
| `replace` | ❌ 跳过 | ✅ 跑(除非 `suppress_llm=True`) | 不需要 page/heading,但要 LLM 语义 |
| `supplement_only` | ❌ 跳过 | ❌ 跳过 | 解析器完全自包含(如已结构化 YAML/JSON) |

`suppress_llm` 是 `replace`/`supplement_only` 模式下的额外开关;`merge` 模式下 LLM 总是跑。

> **为什么是文件级而非解析器级**: 同一个解析器对不同文件可以返回不同策略。

### 2.3 生产集成

`extract()` 函数已集成外部解析器:

- 主进程对每个文件调 `try_external_extractors(path, root=root, nodes=code_index)`
- 按 `merge_mode` 分流(merge 时合并默认 markdown,边按 `(source, target, relation)` 去重)
- `suppress_llm=True` 的文件加入 `suppress_llm_files` 集合,cli.py 构造 `semantic_files` 时排除
- `unmatched` 写入 `.graph/ddd-unmatched.json` sidecar
- `pending_edges` 透传,后续做跨文件全局二次解析

**两阶段提取**: cli.py 先提取 code AST(不传 `code_index`),再提取 doc/其他文件(传 `code_index`),确保 doc 解析器能引用已抽取的 code 节点。

### 2.4 检索集成

`serve.py` 的 `_node_search_text` 条件拼接 `tags` 字段:只在节点实际携带非空 list 时追加,无 tags 字段的节点产出**字节级一致**的搜索文本,行为与 upstream 完全一致。

`desc` 字段作为 embedding 文本源,参与 vector 检索。`norm_label`/`label_tokens`/`source_file` 参与字符串检索。

### 2.5 节点建模约定

`file_type` 是封闭 6 值枚举(`code`/`document`/`concept`/`rationale`/`paper`/`image`),**不要新增枚举值**。自定义解析器的节点全部使用通用字段:

| 字段 | 说明 |
|---|---|
| `id` | `_make_id()` 生成,符合 `[a-z0-9_]` |
| `label` | 可读名称,查询主匹配字段 |
| `file_type` | 复用既有枚举值 |
| `source_file` | 相对 root 的路径 |
| `source_location` | 行号(如 `L42`) |
| `node_kind` | 结构化锚点标记(如 `doc-anchor`,与 `page`/`heading` 并列) |
| `desc` | 描述文字,参与 vector 检索 |
| `concept_id` | 原始 ID,跨文件边解析用,保留原值不 normalize |
| `tags` | 通用标签列表,参与字符串检索 |

**关键约定**: 不用前缀专属字段,类型信息编码进 `tags` 列表,`concept_id` 存原始值不 normalize。

### 2.6 边 shape

| 字段 | 说明 |
|---|---|
| `source` / `target` | 节点 id(可跨类型:doc→code) |
| `relation` | 必须来自 graphify 既有封闭集合 |
| `confidence` | `EXTRACTED` / `INFERRED` / `AMBIGUOUS` |
| `confidence_score` | 0.0-1.0 |
| `source_file` | 相对路径 |
| `weight` | 边权重 |

常用 relation: `references`(doc→code/doc 引用)、`cites`(显式引用)、`conceptually_related_to`(概念关联)、`contains`(层级包含)。

### 2.7 参考实现

- `graphify/extractors/custom/swagger.py` — 结构化 YAML,`replace + suppress_llm=True`(纯 Tier 1,零 LLM)
- `graphify/extractors/custom/ddd.py` — 半结构化 markdown 表格,`merge + suppress_llm=False`(Tier 1 结构化锚点 + Tier 2 语义补充)

### 2.8 扫描目录

Tier 1 支持两个扫描目录,对称于 Tier 2:

| 目录 | 优先级 | 说明 |
|---|---|---|
| `graphify/extractors/custom/` | 内置(append) | 随 graphify 包发布 |
| `.graph/extension/extractors/` | 项目级(prepend) | 用户项目级,优先于内置同名解析器 |

自动扫描机制: `__init__.py` 用 `pkgutil.iter_modules` 扫描两个目录,每个 `.py` 文件用 `try/except` 独立导入,单个解析器 import 失败不拖垮启动。

---

## 3. Tier 2 扩展:提示词型解析器

### 3.1 设计目标

让用户**不写任何 Python 代码**,仅通过 YAML 声明文件定义关心的文件名(支持通配)和配套的 LLM 提取 prompt。graphify Tier 2 加载声明文件,对匹配的文件用自定义 prompt 提取,未匹配的文件走默认通用 prompt。执行路径与当前 Tier 2 语义提取完全一致,不引入新的依赖。

### 3.2 声明文件格式

**目录**: `.graph/extension/prompts/`(项目级,用户自定义)

**格式**: YAML,纯声明式,零 Python 代码

**PromptSpec 字段**:

| 字段 | 类型 | 说明 |
|---|---|---|
| `name` | `str` | spec 名称 |
| `description` | `str` | 描述 |
| `match.files` | `list[str]` | 路径 glob 数组,任一命中即归属该 prompt |
| `mode` | `str` | `replace`(默认) / `merge` |
| `prompt` | `str` | 自定义 system prompt(只写指令部分,不含文件内容) |
| `output_schema` | `dict \| None` | 可选输出校验(在 `validate_extraction` 之后加严) |

**glob 匹配规则**:
- `*` 不跨 `/`(匹配单层路径段)
- `**` 跨任意层目录
- 匹配相对 root 的 posix 路径
- 多个 spec 按列表顺序尝试,第一个匹配的赢

**output_schema 字段**(可选):

| 字段 | 说明 |
|---|---|
| `required_node_fields` | 节点必填字段(在标准 schema 之上加严) |
| `required_edge_fields` | 边必填字段 |
| `valid_file_types` | 允许的 file_type 子集 |
| `valid_relations` | 允许的 relation 子集 |
| `valid_confidences` | 允许的 confidence 子集 |

### 3.3 两种 mode

| mode | 自定义 prompt | 默认 prompt | LLM 调用 | 适用场景 |
|---|---|---|---|---|
| `replace`(推荐默认) | ✅ 跑 | ❌ 跳过 | 1 次 | 自定义 prompt 已覆盖全部提取需求 |
| `merge` | ✅ 跑 | ✅ 也跑 | 2 次 | 自定义提取特定结构 + 默认补充通用语义,两者互补 |

**与 Tier 1 的关键区别**: Tier 1 `merge` 成本极低(本地正则),Tier 2 `merge` 成本翻倍(双 LLM 调用 + 双 token),默认推荐 replace。`merge` 模式的两次 LLM 结果走 graphify 原生去重(ghost-merge + deduplicate_entities),不引入自定义去重逻辑。

**第三种"跳过"由 Tier 1 控制**: Tier 1 解析器通过 `suppress_llm=True` 跳过整个 Tier 2(包括自定义 prompt 和默认 prompt)。

### 3.4 chunk 策略

每个 PromptSpec 匹配到的所有文件组成**一个 chunk**,一次 LLM 调用(用该 spec 的自定义 prompt)。不与默认 prompt 的文件流混合。

```
semantic_files(Tier 1 suppress_llm 过滤后)
  ├─ find_prompt() 路由,分成 N 组
  ├─ 每组独立处理:
  │   ├─ 默认组(无匹配 spec): 走原有 _chunk_within_caps() + _EXTRACTION_SYSTEM
  │   └─ 自定义组: 组成一个 chunk → 一次 LLM 调用(自定义 prompt)
  │       └─ mode=merge → 再跑一次默认 prompt,结果合并
  └─ 合并所有 LLM 结果
```

**超 cap 退化**: 若匹配文件总大小超过 chunk cap,退化到 `_chunk_within_caps()` 再分,但每个子 chunk 仍用同一自定义 prompt。

### 3.5 prompt registry 接口契约

模块: `graphify/prompt_registry.py`

**PromptSpec dataclass** — 见 §3.2 字段表。`eq=False`,用对象身份做相等性比较,`__hash__` 基于 `name`。

| 函数 | 签名 | 说明 |
|---|---|---|
| `load_prompts_from_dir` | `(prompt_dir: Path) -> list[PromptSpec]` | 扫描 `*.yaml`,malformed 文件跳过不中断 |
| `load_builtin_prompts` | `() -> list[PromptSpec]` | 扫描 `graphify/prompts/`(包内内置,当前为空) |
| `load_all_prompts` | `(project_dir: Path \| None = None) -> list[PromptSpec]` | 合并内置 + 项目级,项目级前置(优先) |
| `find_prompt` | `(path, root, specs) -> PromptSpec \| None` | 按 `match.files` glob 匹配,第一个匹配的赢 |
| `group_by_prompt` | `(files, root, specs) -> dict[PromptSpec \| None, list[Path]]` | 按 prompt 分组,未匹配 → `None` key |

### 3.6 Tier 2 集成点

`cli.py` 的 semantic extraction 阶段:

1. `load_all_prompts()` 加载内置 + 项目级 prompt spec(项目级优先)
2. `group_by_prompt()` 把 uncached semantic_files 按 prompt 分组
3. 每组独立调 `extract_corpus_parallel(system_prompt=spec.prompt if spec else None)`
4. `mode=merge` 时对同一组文件先跑自定义 prompt 再跑默认 prompt,结果合并
5. 缓存按组用各自的 prompt 指纹写入(编辑自定义 prompt 会失效缓存)
6. `output_schema` 校验在 `validate_extraction` 之后执行,违规时打印 warning

**`extract_files_direct` 改动**: 新增 `system_prompt: str | None = None` 参数。传 `None` 用默认 `_EXTRACTION_SYSTEM`;传自定义 prompt 替换 system message。`system_prompt` 沿调用链透传:`extract_corpus_parallel` → `_extract_with_adaptive_retry` → `extract_files_direct` → 5 个 `_call_*` 函数。retry/bisection 路径也透传,确保截断/超时重试不丢失自定义 prompt。

### 3.7 两层开关交互

```
Tier 1 merge_mode     suppress_llm    → Tier 2 行为
──────────────────────────────────────────────────────
merge                 false           → 进 Tier 2,按 Tier 2 mode 路由
                                     mode=replace → 自定义 prompt
                                     mode=merge   → 自定义 + 默认都跑
replace               false           → 同上
replace               true            → 跳过 Tier 2(不跑任何 LLM)
supplement_only       (隐含 true)     → 跳过 Tier 2
```

**Tier 1 `suppress_llm=True` 是总开关**,优先于 Tier 2 mode。

### 3.8 安全

- 自定义 prompt 只写指令部分(system message),文件内容由 `_read_files()` 用 `<untrusted_source>` 块包装后注入
- 自定义 prompt 前置 `_SECURITY_PREAMBLE`(注入防御指令),确保模型将 `<untrusted_source>` 块视为 inert data
- `_INJECTION_SENTINELS` 正则中和 prompt 注入哨兵(复用现有机制)
- prompt 不接触文件读取,不存在占位符注入风险

### 3.9 扫描目录

Tier 2 支持两个扫描目录,对称于 Tier 1:

| 目录 | 优先级 | 说明 |
|---|---|---|
| `graphify/prompts/` | 内置(append) | 随 graphify 包发布(当前为空,预留) |
| `.graph/extension/prompts/` | 项目级(prepend) | 用户项目级,优先于内置同名 spec |

项目级 spec 排在列表前面,`find_prompt` 按顺序匹配,第一个匹配的赢——项目级覆盖内置。

### 3.10 与 Tier 1 的关系

| 维度 | Tier 1 工具型 | Tier 2 提示词型 |
|---|---|---|
| 形态 | Python 模块 | YAML 声明文件 |
| 注册 | `@register_doc_extractor` | 声明文件放约定目录自动扫描 |
| 执行 | `extract.py` 主进程(本地) | IDE AI 工具 / `llm.py` backend |
| 返回 | `ExtractionResult` dataclass | LLM 产出 JSON(按 schema) |
| 合并策略 | `merge_mode`: merge/replace/supplement_only | `mode`: replace/merge |
| 跳过对方 | `suppress_llm=True` 跳过 Tier 2 | (无,Tier 2 不能跳过 Tier 1) |
| 内置目录 | `graphify/extractors/custom/` | `graphify/prompts/`(预留) |
| 项目级目录 | `.graph/extension/extractors/` | `.graph/extension/prompts/` |
| git hook 自动触发 | ✅ | ❌(需手动 `/graphify --update`) |
| 适合 | 结构化格式(YAML/JSON/CSV/DDL) | 半结构化文档(需求/API 文档/会议纪要) |

**耦合点**: Tier 1 解析器可通过 `suppress_llm=True` 声明跳过 Tier 2。Tier 2 不能反向跳过 Tier 1。

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
│ │ - 正则 (.md)          │ │  │ │ (未匹配 spec 的文件) │ │
│ │ - JSON config         │ │  │ └──────────────────────┘ │
│ │ - 包清单 (manifest)    │ │  │                          │
│ └──────────────────────┘ │  │ ┌──────────────────────┐ │
│                          │  │ │ prompt registry      │ │
│ ┌──────────────────────┐ │  │ │ 内置: graphify/     │ │
│ │ Tier 1 扩展           │ │  │ │   prompts/ (预留)    │ │
│ │ (registry.py)        │ │  │ │ 项目级: .graph/     │ │
│ │ - DDD 解析器          │ │  │ │   extension/prompts/│ │
│ │ - Swagger 解析器       │ │  │ │ match.files glob     │ │
│ │ - 自定义解析器         │ │  │ │ mode: replace|merge  │ │
│ └──────────────────────┘ │  │ │ 匹配文件→一个 chunk  │ │
│                          │  │ └──────────────────────┘ │
│ 扫描目录:                │  │                          │
│ - graphify/extractors/   │  │ suppress_llm_files 过滤  │
│   custom/ (内置)         │  │ (Tier 1 声明跳过的文件   │
│ - .graph/extension/      │  │  不进 Tier 2,优先于 mode)│
│   extractors/ (项目级)    │  │                          │
│                          │  │ 执行路径(与当前一致):    │
│ 触发方式:                │  │ - IDE /graphify .        │
│ - git commit hook 自动   │  │ - headless graphify      │
│ - /graphify .            │  │   extract                │
│ - graphify extract       │  │ - git commit 不触发       │
│                          │  │   (需手动 --update)      │
└──────────────────────────┘  └──────────────────────────┘
```

---

## 5. 外部集成方式

### 5.1 选层

| 判断 | 选哪层 | 扩展形态 |
|---|---|---|
| 文件是结构化格式(YAML/JSON/CSV/DDL),可用代码精确解析 | Tier 1 | Python 模块 |
| 文件是半结构化文档(需求/API 文档/会议纪要),需 LLM 理解语义 | Tier 2 | YAML 声明文件,零代码 |

### 5.2 Tier 1 扩展步骤

1. 创建解析器模块,放在 `graphify/extractors/custom/`(内置)或 `.graph/extension/extractors/`(项目级,优先级更高)。
2. 实现 `extract_xxx` 函数,签名遵循 `DocExtractor` Protocol,返回 `ExtractionResult` 或 `None`。
3. 用 `@register_doc_extractor` 装饰器注册,声明认领的文件扩展名和优先级。
4. 选择合并策略(`merge_mode` + `suppress_llm`),决定是否让文件继续走默认 markdown 解析和 Tier 2 LLM。

**节点 Schema 要求**(`validate_extraction` 强制):
- 节点必填: `id`(`[a-z0-9_]`)、`label`、`file_type`(6 选 1)、`source_file`
- 边必填: `source`、`target`、`relation`、`confidence`(`EXTRACTED`/`INFERRED`/`AMBIGUOUS`)、`source_file`

**参考实现**: `graphify/extractors/custom/swagger.py`、`graphify/extractors/custom/ddd.py`。

### 5.3 Tier 2 扩展步骤

1. 创建目录 `.graph/extension/prompts/`(若不存在)。
2. 创建 YAML 声明文件,配置 `match.files`(路径 glob 数组)和 `prompt`(自定义指令)。
3. 选择 `mode`(`replace` 推荐 / `merge` 双调用)。
4. 可选:配置 `output_schema` 加严输出校验。

**关键约定**:
- prompt 只写指令部分(system message),文件内容由 graphify 的 `_read_files()` 用 `<untrusted_source>` 块包装后注入。
- 匹配文件组成一个 chunk,一次 LLM 调用。不与默认 prompt 的文件流混合。
- Tier 1 `suppress_llm=True` 是总开关,优先于此处的 mode。
- 执行路径与当前 Tier 2 一致:IDE 会话用 IDE AI 工具执行,headless CLI 用配置的 backend 执行。

### 5.4 两层协同

同一文件可同时被 Tier 1 和 Tier 2 扩展处理:

| Tier 1 状态 | Tier 2 状态 | 结果 |
|---|---|---|
| 解析器 `merge` + `suppress_llm=False` | 匹配 prompt spec | Tier1 结构化锚点 + Tier2 自定义语义,互补 |
| 解析器 `replace` + `suppress_llm=True` | (不进 Tier 2) | 只用 Tier 1 结构化结果,零 LLM 成本 |
| 无 Tier 1 解析器(走默认 markdown) | 匹配 prompt spec | 默认 markdown page/heading + Tier2 自定义语义 |

---

## 6. 代码提交阶段的图谱更新方案

> 关联:`plan_commit.md`(同目录)是提交阶段的能力补齐步骤。

### 6.1 设计原则:文件级增量,不做文件内增量

graphify 的增量模型是**文件级**的:框架告诉处理器"哪些文件变了",处理器对每个文件**全量解析**。不传递 diff 内容,不支持文件内增量解析。

文件级增量(`changed_paths`)+ 内容缓存(content hash)是当前最优方案。

### 6.2 增量信息传递

post-commit hook 取 `git diff --name-only`（只取文件名,不取 diff 内容),传入 `changed_paths: list[Path]`。处理器被调前,`extract()` 先查 content hash 缓存,命中则不调处理器。

### 6.3 各类文件在提交阶段的处理策略

| 文件类型 | Tier1 提取器 | hook 自动? | 处理器被调时做什么 |
|---|---|---|---|
| 代码 (.py/.ts/…) | tree-sitter | ✅ | 全量 AST 重解析 |
| package manifest | extract_package_manifest | ✅ | 全量解析 |
| markdown (.md) | extract_markdown | ⚠️ 有条件 | 全量逐行正则解析 |
| 普通 yaml | 按需扩展(用户编写) | ✅(接入后) | 全量解析 |
| ddd 文档 (.md 白名单) | extract_ddd | ❌(需 code_index) | — |
| paper/image | ❌ | ❌ | — |

### 6.4 markdown 的"有条件"自动处理

- **新 .md(从未跑过 LLM)**: ✅ 自动跑 `extract_markdown`
- **已跑过 Tier2 LLM 的 .md**: ❌ 被 `semantic_doc_set` 排除,避免 AST heading 与 LLM 语义节点重复导致图膨胀

### 6.5 ddd / 外部解析器在提交阶段的限制

ddd 解析器虽纯本地无 LLM,但不在 post-commit hook 里跑,因为 hook 不传 `code_index`,而 ddd 需要 code_index 做锚点匹配。需手动 `graphify extract --update`。

### 6.6 自定义解析器在提交阶段的接入要求

1. 注册到 `_DISPATCH` 表(新扩展名)或通过 `@register_doc_extractor`(.md 等 DOC 扩展名)
2. 不依赖 `code_index`(当前 hook 不传),或接受降级
3. 处理 `semantic_doc_set` 排除(已跑过 Tier2 LLM 的文件 hook 会跳过)

### 6.7 提交阶段 vs 手动更新的职责分工

| 职责 | 提交阶段 (hook 自动) | 手动更新 (graphify extract --update) |
|---|---|---|
| Tier1 代码 AST | ✅ | ✅ |
| Tier1 配置文件(有提取器) | ✅(接入后) | ✅ |
| Tier1 markdown(无语义层) | ✅ | ✅ |
| Tier1 markdown(有语义层) | ❌ 跳过 | ✅ |
| Tier1.5 ddd / 外部解析器(需 code_index) | ❌ | ✅ |
| Tier2 LLM 语义 | ❌ | ✅ |

**设计意图**: hook 保持快速(纯本地,无 LLM,秒级完成),Tier2 语义提取留给手动触发。

---

## 7. 回 upstream 策略

扩展点设计为零侵入,回 upstream 时按需删除:

| 场景 | 操作 |
|---|---|
| 合并 upstream 新代码 | 保留 `registry.py` + `ddd.py` + `extract.py` 注入分支 + `serve.py` tags 拼接 + 自动扫描 + `prompt_registry.py`;合并 upstream 其余改动 |
| upstream 也加了类似机制 | 评估是否弃用自己的 registry,迁移到 upstream 机制 |
| 完全回到原始 graphify | 删 `registry.py`、`ddd.py`、`custom/` 目录、`__init__.py` 扫描逻辑、`extract.py` 注入分支、`serve.py` tags 拼接、`prompt_registry.py`、`prompts/` 目录、测试、fixture |

---

## 8. 验收标准

| ID | 标准 | 验证方式 |
|---|---|---|
| AC1 | Tier 1 `ExtractionResult` dataclass + `register_doc_extractor` + `try_external_extractors` 可用 | 单元测试 |
| AC2 | Tier 1 `extract.py` 主进程注入 + `code_index` + `suppress_llm_files` 透传 | 集成测试 |
| AC3 | Tier 1 `serve.py` tags 检索(条件拼接,无 tags 零干扰) | `test_tags_retrieval_*` |
| AC4 | Tier 1 DDD/Swagger 参考实现 | fixture 测试 |
| AC5 | Tier 1 工具型解析器可声明处理任意扩展名(YAML/JSON/CSV) | 写 YAML 解析器测试 |
| AC6 | Tier 1 内置目录 `graphify/extractors/custom/` 自动扫描 | 放 .py 自动注册 |
| AC7 | Tier 1 项目级目录 `.graph/extension/extractors/` 自动扫描 | 放 .py 自动注册 |
| AC8 | Tier 1 项目级优先级 > 内置(同名 prepend) | 同名解析器项目级赢 |
| AC9 | Tier 1 单个解析器 import 失败不拖垮启动 | 故意写失败解析器,graphify 正常启动 |
| AC10 | Tier 2 `load_all_prompts()` 加载内置 + 项目级,项目级前置 | 放 yaml,加载成功 |
| AC11 | Tier 2 `find_prompt(path, root, specs)` 按 `match.files` glob 路由 | 单元测试 glob 匹配 |
| AC12 | Tier 2 `mode=replace` 时,命中文件用自定义 prompt,未命中用默认 | mock LLM,验证传入 prompt |
| AC13 | Tier 2 `mode=merge` 时,命中文件先跑自定义 prompt 再跑默认 prompt,结果合并 | mock LLM,验证两次调用 + 合并 |
| AC14 | Tier 2 匹配文件组成一个 chunk 一次 LLM 调用,不与默认 prompt 文件流混合 | mock chunk,验证分组 |
| AC15 | Tier 1 `suppress_llm=True` 的文件不进 Tier 2(即使有匹配的 prompt spec) | 集成测试 suppress 优先 |
| AC16 | Tier 2 自定义 prompt 的文件内容仍经 `_read_files()` 的 `<untrusted_source>` 包装 | 验证 user message 含 untrusted_source |
| AC17 | Tier 2 自定义 prompt 前置 `_SECURITY_PREAMBLE` 注入防御指令 | 验证 system message 含 SECURITY 前缀 |
| AC18 | Tier 2 `output_schema` 校验在 `validate_extraction` 之后执行 | 单元测试加严校验 |
| AC19 | Tier 2 缓存按组用各自 prompt 指纹写入,编辑自定义 prompt 失效缓存 | 修改 prompt 后 cache miss |
| AC20 | Tier 2 retry/bisection 路径透传 `system_prompt`,不回退默认 | mock 截断,验证 retry 用自定义 prompt |
| AC21 | Tier 2 `*` glob 不跨 `/`,`**` 跨目录 | 单元测试 glob 语义 |
| AC22 | tags 参与字符串检索 | `graphify query "aggregate_root"` 命中 |
| AC23 | 改动不修改 markdown.py / build.py / dedup.py 既有行为 | git diff 为空 |
