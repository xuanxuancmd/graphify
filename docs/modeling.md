# graphify 数据建模

graphify 把一个项目（代码、文档、DDD 文档、配置文件 YAML/JSON、包清单、PDF、图片）建模成一张可遍历的知识图谱。本文只描述**建模方式**:节点和边的 schema、每种文件类型如何建模、字段含义,以及哪些字段参与默认语义检索或 fuzzy 字符串检索。

> 运行流程（安装、命令、平台集成）见 [README.md](../README.md),整体管线说明见 [how-it-works.md](how-it-works.md),模块职责见 [ARCHITECTURE.md](../ARCHITECTURE.md)。

---

## 1. 节点模型

### 1.1 通用字段

每个节点至少包含以下字段（`validate.py:4-6` 校验必填项）:

| 字段 | 类型 | 必填 | 含义 | 来源 |
|---|---|---|---|---|
| `id` | str | ✅ | 稳定标识符,`[a-z0-9_]+`,格式 `{stem}_{entity}`,stem = 完整 repo-relative 路径去扩展名 | `extractors/base.py:54` `_make_id` |
| `label` | str | ✅ | 人类可读名称 | 各 extractor |
| `file_type` | str | ✅ | 封闭枚举 6 值之一(见 §1.2) | `validate.py:4` |
| `source_file` | str | ✅ | 来源文件路径(build 时规范化为 repo-relative) | 各 extractor |

可选字段（由不同抽取器按需填充）:

| 字段 | 类型 | 含义 | 来源 | 参与检索? |
|---|---|---|---|---|
| `source_location` | str\|null | 行号 `L<line>`(AST 必填,LLM 可为 null) | 各 extractor | ❌ |
| `node_kind` | str | 节点细分类型(见 §1.3) | markdown.py, ddd.py | ❌ |
| `norm_label` | str | 归一化 label(去变音符号 + lower) | build/export 阶段生成 `export.py:338` | ✅ 语义检索主字段 |
| `tags` | list[str] | 通用标签列表 | ddd.py:376 | ✅ 条件拼接 |
| `desc` | str | 描述文本(首段段落,上限 512 字符) | markdown.py:357, ddd.py:373 | ✅ embedding 文本源 |
| `concept_id` | str | DDD doc-anchor 的概念 ID(原始未归一化) | ddd.py:374 | ❌ |
| `frontmatter` | dict | markdown YAML frontmatter | markdown.py:394 | ❌ |
| `source_url` | str | 远程来源 URL(论文/视频) | llm.py | ❌ |
| `captured_at` | str | 抓取时间 | llm.py | ❌ |
| `author` / `contributor` | str | 作者信息 | llm.py / `add` 命令 | ❌ |
| `rationale` | str | WHY/NOTE/HACK 设计理由(作为节点属性,非独立节点) | llm.py:483 | ❌ |
| `_origin` | str | 内部标记 `"ast"` / `"semantic"`,ghost-merge 用 | build.py:48 | ❌ 内部字段 |
| `_callable` / `_callable_class` | bool | TS/JS 代码节点的可调用标记(代替 node_kind) | engine.py | ❌ 内部字段 |

### 1.2 `file_type` 封闭枚举（6 值）

定义于 `validate.py:4`,校验于 `validate.py:48-51`。**任何越界值在 build 时被改写为 `"concept"`**(`build.py:856-857`):

| 值 | 含义 | 典型来源 |
|---|---|---|
| `code` | AST 提取的代码符号(file/function/class/method) + 包清单节点 | 各语言 extractor;`manifest_ingest.py:75` |
| `document` | markdown page/heading 节点 + LLM 文档节点 | `markdown.py:344`;`llm.py:504` |
| `paper` | PDF/论文 LLM 语义提取 | `llm.py:504` |
| `image` | 图片 LLM 语义提取(vision) | `llm.py:504` |
| `rationale` | WHY 决策/设计意图(兼容旧图;当前 prompt 改为节点属性) | `extraction-spec.md:19` |
| `concept` | 兜底类型:跨文件可合并的通用概念、JSON config ref、DDD doc-anchor、LLM 语义概念、无效 file_type 归一化目标 | ddd.py:369;`json_config.py:175,198`;`build.py:857` |

**同义词归一化** (`build.py:88-102` `_FILE_TYPE_SYNONYMS`):`markdown/text→document`、`tool/library→code`、`pattern/principle/constraint/tech/technology/data-source/framework/gotcha→concept`。

### 1.3 `node_kind` 常见值

`node_kind` 存在是因为 `file_type` 是封闭枚举,无法承载 page/heading/doc-anchor 等细分(`markdown.py:289-299`):

| 值 | 来源 | 说明 |
|---|---|---|
| `page` | `markdown.py:393` | markdown 文件节点 |
| `heading` | `markdown.py:345,475` | markdown 标题节点 (# ~ ######) |
| `doc-anchor` | `ddd.py:372` | DDD 文档锚点节点 |
| `rest_endpoint` | `swagger.py` | swagger/openapi 端点节点(label 为 `METHOD:/full/path`) |
| `swagger_doc` | `swagger.py` | swagger 规范文件节点 |
| `file` | (推断) | 代码文件节点(AST extractor 不显式设置,通过 `label==basename(source_file)` 推断,`ddd.py:113`) |
| `class` | (部分语言) | 类声明(部分 AST extractor 设置;TS/JS 用 `_callable_class` 标记代替) |
| `function` / `method_definition` / `function_definition` | (部分语言) | 函数/方法声明(同上,TS/JS 用 `_callable` 标记代替) |

> **关键**: TS/JS AST extractor **不设置** `node_kind`,改用 `_callable`/`_callable_class` 标记 (`ddd.py:84-91,98-103`)。

### 1.4 节点 ID 规约

节点 ID 是图谱一致性的命脉:三个独立生产者(AST extractor、LLM 语义子代理、build 组装器)必须对同一实体产出**相同** ID,否则产生断连的"幽灵"节点 (`ids.py:4-9`)。

规约配方 (`ids.py:50-83`):

```
原始串
  → casefold + NFKC 迭代到不动点(两者不可交换,单遍不够)
  → [^\w]+ 替换为单个 _(re.UNICODE,保留 CJK/西里尔/阿拉伯字母)
  → 折叠连续 _
  → strip 首尾 _
```

`make_id(*parts)` 把各部分用 `_` 拼接后过 `normalize_id`。关键性质:**幂等**、**大小写稳定**。

| 节点类型 | ID 公式 | 例子 |
|---|---|---|
| 代码文件 | `make_id(str(path))` | `docs/v1/api/README.md → docs_v1_api_readme` |
| 代码符号 | `make_id(stem, namespace, entity)` | `src/auth/session.py` 的 `login` → `src_auth_session_login` |
| markdown 文件 | `make_id(str(path))` | `docs/readme.md → docs_readme` |
| markdown 标题 | `make_id(stem, title)` 重名时追加行号 | `make_id(stem, title, str(line_num))` |
| DDD doc-anchor | `make_id("docanchor", stem, concept_id)` | `docanchor_docs_order_domain_model_AG-01` |
| swagger 端点 | `make_id("swagger_ep", stem, method小写, norm_full_path)` | `GET /rest/users/{id}` → `swagger_ep_user_api_get_rest_users_id`(花括号剥除,`/`→`_`,变量名保留) |
| swagger 文档 | `make_id("swagger_doc", stem)` | `swagger_doc_user_api` |
| 包清单 | `make_id("pkg", name)` | `pkg_requests`(按包名 canonical,跨清单去重) |
| JSON config ref | `make_id("ref", val_text)` | `ref_./tsconfig_base.json` |
| LLM 语义节点 | `{stem}_{entity}` | prompt 规约,`llm.py:493-494` |

**stem** = 完整仓库相对路径去扩展名 (`base.py:58-81`)。**用全路径而非仅父目录**,避免不同目录下同名文件坍缩成一个"最后写入者胜"节点。

---

## 2. 边模型

### 2.1 通用字段

`validate.py:7` 校验必填项:

| 字段 | 类型 | 必填 | 含义 | 来源 |
|---|---|---|---|---|
| `source` | str | ✅ | 起点 ID(ACTOR,施动者) | `validate.py:7` |
| `target` | str | ✅ | 终点 ID(ACTED-UPON,受动者) | `validate.py:7` |
| `relation` | str | ✅ | 关系类型(见 §2.2) | `validate.py:7` |
| `confidence` | str | ✅ | `EXTRACTED`/`INFERRED`/`AMBIGUOUS` 三值之一 | `validate.py:5,7` |
| `source_file` | str | ✅ | 关系被发现所在的文件 | `validate.py:7` |
| `confidence_score` | float | LLM 必填 | 置信度分数(见 §2.3) | `llm.py:504`;`extraction-spec.md:47-59` |
| `source_location` | str\|null | 否 | 行号 `L<line>` | 各 extractor |
| `weight` | float | 否 | 边权重(默认 1.0;DDD 默认 0.5) | `json_config.py:106`;`ddd.py:383` |
| `context` | str | 否 | 上下文标注(如 `"import"`/`"dependency"`/`"mixin"`) | `json_config.py:108`;`manifest_ingest.py:103` |
| `target_file` | str | 否 | 文档链接边的解析目标(build 前弹出) | `markdown.py:374-375` |

**边方向规则** (`llm.py:496-499`): `source` 永远是 ACTOR,`target` 是 ACTED-UPON:
- `calls`: source=调用者,target=被调用者
- `imports`/`references`: source=导入/引用方,target=被导入/被引用方
- `implements`/`inherits`: source=子类/实现者,target=基类/接口

### 2.2 `relation` 封闭集合值

关系词汇按抽取来源分四套:

**AST 代码边** (`extract.py:266-269` `SEMANTIC_RELATIONS`):

| 关系 | 语义 | 典型来源 |
|---|---|---|
| `calls` | 函数调用 | call-graph 第二趟 |
| `imports` / `imports_from` / `re_exports` | 模块导入/符号导入/再导出 | import handler |
| `contains` | file→symbol、parent symbol→child symbol | `engine.py:3156` |
| `method` | 类→其方法 | `engine.py:4053` |
| `inherits` | 类继承 | `engine.py:3179` |
| `implements` | 接口实现 | `engine.py:3352` |
| `mixes_in` | mixin/trait/use/prepend(Ruby/PHP/Scala) | `engine.py` |
| `embeds` | 嵌套类型引用 | `engine.py` |
| `references` | 类型引用、属性访问、泛型参数 | `engine.py:3232` |

**LLM 语义边** (`llm.py:504`):

| 关系 | 语义 |
|---|---|
| `calls` | 调用(跨代码与文档引用时) |
| `implements` | 实现 |
| `references` | 引用 |
| `cites` | 引用(论文/ADR/RFC 之间) |
| `conceptually_related_to` | 概念相关 |
| `shares_data_with` | 共享数据结构 |
| `semantically_similar_to` | 语义相似 |

**配置/清单特有边**:

| 关系 | 语义 | 来源 |
|---|---|---|
| `extends` | 配置继承(tsconfig/eslint extends) | `json_config.py:176,187`;`apex.py:132`;`dart.py:396` |
| `depends_on` | 包依赖 | `manifest_ingest.py:103` |
| `dispatches_to` | C# 接口方法调度 | `csharp_dispatch.py:31` |

**Swagger 文档边** (`swagger.py`):

| 关系 | 语义 | 来源 |
|---|---|---|
| `contains` | swagger_doc → rest_endpoint | `swagger.py` |
| `defined_in` | rest_endpoint → swagger_doc(contains 的反向,供 path 查询) | `swagger.py` |
| `references` | rest_endpoint → 控制器类(tags[0] 匹配)/处理函数(operationId 匹配代码索引) | `swagger.py` |

**DDD 边** (`ddd.py:787-792`,pending 内部类型→最终 relation 映射):

| DDD 内部类型 | 映射到 relation | 语义 |
|---|---|---|
| `describes` | `references` | doc-anchor 描述代码符号 |
| `related` | `conceptually_related_to` | doc↔doc 概念关联 |
| `categorized_under` | `conceptually_related_to` | doc→doc 归属 |
| `cites` | `cites` | doc→doc 引用 |

**通用/弱关系** (`build.py:63` `_GENERIC_RELATIONS`,合并时被具体关系覆盖):`references`、`uses`、`mentions`

**超边 relation** (`llm.py:504`):`participate_in`、`implement`、`form`

### 2.3 `confidence` 三值枚举

定义于 `validate.py:5`,校验于 `validate.py:68-72`:

| 值 | 含义 | confidence_score | 来源 |
|---|---|---|---|
| `EXTRACTED` | 关系在源中显式存在(import 语句、直接调用、引用、链接) | **1.0**(恒定) | `llm.py:480`;`extraction-spec.md:48` |
| `INFERRED` | 合理推断(call-graph 第二趟、共享数据结构、隐含依赖) | 离散取值:`0.95`(直接结构证据)/ `0.85`(强推断)/ `0.75`(合理)/ `0.65`(弱)/ `0.55`(推测) | `llm.py:481`;`extraction-spec.md:49-54` |
| `AMBIGUOUS` | 不确定,标记待审,不可省略 | `0.1-0.3` | `llm.py:482`;`extraction-spec.md:59` |

> **关键**: `confidence_score` 在每条 LLM 边上是**必填**的,禁止用 0.5 作默认值 — INFERRED 若无合适值应标 AMBIGUOUS。AST 跨文件解析的 INFERRED 边用 0.85 (`symbol_resolution.py:370`)。

---

## 3. 各文件类型的建模方式

### 3.1 code 文件（.py / .ts / .go / .rs / .java / ...）

**提取方式**: tree-sitter AST,本地确定性,无 LLM。

**产出节点** (`engine.py:2995-3035`):

| 节点 | node_kind / 标记 | file_type | 说明 |
|---|---|---|---|
| 文件节点 | (推断,不显式设置) | `code` | `id=_make_id(str(path))`,`label=path.name`,`source_location="L1"` |
| 类/接口/结构体 | `class`(部分语言)或 `_callable_class`(TS/JS) | `code` | 可带 `is_partial`/`is_nested_type` 元数据 |
| 函数/方法 | `function`/`method_definition`(部分语言)或 `_callable`(TS/JS) | `code` | 标签按 `function_label_parens` 决定是否加 `()` |
| 命名空间/模块 | (设 `type` 字段为 `namespace`/`module`) | `code` | `engine.py:3088` |
| 存根(stub) | — | `code` | 跨文件引用的基类/类型在当前文件未定义时产出,`source_file=""`,留给语料级解析坍缩 |

**产出边**: `calls`、`imports`/`imports_from`/`re_exports`、`contains`、`method`、`inherits`、`implements`、`mixes_in`、`embeds`、`references`、`extends`(Apex/Dart)

所有 AST 节点打 `_origin="ast"` 标记 (`build.py:1013`),作为 ghost-merge 的权威信号。

### 3.2 配置 JSON（package.json / tsconfig.json / composer.json / ...）

**文件**: `extractors/json_config.py`

**识别** (`json_config.py:10-49`):文件名命中白名单(`package.json`/`tsconfig.json`/`jsconfig.json`/`composer.json`/`deno.json`/`bower.json`/`manifest.json`/`app.json`/`now.json`/`vercel.json`/`angular.json`/`nest-cli.json`/`biome.json`/`renovate.json`/`.babelrc`/`.eslintrc.json`/`.prettierrc.json`/`babel.config.json` 等),或顶层 key 命中(`dependencies`/`devDependencies`/`peerDependencies`/`extends`/`$ref`/`$schema`/`compilerOptions`)。数据 JSON(fixtures/datasets/GeoJSON/API dumps)被跳过。

**产出节点**:

| 节点 | id | file_type | 说明 |
|---|---|---|---|
| file 节点 | `_make_id(str(path))` | `code` | `label=path.name` |
| key 节点 | `_make_id(stem, [parent_key], key)` | `code` | 每个 JSON pair 产出一个,递归 object(深度≤6,pair数≤500) |
| ref 节点(外部引用) | `_make_id("ref", val_text)` | `concept` | `extends`/`$ref`/依赖包名,命名空间避免与 code 节点 ID 撞 |

**产出边**: `contains`(file→key、parent key→child key)、`extends`(file/key→ref)、`references`(parent→ref,$ref 引用)、`imports`(dep_key→ref,dependencies block)

所有边 `confidence="EXTRACTED"`,`weight=1.0`,`context="import"`。文件大小上限 1 MiB。

### 3.3 包清单（pyproject.toml / Cargo.toml / go.mod / pom.xml / apm.yml）

**文件**: `manifest_ingest.py`

**识别** (`manifest_ingest.py:28-35`):按文件名命中 → `apm.yml/apm.yaml→"apm"`、`pyproject.toml→"python"`、`cargo.toml→"cargo"`、`go.mod→"go"`、`pom.xml→"maven"`。

**产出节点** (`manifest_ingest.py:72-83`):

| 节点 | id | file_type | 说明 |
|---|---|---|---|
| canonical package 节点 | `_make_id("pkg", name)` | `code` | **按包名去重**,跨清单共享(一个 `requests` 包在 10 个 pyproject.toml 出现只产 1 个节点)。带 `type="package"`、`ecosystem=<eco>`、可选 `version` |

**产出边**: `depends_on`(pkg→dep_pkg,`context="dependency"`,`confidence="EXTRACTED"`,`confidence_score=1.0`,`weight=1.0`)

> 依赖包自身清单不在语料中时,边变成 dangling 被 build 剪除,**故意不**产出 stub 节点(避免空 source_file 覆盖真实节点)。

### 3.4 markdown 文档（.md / .mdx / .qmd / .rst / .txt）

**文件**: `extractors/markdown.py`

**提取方式**: 纯逐行解析,无 tree-sitter 依赖。

**产出节点**:

| 节点 | node_kind | file_type | 说明 |
|---|---|---|---|
| 文件节点 | `page` | `document` | `id=_make_id(str(path))`,携带 `frontmatter`(解析后的 YAML)、`desc`(首段段落,上限 512 字符) |
| 标题节点 | `heading` | `document` | `id=_make_id(stem, title)` 重名时追加行号,`desc`=标题后首段 |

**产出边**: `contains`(file→heading、parent heading→child heading 按层级嵌套)、`references`(file→target_doc,解析 `[text](./other.md)`、`[label]: ./other.md`、`[[wikilink]]`)

所有边 `confidence="EXTRACTED"`,`weight=1.0`。

**链接解析** (`markdown.py:185-236`):剥离 `#anchor`/`?query`,跳过外部 URL/mailto/纯锚点/非文档扩展名。Wikilink 支持 vault 回退(目标不存在时全局按 basename 查找)。

### 3.5 YAML 文件（.yaml / .yml）

**无专用 AST 提取器**。走 LLM 语义提取(extraction-spec.md 通用 prompt),产出 `concept`/`rationale`/`document` 节点 + `conceptually_related_to`/`semantically_similar_to`/`references`/`cites` 等语义边。

**例外**:
- swagger / openapi 规范 yaml 走 `extractors/custom/swagger.py` 确定性解析(见 §3.5b),不走 LLM
- `apm.yml`/`apm.yaml` 走 `manifest_ingest.py` 确定性解析(见 §3.3)
- markdown 中的 YAML frontmatter 由 `markdown.py:100-140` 解析到 page 节点的 `frontmatter` 字段

### 3.5b swagger / openapi 规范 YAML

**文件**: `extractors/custom/swagger.py`

**识别** (`_is_swagger_spec`):`swagger: "2.0"` / `openapi: "3.x"` key 存在,或 `paths` 下有 `/` 前缀 key 含 HTTP method 子键(宽松匹配)。非 swagger yaml(docker-compose/CI/k8s)返回 None,回退默认文档提取。

**提取方式**: 纯确定性 yaml 解析(safe_load 取数据 + compose 取行号),`suppress_llm=True`(Tier 1,零 LLM 成本),`merge_mode="replace"`(结构化数据,默认 markdown 只加噪声)。

**产出节点** (全通用字段,无 swagger 专属字段):

| 节点 | node_kind | file_type | 说明 |
|---|---|---|---|
| 文档节点 | `swagger_doc` | `document` | 每个规范文件一个,`label=文件名`,`tags=["swagger"]` |
| 端点节点 | `rest_endpoint` | `concept` | 每个 `paths.<path>.<method>` 一个,形态如下 |

端点节点形态:

```python
{
    "id": "swagger_ep_<stem>_<method>_<norm_path>",   # 花括号剥除, / → _, 变量名保留进 ID
    "label": "GET:/rest/users/{id}",                  # METHOD:/full/path, 路径变量与 yaml 原文一致
    "file_type": "concept",
    "source_file": "docs/user-api.yaml",
    "source_location": "L118",
    "node_kind": "rest_endpoint",
    "desc": "description + x-examples",               # 不含 summary(与 description 冗余)
    "tags": ["url"],
}
```

**URL 的唯一载体是 label**: method 与路径从 label 可完整恢复(首个 `:` 前是 method);控制器/处理函数关联由 `references` 边承载;请求/响应结构细节留在 yaml 原文,经 `source_file` + `source_location` 可回溯。`tags=["url"]` 参与词法检索,使 "url" 类查询能命中端点节点(§4.1)。

**desc 是语义检索唯一入口** (`embeddings.py:_node_embed_text`): 端点的业务语言(description + 示例报文)经 embedding 服务于中文/自然语言查询("用户注册怎么做");label 的 token(get/rest/users)服务于词法查询。

**DDD URL 锚点匹配** (`ddd.py:_build_code_indices`): DDD 文档 `<anchor:code>` 列的 `HTTP方法:/路径` 锚点(如 `GET:/rest/users/{id}`)按端点 **label** 派生的键匹配——method+path 主键(method 精确核对,锚点方法与端点不符时降级 AMBIGUOUS)+ 裸路径键 + 路径变量归一化变体(`{id}`/`{userId}` 互匹配)。

**产出边**: `contains`(doc→endpoint)、`defined_in`(endpoint→doc,反向)、`references`(endpoint→控制器类 via `tags[0]`、→处理函数 via `operationId`;Java 代码生成项目有 `Impl` 后缀回退)。未匹配的 tags/operationId 记入 `unmatched`,不产影子节点。

### 3.6 DDD 文档（context-map / technical-constraints / business-flow / invariants / contracts / domain-events / domain-model）

**文件**: `extractors/ddd.py`(从 `parse-ddd-tables.mjs` 逐行移植)

**识别** (`ddd.py` `extract_ddd`):**文件名精确匹配白名单**——`path.name.lower()` 必须等于 `f"{kw}.md"`(关键词 + `.md`);目录名不参与匹配,`api/contracts/` 下的文件不会因路径含 `contracts` 被误吸入。

**产出节点** (`ddd.py:356-377` `_make_node`):doc-anchor 节点,全通用字段(无 `ddd_*` 前缀):

```python
{
    "id": "docanchor_{stem}_{concept_id}",   # _make_id 生成, 符合 [a-z0-9_]
    "label": "业务术语名称",                    # 查询主匹配字段
    "file_type": "concept",                   # 复用既有枚举, 不新增
    "source_file": "docs/.../domain-model.md",
    "source_location": "L42",
    "node_kind": "doc-anchor",               # 与 page/heading 并列
    "desc": "概念描述",
    "concept_id": "AG-01",                   # 原始未归一化, 跨文件边解析用
    "tags": ["ddd", "aggregate_root", "domain-model"],  # 编码 DDD 类型
}
```

**ddd_type 推断** (`ddd.py:321-344`):从表格 `<anchor:xxx>` 列名推断,取值 `aggregate_root`/`domain_event`/`invariant`/`bounded_context`/`value_object`/`domain_service`/`contract`/`business_flow_step`/`glossary_term`/`tech_constraint`/`concept`。

**产出边** (`ddd.py:380-391` `_make_edge`):`references`(describes→references,doc→code)、`conceptually_related_to`(related/categorized_under,doc↔doc)、`cites`(doc→doc)。默认 `confidence="EXTRACTED"`,`confidence_score=1.0`,`weight=0.5`。

**解析模式** (`ddd.py:833-885`):
- `context-map.md` → BC 节点 + related 边 + glossary 节点
- `technical-constraints.md` → `### TC-xxx:` 标题 + `**代码锚点**`/`**适用范围**` 段落前缀
- 其他 5 类 → 带 `<anchor:ddd>` 标签的表格解析

**合并策略**: `merge_mode="merge"` — DDD 节点与默认 markdown page/heading 节点合并互补,LLM Tier 2 仍跑通用 prompt。

### 3.7 PDF / 图片

走 LLM 语义提取。PDF 经 `pypdf` 提取文本层 (`llm.py:531-534`) 后送 LLM;图片以 `<untrusted_source>` 块或视觉附件形式送入。产出 `paper`/`image`/`concept` 节点 + 语义边。

---

## 4. 检索机制

### 4.1 检索文本拼接（`_node_search_text`）

**位置**: `serve.py:328-370`

检索时把每个节点的以下字段拼接成一段文本(用 `\x00` NUL 分隔,防止跨字段 trigram),构建 trigram 索引作为候选节点生成器:

| 顺序 | 字段 | 计算方式 | 喂给哪个检索路径 | 永远拼接? |
|---|---|---|---|---|
| 1 | `norm_label` | `norm_label or _strip_diacritics(label).lower()` | `_score_nodes` substring tier;`_find_node` exact/prefix/substring tier | ✅ |
| 2 | `label_tokens` | `" ".join(_search_tokens(label))`(标点拆成空格) | `_find_node` 的 `term in label_tokens` 分支(跨标点匹配 "foo bar" vs "foo.bar") | ✅ |
| 3 | `nid` | `str(nid).lower()` | `_find_node` 的 `joined == nid_lower` tier | ✅ |
| 4 | `source_file` | `(source_file or "").lower()` | `_score_nodes` 的 `t in source` source-match tier | ✅ |
| 5 | `source_tokens` | `" ".join(_search_tokens(source_file))` | `_find_node` 的 `term == source_tokens` source_exact tier(路径精确匹配) | ✅ |
| 6 | `nid_folded` | `_strip_diacritics(nid).lower()` | `_find_node` 的 `norm_query == nid_norm` tier(Hangul 等 NFKD 分解) | ⚠️ 条件:仅当 nid 非 ASCII 且 fold 后不同时追加 |

> **关键设计**: `tags` 字段**不进搜索文本** — tags 是 graph.html 过滤面板的人面元数据,不是内容(见 `tags.py` 治理);query 语义与 tags 完全解耦。`nid_folded` 是唯一**条件拼接**字段。

### 4.2 字符串检索打分层级（`_score_query` / `_find_node`）

**位置**: `serve.py:476` `_score_query`、`serve.py:1426` `_find_node_tiers`、`serve.py:1504` `_find_node`

**打分层级常量** (`serve.py:290-293`):

| Tier | 常量 | 值 | 触发条件 | 匹配字段 |
|---|---|---|---|---|
| EXACT | `_EXACT_MATCH_BONUS` | 1000.0 | `t == norm_label` 或 `t == bare_label` | `norm_label` |
| PREFIX | `_PREFIX_MATCH_BONUS` | 100.0 | `norm_label.startswith(t)` 或 `bare_label.startswith(t)` | `norm_label` |
| SUBSTRING | `_SUBSTRING_MATCH_BONUS` | 1.0 | `t in norm_label` | `norm_label` |
| SOURCE | `_SOURCE_MATCH_BONUS` | 0.5 | `t in source` | `source_file` |
| FUZZY | `_FUZZY_MATCH_BONUS × sim` | 2.0 × sim | **仅当 EXACT/PREFIX/SUBSTRING 三层全 miss**时触发,JaroWinkler ≥0.85 | `label` |
| VECTOR | `_VECTOR_SIMILARITY_BONUS × sim` | 5.0 × sim | cosine 相似度(post-loop merge pass,trigram 排除的节点也能命中) | `desc` 的 embedding |

**IDF 加权** (`serve.py:296-318`): 每个 tier 值 × `idf[t] = log(1 + N/(1+df[t]))`,稀有标识符得高分,通用词得低分。

**三 tier 互斥** (`serve.py:604-612`): 每个 term 取最强 tier(exact > prefix > substring),不重复计分;substring 和 source 是累加的。

**Coverage 缩放** (`serve.py:665`): per-term exact/prefix tier 之和 × `(matched/n_terms)**2`,防止单个通用词的 exact 匹配淹没多词匹配。

**`_find_node` 返回 4 个 tier** (`serve.py:1487-1501`),按优先级:

| 优先级 | Tier | 匹配条件 |
|---|---|---|
| 1 | `source_exact` | `term == source_tokens`(tokenized source_file 路径精确匹配) |
| 2 | `exact` | `term == norm_label/bare_label/label_tokens/nid_lower` 或 `norm_query == norm_label/bare_label/nid_norm` |
| 3 | `prefix` | `norm_label/bare_label/label_tokens/nid_lower.startswith(term)` |
| 4 | `substring` | `term in norm_label` 或 `term in label_tokens` 或 `norm_query in norm_label` |

> **`_find_node` 是纯 lexical**(exact/prefix/substring/source_exact),fuzzy 和 vector 只在 `_score_query` 中。

### 4.3 fuzzy 检索（hybrid_scorer.py + fuzzy.py）

**位置**: `hybrid_scorer.py`(154 行)、`fuzzy.py`

**设计**: 作为 `_score_query` 的**加法 bonus**,不替换 lexical 三层。精确查询仍 EXACT 主导,模糊/语义查询从 0 分被救回。

**两个 tier**:

| Tier | 算法 | 阈值 | bonus 公式 | 匹配字段 |
|---|---|---|---|---|
| FUZZY | JaroWinkler 相似度 | ≥0.85 (`fuzzy.py:18,32-33`) | `2.0 × sim` | `label`(case-insensitive) |
| VECTOR | cosine 相似度 | (无阈值, post-loop merge) | `5.0 × sim` | `desc` 的 embedding |

**触发条件** (`serve.py:622-632`): FUZZY tier 仅在该 token 在该节点上 EXACT/PREFIX/SUBSTRING 三层全 miss 时触发,精确匹配永不被打扰。

**可用性** (`hybrid_scorer.py:97-104`): `available` 当且仅当 embedding sidecar 已加载**且**配置了 embedding backend(`GRAPHIFY_EMBED_BACKEND` 或 extraction 同款 env key)。不可用时 `_score_query` 跑纯 lexical 模式。

---

## 5. 去重和合并

### 5.1 ghost-merge（build.py）

**位置**: `build.py:979-1069`

**去重 key**: `(source_file, label)` 二元组 (`build.py:1023,1046`)

**机制**:
1. **Pass 1**: 收集 canonical 节点。`_origin=="ast"` 的节点优先(覆盖已有非 AST 条目)。两个 AST 节点同 key → 记入 `_loc_collisions`(歧义,不合并)
2. **Pass 2**: 找 ghost — 非 AST 节点中,其 `(source_file, label)` key 在 canonical 中存在且 canonical 不是自己的
3. **合并**: `_ghost_remap[ghost_id] = ast_id`,移除 ghost 节点,边通过 `norm_to_id` 重定向

### 5.2 deduplicate_entities（dedup.py）

**位置**: `dedup.py:503-856`

**三阶段 pipeline**:

| Pass | 机制 | key | 范围 |
|---|---|---|---|
| Pass 0 | 精确 ID 去重 | `id` | 全部节点,survivor 由 `_collision_rank` 全序决定 |
| Pass 1 | 精确归一化 | `_norm(label)`(NFKC + casefold + 非 alphanumeric 折叠为空格) | 同文件同 norm label → 合并;跨文件同 norm label → 仅 `file_type=="concept"` 且 entropy ≥2.5 时合并;**code 节点完全跳过** |
| Pass 2 | MinHash/LSH + Jaro-Winkler | label 相似度 | 仅高 entropy 节点(≥2.5);MinHash LSH 阻塞(阈值 0.7,128 perm);Jaro-Winkler 验证(阈值 92.0);同 community 加分 5.0;**code 节点完全跳过** |

**阻断规则**: 短 label 变体、prefix-extension(`getActiveSession` vs `getActiveSessions`)、数字 token 不同、模板兄弟、跨文件 `rationale`/`document` 不合并。

### 5.3 _doc_twin_remap（build.py）

**位置**: `build.py:766-795`

**目的**: markdown 快速扫描产出 bare id `_make_id(path)` 的 doc 节点,LLM 语义 pass 产出 `<slug>_doc` 的 doc 节点,同一文件分裂成两个断连节点。合并到语义 `_doc` 节点(它带更丰富的 references/hyperedges)。

**合并条件**:
1. 语义节点 id 以 `_doc` 结尾
2. bare 节点 `by_id[nid[:-4]]` 存在
3. **两端 `source_file` 相同**
4. **两端 `file_type == "document"`**(防止 code 符号 `foo` 和 `foo_doc` 误合并)

---

## 6. 检索字段速查

| 检索方式 | 匹配的字段 | 算法 | 阈值/打分 | 来源 |
|---|---|---|---|---|
| 默认语义检索(exact) | `norm_label` | 精确相等 | 1000.0 × idf | `serve.py:290` |
| 默认语义检索(prefix) | `norm_label` | 前缀匹配 | 100.0 × idf | `serve.py:291` |
| 默认语义检索(substring) | `norm_label` | 子串包含 | 1.0 × idf | `serve.py:292` |
| 默认语义检索(source) | `source_file` | 子串包含 | 0.5 × idf | `serve.py:293` |
| fuzzy 字符串检索 | `label` | JaroWinkler | ≥0.85,bonus = 2.0 × sim | `fuzzy.py:18`;`hybrid_scorer.py:138-146` |
| vector 语义检索 | `desc` 的 embedding | cosine 相似度 | bonus = 5.0 × sim | `hybrid_scorer.py:106-136` |
| 路径精确检索 | `source_file` tokenized | 精确 token 匹配 | source_exact tier(最高优先级) | `serve.py:1487` |
| ID 检索 | `id` lower | 精确/前缀/子串 | exact/prefix/substring tier | `serve.py:1488-1500` |
