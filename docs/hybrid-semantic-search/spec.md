# Spec: 混合语义检索（语义 + fuzzy 重排）

## 1. 背景与问题

graphify 当前的查询检索是**纯词法匹配**（`serve.py:462-629` `_score_query`）：

- 3 层加权：EXACT (x1000) / PREFIX (x100) / SUBSTRING (x1) + SOURCE-FILE (x0.5)
- IDF 加权 + 覆盖率平方缩放
- **无 stemming、无同义词、无 embedding、无 LLM query rewriting**
- PascalCase 不拆分（`AuthService` 是单 token `authservice`）
- substring 单向（query token 必须是 label 子串）

**召回失败案例**（已取证）：

| NL 问题 | 目标 code 节点 | 失败原因 |
|---|---|---|
| "how does authentication work?" | `class AuthService` | "authentication" 不是 "authservice" 的子串（更长），PascalCase 不拆 |
| "where is the login logic?" | `class AuthService` | "login" 与 "authservice" 零词法重叠 |
| "show me the credential validation" | `verify_password()` | "credential"/"validation" 与 "verify_password" 零重叠 |
| "find the rate limiter" | `class ThrottleService` | "rate"/"limiter" 与 "throttleservice" 零重叠 |

**根因**：整个召回链路的成败系于"词形是否巧合"。BFS 遍历再强大，找不到种子就是空跑。

## 2. 设计目标

| 目标 | 描述 |
|---|---|
| **G1 混合检索** | query 支持"语义检索 + fuzzy 检索"混合重排，返回 top-N |
| **G2 复用 query 接口** | 不新建接口，在现有 `graphify query` / MCP `query_graph` 上增加 `semantic` 参数控制是否开启语义检索 |
| **G3 默认混合** | `semantic` 默认开启（混合模式）；传 `semantic=false` 退回纯词法 |
| **G4 可选降级** | 无 embedding sidecar 时自动降级为纯词法，不报错 |
| **G5 参考 llm-wiki** | 借鉴 pixillab/llm_wiki 的三阶段 pipeline：Phase 1 tokenized → Phase 1.5 vector → Phase 2 graph expansion |
| **G6 与 upstream 解耦** | 语义检索作为独立模块注入，不动 `_score_query` 既有 3 层逻辑，方便回 upstream |

## 3. 参考方案：llm-wiki 的混合检索 pipeline

pixillab/llm_wiki 的 `POST /api/v1/projects/{id}/search` 实现了三阶段混合检索：

### Phase 1: Tokenized Search（与 graphify 当前一致）
- 英文：word splitting + stop word removal
- 中文：CJK bigram token
- 产出 top-K 结果

### Phase 1.5: Vector Semantic Search（可选）
- Embedding via 任意 OpenAI-compatible `/v1/embeddings` endpoint
- 存储在 LanceDB（Rust backend）做 fast ANN retrieval
- Cosine similarity 找语义相关页面，**即使无关键词重叠**
- 结果 merge 到 Phase 1：boost 已有匹配 + 加新发现
- **benchmark：召回率从 58.2% 提升到 71.4%**

### Phase 2: Graph Expansion
- Top search results 作为 seed nodes
- 4-signal relevance model（direct link ×3.0 / source overlap ×4.0 / Adamic-Adar ×1.5 / type affinity ×1.0）
- 2-hop traversal with decay

### graphify 的对应映射

| llm-wiki 阶段 | graphify 对应 | 当前状态 |
|---|---|---|
| Phase 1 tokenized | `_score_query` 3 层词法 | ✅ 已有 |
| Phase 1.5 vector | **新增**：embedding cosine similarity tier | ❌ 缺失（本特性交付） |
| Phase 2 graph expansion | `_pick_seeds` + `_bfs`/`_dfs` | ✅ 已有 |

**本特性的核心交付**：在 graphify 的 `_score_query` 中增加 Phase 1.5 vector tier，作为加法 tier 与既有 3 层词法并列。

## 4. 混合检索架构

### 4.1 三阶段打分公式

```
节点总分 = 词法分（既有 3 层） + 语义分（新增 vector tier） + fuzzy 分（新增 fuzzy tier）

词法分 = Σ [ tier_value × IDF × coverage² ] + Σ [ source_value × IDF ]
    tier_value ∈ {1000(EXACT), 100(PREFIX), 1(SUBSTRING), 0}

语义分 = _VECTOR_SIMILARITY_BONUS × max_cosine_sim(query_embedding, node_embeddings[nid])
    _VECTOR_SIMILARITY_BONUS = 5.0  (介于 SUBSTRING=1 和 PREFIX=100 之间)

fuzzy 分 = _FUZZY_MATCH_BONUS × JaroWinkler(query_token, node_label) × IDF
    _FUZZY_MATCH_BONUS = 2.0  (高于 SUBSTRING=1, 低于 VECTOR=5)
    仅当词法三层都未命中且 JaroWinkler ≥ 0.85 时触发
```

### 4.2 为什么是加法 tier 而非替换

| 方案 | 优点 | 缺点 |
|---|---|---|
| 替换词法为纯语义 | 召回最高 | 精确查询（用户输入精确类名）时排序不如 EXACT |
| **加法 tier（选）** | 精确查询时词法 EXACT 仍主导；模糊查询时语义/fuzzy 补偿 | 分数混合需调参 |
| 纯 fuzzy | 拼写容错 | 无语义理解 |

**加法 tier 的设计**：
- 精确查询 "UserService" → EXACT x1000 主导，语义分 5.0 × 0.9 ≈ 4.5 可忽略
- 模糊查询 "authentication" → 词法 0，语义分 5.0 × 0.85 = 4.25 > 0，节点进入候选
- 拼写错误 "UserServise" → 词法 0，fuzzy 分 2.0 × 0.93 = 1.86 > 0，节点进入候选

### 4.3 触发条件

| Tier | 何时触发 | 条件 |
|---|---|---|
| 词法 3 层 | 始终 | 既有逻辑 |
| 语义 vector tier | `semantic != false` 且 embedding sidecar 存在 | query 被 embed 成功 + 节点 embedding 矩阵加载 |
| fuzzy tier | `semantic != false`（与 semantic 同开关） | rapidfuzz 已是依赖（`pyproject.toml:17`） |

> **fuzzy tier 与 semantic 同开关**：fuzzy 是"轻量语义补偿"（拼写容错 + 词形变体），与 vector 语义检索一起作为"混合模式"的组成部分。`semantic=false` 时退回纯词法。

## 5. Embedding 生成与存储

### 5.1 生成时机：build-time

**决策**：build-time 生成，存为二进制 sidecar。理由：
- 确定性、可复现
- 查询时无需 API key（MCP server 可能没有）
- 与 graphify 既有"code local / docs via LLM"分离一致

### 5.2 Embedding 的文本源：仅 `desc` 字段

**每个节点新增 `desc` 字段**，作为唯一的 embedding 文本源。

```python
def _node_embed_text(node: dict) -> str:
    """唯一向量化文本源。desc 为空时 fallback 到 label。"""
    desc = node.get("desc", "")
    if desc:
        return desc
    return node.get("label", "")
```

**不向量化的字段**（只走词法 tier）：

| 字段 | 不向量化的理由 |
|---|---|
| `norm_label` | 代码节点是 camelCase 符号名（embedding model 不拆词，语义弱）；文档节点是文件名/标题（`README` 语义为零）。有 desc 时不缺这个语义，无 desc 时作为 fallback 已足够 |
| `nid` | 路径派生的 ID（如 `docs_v1_api_readme`），路径片段被当成语义信号是噪声 |
| `source_file` | 文件路径（如 `src/auth/service.py`），目录名巧合会污染 cosine 相似度 |
| `source_tokens` / `nid_folded` | 路径分词 / NFKD 折叠 ID，同上 |

> **设计原则**：路径信息（nid/source_file）完全留给词法 3 层（EXACT/PREFIX/SUBSTRING）匹配；语义匹配只看 `desc`。两条召回链各司其职，互不污染。

### 5.3 节点 `desc` 字段设计

所有节点类型都应携带 `desc` 字段，作为该节点的语义描述：

| 节点类型 | `desc` 来源 | 示例 |
|---|---|---|
| **代码函数/方法节点**（AST） | 函数 docstring（Python）/ JSDoc（JS/TS）/**块注释紧跟函数**（C/Go/Rust 等） | `"Validate user credentials against the stored hash."` |
| **代码类/接口节点**（AST） | 类 docstring / 类上方块注释 | `"Manages authentication sessions and token refresh."` |
| **代码文件节点**（AST） | 模块级 docstring（Python `"""..."""`）/ 文件头注释 | `"Authentication service module."` |
| **文档文件节点**（markdown） | 正文首段（首个非标题、非 frontmatter 的段落） | `"This document describes the login flow..."` |
| **文档标题节点**（markdown） | 该标题下首个段落 | `"## Authentication\n\n Users authenticate via..."` → desc 为首段 |

**提取规则**：

- **代码节点（AST）**：在 `_extract_generic` 的 `walk` 中，当处理 `function_definition` / `class_declaration` 时，检查 body 的第一个子节点；若是 `string` / `comment` / `expression_statement(string)` 则提取为 `desc`。提取逻辑封装为 `_extract_node_desc(node, source, language) -> str`，按语言适配（Python docstring 是 body 首个 expression_statement；C/Go 是函数定义上方的 `comment` 节点；JS/TS 是 JSDoc `comment` 节点）。
- **文档节点（markdown）**：在 `extract_markdown` 中，file 节点的 `desc` 取正文首段；heading 节点的 `desc` 取该标题下首个段落。
- **desc 经过 `sanitize_label` 后存储**（复用既有安全过滤，防止注入）。

**对 DDD doc-anchor 节点**（特性 1 产出）：原计划的 `summary` 字段**改名为 `desc`**，与上述统一。`ddd_type` 保留作为独立字段（不向量化，仅用于过滤）。

### 5.4 存储格式：二进制 sidecar

```
.graph/
├── graph.json                  # 既有
├── embeddings/
│   ├── {model_slug}.npy        # np.ndarray((N, D), dtype=np.float32)
│   ├── {model_slug}.index.json # {"node_ids": [...], "model": "...", "dim": 384}
│   └── {model_slug}.meta.json  # {"generated_at": "...", "node_count": N, "dim": D}
```

- `{model_slug}`：如 `text-embedding-3-small` → `text_embedding_3_small`
- `.npy`：一个 `(N, D) float32` ndarray（10k 节点 × 384 dim = 15 MB）
- `.index.json`：node_id → row index 映射
- 不存入 `graph.json`（避免 JSON 膨胀，384 float JSON 化每节点 ~4KB）

### 5.5 Embedding 后端

| 后端 | 支持 embedding? | 用法 |
|---|---|---|
| OpenAI / OpenAI-compat（openai/gemini/ollama/kimi/deepseek） | ✅ `client.embeddings.create(...)` | 复用既有 `openai` SDK |
| Azure OpenAI | ✅ 同 OpenAI | 复用 `_call_azure` 路径 |
| AWS Bedrock | ✅ Titan embeddings | `bedrock-runtime:InvokeModel` |
| Anthropic Claude | ❌ 无 embedding API | fallback 到 OpenAI 或跳过 |
| Ollama | ✅ `/api/embeddings` | 复用 `OLLAMA_BASE_URL` |

**配置**：新增 env vars
- `GRAPHIFY_EMBED_BACKEND`：`openai` / `gemini` / `ollama` / `kimi` / `deepseek` / `azure` / `bedrock`（默认与 `GRAPHIFY_EXTRACT_BACKEND` 相同）
- `GRAPHIFY_EMBED_MODEL`：如 `text-embedding-3-small`（默认按后端自动选）
- `GRAPHIFY_EMBED_DIM`：维度（默认 384，按模型自动检测）

### 5.6 查询时 embedding

query 字符串在查询时被 embed 一次（一次 API 调用或一次本地前向），缓存于 `G.graph["_query_embedding_cache"]`（LRU，key=query string）。

## 6. 接口变更

### 6.1 CLI `graphify query`

```bash
# 默认混合检索（semantic + fuzzy + 词法）
graphify query "how does login work?"

# 关闭语义检索，纯词法
graphify query "how does login work?" --no-semantic

# 控制返回数量
graphify query "how does login work?" --top-k 5
```

### 6.2 MCP `query_graph` 工具

inputSchema 新增字段：

```json
{
  "question": {"type": "string"},
  "semantic": {"type": "boolean", "default": true,
               "description": "Enable hybrid semantic+fuzzy retrieval (default true). Set false for pure lexical matching."},
  "top_k": {"type": "integer", "default": 3,
            "description": "Number of seed nodes to return before BFS expansion"},
  "top_n": {"type": "integer", "default": 1,
            "description": "Number of independent subgraph results to return (default 1). When >1, each top seed gets its own BFS subgraph; AI picks the most relevant."},
  "mode": {"type": "string", "enum": ["bfs", "dfs"], "default": "bfs"},
  "depth": {"type": "integer", "default": 3},
  "token_budget": {"type": "integer", "default": 2000},
  "context_filter": {"type": "array", "items": {"type": "string"}}
}
```

**`top_n` 多结果返回设计**：

- `top_n=1`（默认）：当前行为不变——取 ranked 列表 top seed → 单次 BFS → 单个子图文本
- `top_n>1`：取 ranked 列表前 `top_n` 个种子，每个种子独立 BFS（各自 `token_budget`），返回 `top_n` 个子图，按种子分数降序排列，用分隔符隔开：

```
=== Result 1/3 (seed: AuthService, score: 4.25) ===
<子图文本>

=== Result 2/3 (seed: ThrottleService, score: 3.10) ===
<子图文本>

=== Result 3/3 (seed: RateLimit, score: 2.80) ===
<子图文本>
```

- AI 拿到多个候选子图后自行判断哪个最相关，或对最相关的做 follow-up 深入
- 每个 `top_n` 子图共享 `token_budget`（总输出按 `token_budget × top_n` 上限控制，避免膨胀）

### 6.3 `_query_graph_text` 签名扩展

```python
def _query_graph_text(
    G: nx.Graph,
    question: str,
    *,
    mode: str = "bfs",
    depth: int = 3,
    token_budget: int = 2000,
    context_filters: list[str] | None = None,
    graph_path: str | None = None,
    semantic: bool = True,      # 新增
    top_k: int = 3,             # 新增：BFS 前选取的种子数
    top_n: int = 1,             # 新增：返回的独立子图结果数
) -> str:
```

### 6.4 `_score_query` 签名扩展

```python
def _score_query(
    G: nx.Graph,
    terms: list[str],
    *,
    collect_per_term_seeds: bool,
    query_embedding: np.ndarray | None = None,  # 新增
    semantic: bool = True,                       # 新增
) -> _QueryScores:
```

## 7. 非目标

- 不替换既有词法 3 层（保留 EXACT/PREFIX/SUBSTRING）
- 不向量化 `norm_label` / `nid` / `source_file` / `source_tokens`（路径信息只走词法 tier）
- 不引入 LanceDB/faiss（10k-100k 节点用 numpy brute-force 足够）
- 不实现 query rewriting / synonym expansion（vector tier 已覆盖同义场景）
- 不修改 `_find_node`/`_find_node_tiers`（explain/path 命令暂不加语义，保持精确匹配语义）
- 不实现本地 sentence-transformers 模型（Phase 1 仅支持 hosted API）
- `top_n` 多结果返回时不做跨结果去重（每个种子独立 BFS，重叠的邻居节点可重复出现——AI 可自行处理）

## 8. 验收标准

| ID | 标准 | 验证方式 |
|---|---|---|
| AC1 | `semantic=true`（默认）时，"login" 能匹配到 `AuthService`（若 embedding 判断语义相关） | `graphify query "login" --top-k 5` 返回 AuthService |
| AC2 | `semantic=false` 时，行为与当前完全一致（纯词法） | `graphify query "login" --no-semantic` 不返回 AuthService（若无词法重叠） |
| AC3 | embedding sidecar 不存在时，自动降级为纯词法，不报错 | 删 `.graph/embeddings/`，`graphify query "login"` 仍工作 |
| AC4 | embedding sidecar 存在时，build-time 生成成功 | `graphify extract . --embed-backend openai` 产出 `embeddings/*.npy` |
| AC5 | 混合模式召回率高于纯词法 | 用 fixture 跑 benchmark：10 个 NL 问题，混合模式召回 ≥ 纯词法 |
| AC6 | 精确查询不受语义干扰 | `graphify query "UserService"` 的 top-1 仍是 `UserService` 节点（EXACT x1000 主导） |
| AC7 | fuzzy tier 容错拼写 | `graphify query "UserServise"`（拼写错）能匹配到 `UserService` |
| AC8 | MCP `query_graph` 的 `semantic` 参数生效 | MCP 调用 `semantic=false` 时返回与纯词法一致 |
| AC9 | 改动不修改 `_score_query` 既有 3 层逻辑 | `git diff` 显示 3 层 if/elif/elif 不变，新增 tier 在外部加法 |
| AC10 | 回 upstream 时，删掉语义模块 + 参数，行为不变 | 删除后 `pytest tests/ -q` 全绿 |
| AC11 | 代码函数节点携带 `desc` 字段（来自 docstring） | 提取带 docstring 的 Python 文件，检查节点 JSON 含 `desc` |
| AC12 | 文档节点携带 `desc` 字段（来自正文首段） | 提取 markdown 文件，检查 file/heading 节点含 `desc` |
| AC13 | `top_n>1` 时返回多个独立子图 | `graphify query "auth" --top-n 3` 返回 3 个用 `=== Result N/3 ===` 分隔的子图 |
| AC14 | `top_n=1`（默认）时返回与当前格式完全一致的单个子图 | `graphify query "auth"` 输出无 `=== Result` 分隔符 |
| AC15 | DDD doc-anchor 节点使用 `desc` 而非 `summary` 字段 | 检查 DDD 节点 JSON：有 `desc` 字段，无 `summary` 字段 |

## 9. 风险

| 风险 | 缓解 |
|---|---|
| Anthropic 无 embedding API（默认 backend 不支持） | `GRAPHIFY_EMBED_BACKEND` 显式指定 OpenAI/Ollama；无配置时降级为纯词法 |
| embedding 生成成本（10k 节点 × API 调用） | batch embed（`_embed_batch` 一次传 100 个文本）；build-time 一次性成本，查询时零成本 |
| numpy brute-force 在 100k+ 节点图上慢 | 10k 节点 = 15MB / sub-ms；100k = 146MB / ~5ms；>500k 才需 faiss（Phase 2） |
| 混合分数调参困难（vector bonus vs 词法 bonus） | `_VECTOR_SIMILARITY_BONUS=5.0` 介于 SUBSTRING(1) 和 PREFIX(100) 之间，保证精确查询词法主导；用 benchmark fixture 调参 |
| query embedding 增加查询延迟 | LRU 缓存 query embedding（同 query 不重复 embed）；仅当词法弱结果时才触发 vector tier（可选优化） |
| `_extract_generic` 是 40+ 语言共用引擎，加 desc 提取影响面大 | desc 提取逻辑封装为 `_extract_node_desc()` 按语言分派；只处理有明确 docstring 模式的语言（Python/JS/TS/C/Go/Rust/Java/C#/Swift），其余语言 desc 留空（fallback 到 label） |
| docstring 过长导致 embedding 噪声/超 token 限制 | `desc` 截断到 512 字符（embedding model 通常 512 token 上下文，desc 作为节点级摘要不应过长）；超长时取首段 |
