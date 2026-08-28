# Embedding 配置指南

hybrid 语义检索的 vector tier 需要一个 embedding 模型。本文档说明如何配置 embedding 后端。

## 三种部署模式

| 模式 | 适用场景 | 是否跨进程 | 是否需要 API key | 数据是否出机器 |
|---|---|---|---|---|
| **跨进程：Ollama** | 本地开发 / 离线 / 隐私敏感 | ✅（HTTP 服务） | ❌（本地） | ❌ |
| **跨进程：OpenAI 兼容端点** | 自托管 vLLM/LM Studio/llama.cpp | ✅（HTTP 服务） | 可选 | ❌ |
| **跨进程：云端 API** | 生产环境 | ✅（HTTPS） | ✅ | ✅ |
| **同进程：sentence-transformers** | 测试 / CI | ❌（进程内） | ❌ | ❌ |

> **Ollama 本质上也是"远端方案"**——它启动一个 HTTP 服务，graphify 通过 OpenAI SDK 调 `localhost:11434/v1/embeddings`。和调 OpenAI 云端 API 走同一段代码，只是 `base_url` 不同。
>
> **真正的"本地方案"只有 sentence-transformers**——PyTorch 进程内直接推理，无 HTTP，无服务进程。但模型文件较大（120MB+），不作为默认方案，仅用于测试/CI。

---

## 配置方式（配置文件，无需改代码）

### 唯一方式：配置文件 `.graph/graphifyrc`

在项目的 graph 输出目录（默认 `.graph/`，和 graph.json 同目录）创建 `graphifyrc` 文件：

```ini
# <project>/.graph/graphifyrc
# embedding 后端配置 (无需环境变量, 无需改代码)
embed_backend=openai-compatible
embed_base_url=http://my-embedding-server:8080/v1
embed_api_key=sk-your-key-here
embed_model=text-embedding-3-small
```

支持的 4 个 key：

| Key | 说明 | 示例 |
|---|---|---|
| `embed_backend` | 后端类型（见下表） | `openai-compatible` |
| `embed_base_url` | OpenAI 兼容端点 URL | `http://localhost:8080/v1` |
| `embed_api_key` | API key（本地服务填任意非空值） | `sk-...` |
| `embed_model` | 模型名（不填用后端默认） | `text-embedding-3-small` |

> **两层配置 merge**：`graphify/.default-graphifyrc`（包内出厂默认，全注释占位）+ `.graph/graphifyrc`（项目级覆盖）。项目级覆盖 default 的对应 key，未覆盖的 fallback 到 default。你可以在 default 里 uncomment 配置让 graphify 开箱即用。
>
> 环境变量（`GRAPHIFY_EMBED_BACKEND` 等）已废弃，不再支持。全部用配置文件。

### CLI flag（可选覆盖）

```bash
graphify extract . --embed-backend openai-compatible --embed-model text-embedding-3-small
```

> **优先级**：CLI flag > `.graph/graphifyrc` 配置文件 > `graphify/.default-graphifyrc`（出厂默认）。

---

## 支持的后端

| Backend | 调用方式 | 需要 `embed_base_url` | 需要 `embed_api_key` | 默认模型 |
|---|---|---|---|---|
| `openai-compatible` | HTTPS/HTTP → 任意 OpenAI 兼容端点 | ✅ 必填 | ✅ 必填 | `default`（需填 `embed_model`） |
| `openai` | HTTPS → api.openai.com | 可选（默认 OpenAI 官方） | ✅ 必填 | `text-embedding-3-small` |
| `ollama` | HTTP → localhost:11434 | 可选（默认本地） | 可选（填任意值） | `nomic-embed-text` |
| `gemini` | HTTPS → Google AI | 可选 | ✅ 必填 | `text-embedding-004` |
| `kimi` | HTTPS → Moonshot | 可选 | ✅ 必填 | `embedding-2` |
| `deepseek` | HTTPS → DeepSeek | 可选 | ✅ 必填 | `deepseek-embed` |
| `azure` | HTTPS → Azure OpenAI | ✅ 必填 | ✅ 必填 | `text-embedding-3-small` |
| `sentence-transformers` | 进程内 PyTorch CPU | ❌ | ❌ | `paraphrase-multilingual-MiniLM-L12-v2` |

> **Anthropic Claude 没有 embedding API**——如果默认 backend 是 claude，必须显式配置其他 backend，否则 query 时自动降级为纯词法。

### `openai-compatible` backend（推荐用于自托管端点）

适用于任何实现了 `/v1/embeddings` 的服务：vLLM、LM Studio、llama.cpp、OpenRouter、自建网关等。

`.graph/graphifyrc` 示例：

```ini
# <project>/.graph/graphifyrc
embed_backend=openai-compatible
embed_base_url=http://my-server:8080/v1
embed_api_key=local-no-key-needed
embed_model=BAAI/bge-m3
```

---

## 初始化行为

**`graphify .` / `graphify extract .` 默认会尝试生成 embedding**——无需传 `--embed-backend`，配置文件是唯一开关：

- **配置了 backend**（`.default-graphifyrc` 或 `.graph/graphifyrc`）→ build 完成后自动生成 sidecar，查询时启用 vector tier
- **未配置任何 backend** → 静默跳过 embedding 生成，不报错，graph 正常产出；查询时 `HybridScorer.available=False`，自动退回纯词法

embedding 与 graph 提取/构建是同一次 `graphify .` 调用的两个阶段：先提取图谱，再（如果配置了 backend）生成 embedding sidecar。`--embed-backend` / `--embed-model` 仍是 CLI 覆盖参数，但不再是触发开关——触发完全由配置文件决定。

---

## build-time 生成 sidecar

```bash
# 配置了 .graph/graphifyrc 后, 直接 graphify . 即可生成
graphify .

# 或用 CLI flag 临时覆盖配置 (不是触发开关, 只是覆盖)
graphify extract . --embed-backend openai-compatible --embed-model text-embedding-3-small
```

生成产物：

```
.graph/embeddings/
├── <model_slug>.npy           # numpy 二进制矩阵 (N, D) float32
├── <model_slug>.index.json    # node_id -> row 映射
└── <model_slug>.meta.json     # 模型/维度/生成时间
```

**可以提交到代码仓**——和 `graph.json` 一样是确定性产物（同模型 + 同输入产出相同向量）。

---

## query-time 自动加载

查询时无需显式指定 backend——`HybridScorer` 会：
1. 读取 `.graph/graphifyrc` 配置文件确定 backend
2. 加载 `.graph/embeddings/` 下最新的 sidecar
3. embed query 字符串，算 cosine similarity
4. 作为 additive bonus 加到词法分数上

```bash
# 生成 sidecar 后, 查询自动启用 vector tier
graphify query "how does login work?"

# 关闭 vector tier (纯词法对照)
graphify query "how does login work?" --no-semantic
```

---

## sentence-transformers（仅测试/CI）

纯本地 CPU 推理，无需服务进程，无需 API key。**不作为正式方案**，仅用于测试和 CI。

默认模型 `paraphrase-multilingual-MiniLM-L12-v2`（384 维，120MB，支持 50+ 语言含中英跨语言检索）。

在 `.graph/graphifyrc` 中配置：

```ini
embed_backend=sentence-transformers
embed_model=paraphrase-multilingual-MiniLM-L12-v2
```

然后直接 `graphify .` 即可生成 sidecar（无需 `--embed-backend` flag，无需环境变量）：

```bash
pip install sentence-transformers
graphify .

# 查询
graphify query "how does login work?"
```

CPU 性能（4 核）：81 节点编码 279ms，单 query 10ms。中英跨语言准确率 100%（7/7 测试对）。

---

## 持久化文件

所有 backend 产出的 sidecar 格式相同：

```
.graph/embeddings/
├── <model_slug>.npy           # numpy 二进制矩阵 (N, D) float32
├── <model_slug>.index.json    # node_id -> row index 映射
└── <model_slug>.meta.json     # 生成时间 / 维度 / 模型名 / backend
```

**可以提交到代码仓**——和 `graph.json` 一样是确定性产物。benchmark fixture 已提交：`tests/fixtures/search_benchmark/embeddings/`。

---

## 降级行为

- 无 sidecar 文件 → `HybridScorer.available=False`，query 自动退回纯词法（不报错）
- 有 sidecar 但无 backend 配置 → 同上，退回纯词法
- embedding API 调用失败 → build 时打 warning（不阻断 graph 生成），query 时退回纯词法

---

## 配置文件速查

| Key (in `.graph/graphifyrc`) | 用途 | 默认值 |
|---|---|---|
| `embed_backend` | embedding 后端类型 | 无（未配置则跳过 embedding） |
| `embed_base_url` | endpoint URL（openai-compatible 必填，其他可选覆盖） | 按 backend 默认 |
| `embed_api_key` | API key（本地服务填任意非空值） | 无 |
| `embed_model` | embedding 模型名 | 按 backend 默认 |

> 环境变量（`GRAPHIFY_EMBED_BACKEND` 等）已废弃，不再支持。全部用 `.graph/graphifyrc` 配置文件。

---

## 已验证的端到端结果

用 `tests/e2e/resources/user-management` 真实项目（81 节点，TS 代码）+ `sentence-transformers` 本地模型验证：

| 查询 | 纯词法 | hybrid (vector+fuzzy) | 说明 |
|---|---|---|---|
| `login` | `.login()` | `.login()` | 都命中 |
| `how does authentication work` | **No match** | `AuthenticatedRequest`, `.login()`, `AuthController`, `.handleLogin()`, `AuthMiddleware` | vector 救回 5 个节点 |
| `AuthService` | `AuthService` | `AuthService` | 精确查询不受干扰 |

benchmark fixture（10 节点小图）：hybrid recall@5 = **100%** (10/10) vs pure lexical **40%** (4/10)。

手动验证步骤见 `tests/docs/embedding-manual-test.md`。
