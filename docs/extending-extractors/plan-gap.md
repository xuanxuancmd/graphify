# Plan: 解析器扩展机制能力补齐

> 关联:`spec.md`(同目录)是扩展机制的完整规格。本文是**当前实现 vs 规格之间的差异清单**,每个 Gap 是一个可独立执行、可验证的原子改动。
>
> `plan.md`(同目录)是 Tier 1 差异修复步骤(Gap-1/2/3),本文在此基础上补齐 Gap-4~7。

---

## 现状总览

| Gap | 层 | 一句话 | 涉及文件 | 状态 |
|---|---|---|---|---|
| Gap-1 | Tier 1 | 扫描范围硬编码,只认 `.md/.mdx/.qmd/.skill` | `extract.py` | ✅ 已实现 |
| Gap-2 | Tier 1 | 无自动扫描目录,注册靠手动 import | `extractors/__init__.py` | ✅ 已实现 |
| Gap-3 | Tier 1 | 无项目级目录,解析器和内置混排 | `extractors/custom/` 目录结构 | ✅ 已实现 |
| Gap-4 | Tier 2 | 无 prompt registry,全局单一通用 prompt | 新建 `prompt_registry.py` + 改 `llm.py`/`cli.py`/`validate.py` | ✅ 已实现 |
| Gap-5 | Tier 1 | 两阶段提取(代码+配置混合→文档),应改三阶段 | `cli.py` | ✅ 已实现 |
| Gap-6 | Tier 1 | DDD 代码锚点匹配不支持全限定名/多匹配/置信度 | `extractors/custom/ddd.py` | ✅ 已实现 |
| Gap-7 | Tier 1 | URL 锚点匹配失效,endpoint_index 几乎为空 | `extractors/custom/ddd.py` + `swagger.py` | ✅ 已实现 |

**全部 7 个 Gap 已实现。**

**依赖关系**: Gap-1/2/3 互相独立;Gap-4 独立;Gap-5 依赖 Gap-1(需先支持任意扩展名才能三阶段分流);Gap-6/7 独立。

**建议顺序**: Gap-2 → Gap-3 → Gap-1 → Gap-5 → Gap-4 → Gap-6 → Gap-7

---

## Gap-1: 解除 Tier 1 扫描范围硬编码

**目标**: `try_external_extractors` 对任意扩展名的文件都被调用,不止 `.md/.mdx/.qmd/.skill`。

**现状**:
- `extract.py` 的 external extractor pre-pass 用 `_DOC_EXTS = {".md", ".mdx", ".qmd", ".skill"}` 限定扫描范围
- 仅这些扩展名的文件会进入 `try_external_extractors`,YAML/JSON/CSV 等被跳过
- swagger 解析器认领 `.yaml/.yml`,但因硬编码扫描范围,改 `.yaml` 文件不会被 pre-pass 捕获(只在 `extensions` 声明 + `_rebuild_code` 里被 `external_extractor_extensions()` 拉入,但 `extract()` 主流程仍受 `_DOC_EXTS` 限制)

**步骤**:
1. `extract.py` external extractor pre-pass:移除 `_DOC_EXTS` 过滤,对所有文件调 `try_external_extractors`
2. `merge_mode="merge"` 分支:非 doc 扩展名时 `extract_markdown` 不适用,merge 退化为 replace(外部结果 only)——当前已有此退化逻辑,确认覆盖
3. 更新 `external_extractor_extensions()` 的调用方,确保 `_rebuild_code`(watch.py)仍正确拉入声明的扩展名
4. 测试:注册一个认领 `.csv` 的解析器,放一个 `.csv` fixture,验证被 pre-pass 捕获

**验收**:
- AC5: 工具型解析器可声明处理任意扩展名(YAML/JSON/CSV)
- `.csv` fixture 被自定义解析器处理,`graph.json` 含对应节点

---

## Gap-2: 内置目录自动扫描

**目标**: `graphify/extractors/custom/` 下的 `.py` 文件自动导入并注册,无需手动在 `__init__.py` 加 import 行。

**现状**:
- 注册靠 `extractors/__init__.py:18` 手动 `from graphify.extractors import ddd` 触发 `@register_doc_extractor`
- 新增解析器需改 graphify 源码,项目级解析器无法独立维护
- 单个解析器 import 失败会拖垮启动

**步骤**:
1. `extractors/__init__.py`:用 `pkgutil.iter_modules` 扫描 `custom/` 目录,逐个 `importlib.import_module`
2. 每个 import 用 `try/except`,失败时 `logging.warning` 不中断启动
3. `custom/` 下每个 `.py` 文件用 `@register_doc_extractor` 自注册,扫描后自动生效
4. 测试:在 `custom/` 放一个故意写错 import 的解析器,验证 graphify 正常启动 + warning 输出

**验收**:
- AC6: 内置目录 `graphify/extractors/custom/` 自动扫描
- AC9: 单个解析器 import 失败不拖垮启动

---

## Gap-3: 项目级目录 + 优先级

**目标**: 支持 `.graph/extension/extractors/` 项目级目录,项目级解析器优先于内置同名解析器。

**现状**:
- 解析器和内置语言解析器混在 `graphify/extractors/` 同一目录,合并 upstream 时 diff 不干净
- `register_doc_extractor` 已支持 `priority="prepend"`(项目级)和 `priority="append"`(内置),但无项目级目录扫描

**步骤**:
1. `extractors/__init__.py` 扫描 `custom/` 后,再扫描 `.graph/extension/extractors/`(若存在)
2. 项目级目录的解析器用 `priority="prepend"` 注册,确保优先于内置
3. 同名解析器:项目级赢(prepend 插入注册表头部,`try_external_extractors` 按顺序第一个匹配的赢)
4. 测试:在内置 `custom/` 和项目级 `.graph/extension/extractors/` 各放同名解析器,验证项目级优先

**验收**:
- AC7: 项目级目录 `.graph/extension/extractors/` 自动扫描
- AC8: 项目级优先级 > 内置(同名 prepend)

---

## Gap-4: Tier 2 prompt registry

**状态**: ✅ 已实现

**目标**: 支持 `.graph/extension/prompts/*.yaml` 声明式自定义 LLM prompt,按 `match.files` glob 路由,匹配文件组成一个 chunk。

**现状**:
- `llm.py` 的 `_EXTRACTION_SYSTEM` 是全局单一通用 prompt,不区分文件类型
- 所有 doc/paper/image 走同一个 prompt
- `extract_files_direct()` 无 `system_prompt` 参数,无法传入自定义 prompt
- `cli.py` 对所有 `semantic_files` 用统一 prompt,无分组 chunking

**步骤**:

### 4.1 新建 `graphify/prompt_registry.py`(~120 LOC)

```python
@dataclass
class PromptSpec:
    name: str
    description: str
    match: dict                    # {"files": ["glob1", "glob2", ...]}
    mode: str = "replace"           # "replace" | "merge"
    prompt: str                    # system prompt 指令部分
    output_schema: dict | None = None
```

函数:
- `load_prompts_from_dir(prompt_dir: Path) -> list[PromptSpec]`:扫描 `.graph/extension/prompts/*.yaml`
- `find_prompt(path: Path, root: Path) -> PromptSpec | None`:按 `match.files` glob 匹配(Python `fnmatch` 或 `pathlib.PurePath.match`),第一个匹配的赢
- `group_by_prompt(files: list[Path], root: Path) -> dict[PromptSpec | None, list[Path]]`:把 semantic_files 按 prompt 分组

### 4.2 改 `graphify/llm.py` `extract_files_direct()`(~15 LOC)

新增参数 `system_prompt: str | None = None`:
- `None`:用 `_extraction_system(deep=deep_mode)`(现有逻辑不变)
- 非 None:替换 system message,文件内容仍由 `_read_files()` 生成 user message(含 `<untrusted_source>` 包装)

改动点:`_call_claude` / `_call_claude_cli` / `_call_openai_compat` / `_call_azure` / `_call_bedrock` 的 system message 来源从硬编码 `_extraction_system(deep=...)` 改为参数传入。

### 4.3 改 `graphify/cli.py` semantic extraction 分组(~40 LOC)

当前(`cli.py:3918-3919`):
```python
from graphify.llm import _extraction_system as _sem_prompt_for
sem_prompt = _sem_prompt_for(deep=deep_mode)
```

改为:
```python
from graphify.prompt_registry import load_prompts_from_dir, group_by_prompt

specs = load_prompts_from_dir(Path.cwd() / ".graph" / "extension" / "prompts")
groups = group_by_prompt(semantic_files, root)

for spec, files in groups.items():
    if spec is None:
        # 默认组:原有 _chunk_within_caps + _EXTRACTION_SYSTEM
        for chunk in _chunk_within_caps(files):
            extract_files_direct(chunk, system_prompt=None, ...)
    else:
        # 自定义组:匹配文件组成一个 chunk
        if spec.mode == "merge":
            custom_result = extract_files_direct(files, system_prompt=spec.prompt, ...)
            default_result = extract_files_direct(files, system_prompt=None, ...)
            # 合并(走 graphify 原生去重)
        else:  # replace
            extract_files_direct(files, system_prompt=spec.prompt, ...)
```

### 4.4 扩展 `graphify/validate.py`(~30 LOC)

新增 `validate_prompt_schema(data: dict, spec: PromptSpec) -> list[str]`:
- 在 `validate_extraction(data)` 之后执行
- 按 `spec.output_schema` 的 `valid_file_types` / `valid_relations` 做额外枚举校验
- `spec.output_schema` 为 None 时跳过(空列表 = 通过)

### 4.5 测试

- 单元:`load_prompts_from_dir` 加载 yaml;`find_prompt` glob 匹配;`group_by_prompt` 分组
- 集成:mock LLM,验证 mode=replace 传入自定义 prompt;mode=merge 两次调用;suppress_llm 优先于 mode
- 安全:验证 user message 含 `<untrusted_source>` 包装

**验收**:
- AC10: `load_prompts_from_dir()` 加载 `.graph/extension/prompts/*.yaml`
- AC11: `find_prompt(path, root)` 按 `match.files` glob 路由
- AC12: `mode=replace` 时命中文件用自定义 prompt,未命中用默认
- AC13: `mode=merge` 时命中文件先跑自定义再跑默认,结果合并
- AC14: 匹配文件组成一个 chunk,不与默认 prompt 文件流混合
- AC15: Tier 1 `suppress_llm=True` 的文件不进 Tier 2
- AC16: 自定义 prompt 的文件内容仍经 `<untrusted_source>` 包装
- AC17: `output_schema` 校验在 `validate_extraction` 之后执行

---

## Gap-5: 三阶段提取顺序

**目标**: 当前两阶段(代码+配置混合→文档)改为三阶段(代码→配置文件→文档),确保文档解析器能引用到配置文件产出的节点(如 swagger endpoint)。

**现状**:
- `cli.py` 两阶段:阶段 1 提取所有 code 文件(AST),阶段 2 提取所有 doc 文件(传 `code_index`)
- 配置文件(YAML/JSON)在阶段 1 和 code 混在一起提取,但配置文件解析器(如 swagger)产出的节点需要在阶段 2 供 ddd 解析器做锚点匹配
- `extract.py` 已有 `_ordered_indices` 排序(配置文件在 doc 之前),但只在单次 `extract()` 调用内生效,跨阶段不保证

**步骤**:
1. `cli.py` 阶段 1 拆分为 1a(代码 AST)和 1b(配置文件),1b 在 1a 完成后跑,产出 code + config 节点
2. 阶段 2 提取 doc 文件时,`code_index` 包含 1a + 1b 的全部节点
3. 测试:swagger `.yaml` 和 ddd `contracts.md` 在同一目录,验证 ddd 能匹配到 swagger 产出的 endpoint 节点

**依赖**: Gap-1(需先支持配置文件扩展名进入 `try_external_extractors`)

**验收**:
- swagger endpoint 节点在 ddd 解析器运行前已产出
- ddd `contracts.md` 的 `<anchor:code>` 能匹配到 swagger endpoint

---

## Gap-6: DDD 代码锚点匹配增强

**目标**: 支持全限定名匹配、多匹配结果(非只取第一个)、置信度标注。

**现状**:
- `ddd.py` `_build_code_indices` 只按简单 name 索引,不支持 `module.Class.method` 全限定名
- 匹配到多个候选时只取第一个,丢失其他合理匹配
- 无置信度标注(所有 matches 都是 `EXTRACTED`,无 `INFERRED` 区分)

**步骤**:
1. `_build_code_indices`:增加全限定名索引(`source_file:Class.method` → node)
2. `_match_controller` / `_match_handler`:返回所有匹配结果(非只取第一个),按匹配精确度排序
3. 每个匹配标注置信度:精确全限定名 = `EXTRACTED`(1.0);类名模糊匹配 = `INFERRED`(0.5-0.8)
4. 测试:构造 `OrderService` 和 `PaymentService`,验证 `OrderService.create` 匹配到精确方法

**验收**:
- 全限定名 `module.Class.method` 匹配成功
- 多匹配时全部产出边(不同置信度)
- 精确匹配标注 `EXTRACTED`,模糊匹配标注 `INFERRED`

---

## Gap-7: URL 锚点匹配修复

**目标**: `POST:/path` 格式的代码锚点能匹配到 swagger 产出的 endpoint 节点。

**现状**:
- `ddd.py` `_build_code_indices` 构建 `endpointIndex`,但 endpoint 节点由 swagger 解析器产出
- swagger 和 ddd 在不同阶段/不同 `extract()` 调用中运行,endpoint 节点可能不在 ddd 的 `code_index` 里
- 路径未规范化(`/api/users` vs `api/users` vs `/api/users/`),匹配失败

**步骤**:
1. 路径规范化:`_normalize_endpoint_path(path)` 去除重复 `/`、统一前导 `/`、去除尾部 `/`
2. swagger 产出的 endpoint 节点 `id` 和 ddd 的 `endpointIndex` key 用同一规范化函数
3. 确保 Gap-5(三阶段)落实后,swagger endpoint 节点在 ddd 运行前已入 `code_index`
4. 测试:swagger 定义 `POST /api/users`,ddd `contracts.md` 锚点 `POST:/api/users`,验证匹配成功

**依赖**: Gap-5(swagger endpoint 需在 ddd 之前产出)

**验收**:
- `POST:/api/users` 匹配到 swagger endpoint 节点
- 路径变体(`/api/users`、`api/users`、`/api/users/`)都能匹配
- endpoint_index 非空

---

## 实施优先级

| 优先级 | Gap | 理由 | 状态 |
|---|---|---|---|
| P0 | Gap-2 | 自动扫描是其他扩展的基础,且最简单 | ✅ 已实现 |
| P0 | Gap-3 | 项目级目录,让用户不改 graphify 源码就能加解析器 | ✅ 已实现 |
| P1 | Gap-1 | 解除扫描范围限制,配合 Gap-2/3 让任意扩展名可用 | ✅ 已实现 |
| P1 | Gap-4 | Tier 2 prompt registry,本轮设计的核心交付物 | ✅ 已实现 |
| P2 | Gap-5 | 三阶段提取,改善 swagger→ddd 节点传递 | ✅ 已实现 |
| P2 | Gap-6 | DDD 锚点匹配精度提升 | ✅ 已实现 |
| P2 | Gap-7 | URL 锚点匹配修复,依赖 Gap-5 | ✅ 已实现 |
