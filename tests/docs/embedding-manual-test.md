# Embedding 手动验证流程

本文档记录 hybrid semantic search 的 embedding 端到端手动验证流程，可完整复现。
验证用真实项目 `tests/e2e/resources/user-management`（12 个 TypeScript 文件，81 节点）。

## 前置说明：四种 embedding backend

验证前需明确四种 backend 的区别——本流程用的是 **sentence-transformers**（纯本地 CPU，无需服务进程）：

| Backend | 运行方式 | 需要服务进程 | 需要 API key | 适用场景 |
|---|---|---|---|---|
| `sentence-transformers` | PyTorch 进程内 CPU 推理 | ❌ | ❌ | **测试 / CI**（本文档用此方式） |
| `ollama` | HTTP 调用 localhost:11434 | ✅ `ollama serve` | ❌ | 本地开发 / 离线 / 隐私敏感 |
| `openai-compatible` | HTTP 调任意 OpenAI 兼容端点 | ✅ 自托管服务 | 可选 | 自托管 vLLM/LM Studio/llama.cpp |
| `openai` / `gemini` / `kimi` / `azure` | HTTPS 调云 API | ❌ | ✅ | 生产环境 |

> **Ollama 和 openai-compatible 都是跨进程方案**——通过 OpenAI SDK 调 HTTP 端点，只是 `base_url` 不同。Ollama 是本地部署的 HTTP 服务，openai-compatible 适用于任何 `/v1/embeddings` 端点（含云端和自托管）。
>
> **sentence-transformers 是唯一的同进程方案**——PyTorch 进程内直接推理，无 HTTP，无服务进程。专为测试/CI 加的免费本地方案，不作为正式方案（模型文件 120MB）。

### 配置方式（三选一，无需改代码）

| 方式 | 位置 | 说明 |
|---|---|---|
| **配置文件**（推荐） | `.graph/graphifyrc` | 和 graph.json 同目录，4 个 key：`embed_backend` / `embed_base_url` / `embed_api_key` / `embed_model` |
| 环境变量 | `GRAPHIFY_EMBED_BACKEND` 等 | 适用于 CI / 临时覆盖 |
| CLI flag | `--embed-backend` | 仅 build-time（`graphify extract`） |

> **两层配置 merge**：`graphify/.default-graphifyrc`（包内出厂默认，全注释占位）+ `.graph/graphifyrc`（项目级覆盖）。项目级覆盖 default 的对应 key，未覆盖的 fallback 到 default。
>
> 本文档验证用环境变量（最简单），实际项目推荐用 `.graph/graphifyrc` 配置文件。

---

## 步骤 1：环境准备

### 1.1 确认 Python 版本

```powershell
python --version
```

**预期输出**：
```
Python 3.13.0
```

### 1.2 安装依赖

```powershell
pip install sentence-transformers
```

> 首次安装会带入 PyTorch（CPU 版）、transformers、tokenizers 等，约 500MB。
> 如果机器上有 CUDA GPU，PyTorch 会自动用 GPU；CPU 也能跑（`all-MiniLM-L6-v2` 仅 80MB，CPU 推理 <100ms/查询）。

### 1.3 确认 graphify 核心依赖

```powershell
python -c "import sentence_transformers, torch, networkx, rapidfuzz; print('OK')"
```

**预期输出**：
```
OK
```

### 1.4 确认运行在 CPU 模式（可选，用于验证无 GPU 也能跑）

```powershell
python -c "import torch; print('PyTorch:', torch.__version__, 'CUDA:', torch.cuda.is_available())"
```

**预期输出**：
```
PyTorch: 2.13.0+cpu CUDA: False
```

> `CUDA: False` 说明纯 CPU 推理。CPU 跑 `all-MiniLM-L6-v2` 完全够用。

---

## 步骤 2：确认真实项目存在

### 2.1 检查 fixture 项目

```powershell
Get-ChildItem "tests\e2e\resources\user-management\src" -Recurse -File -Filter "*.ts" | Measure-Object | Select-Object Count
```

**预期输出**：
```
Count
-----
  12
```

### 2.2 查看项目结构（可选）

```powershell
Get-ChildItem "tests\e2e\resources\user-management\src" -Recurse -File -Filter "*.ts" | ForEach-Object { $_.FullName.Replace((Get-Location).Path + "\", "") }
```

**预期输出**（12 个 TS 文件）：
```
tests/e2e/resources/user-management/src/auth/auth.controller.ts
tests/e2e/resources/user-management/src/auth/auth.service.ts
tests/e2e/resources/user-management/src/auth/jwt.ts
tests/e2e/resources/user-management/src/auth/password.ts
tests/e2e/resources/user-management/src/config.ts
tests/e2e/resources/user-management/src/index.ts
tests/e2e/resources/user-management/src/middleware/auth.middleware.ts
tests/e2e/resources/user-management/src/middleware/request-logger.ts
tests/e2e/resources/user-management/src/models/user.ts
tests/e2e/resources/user-management/src/repositories/user.repository.ts
tests/e2e/resources/user-management/src/services/user.service.ts
tests/e2e/resources/user-management/src/utils/logger.ts
```

> 这些 TS 文件带 JSDoc 注释（如 `/** Register a new user — ... */`），用于验证 desc 字段提取。

---

## 步骤 3：重新 build graph（验证 desc 提取）

### 3.1 设置环境变量

```powershell
$env:PYTHONPATH = "."
$env:PYTHONIOENCODING = "utf-8"
```

### 3.2 运行 extract（强制重建）

```powershell
python -m graphify extract tests/e2e/resources/user-management/src --no-cluster --no-viz --code-only --force
```

**预期输出**（关键行）：
```
[graphify extract] --force --code-only: full AST re-scan, existing semantic layer preserved
[graphify extract] found 12 code, 0 docs, 0 papers, 0 images
[graphify extract] AST extraction on 12 code files...
[graphify extract] wrote ...\src\.graph\graph.json — 81 nodes, 204 edges (no clustering)
```

> `--force` 强制全量重建（否则增量扫描会跳过未改动文件）。
> `--code-only` 只跑 AST，不调 LLM（无需 API key）。
> `--no-cluster` 跳过社区检测（验证 desc 不需要）。

### 3.3 验证 graph.json 节点携带 desc 字段

创建临时脚本 `_check_desc.py`：

```python
import json
from pathlib import Path

g = Path("tests/e2e/resources/user-management/src/.graph/graph.json")
data = json.loads(g.read_text(encoding="utf-8"))
nodes = data.get("nodes", [])
with_desc = [n for n in nodes if n.get("desc")]
print(f"graph.json: {len(nodes)} 节点, {len(with_desc)} 带 desc ({len(with_desc)*100//max(len(nodes),1)}%)")
print()
print("前 8 个带 desc 的节点:")
for n in with_desc[:8]:
    print(f"  {n['label']:35s} desc={n['desc'][:70]!r}")
```

运行：

```powershell
python _check_desc.py
```

**预期输出**：
```
graph.json: 81 节点, 30 带 desc (37%)

前 8 个带 desc 的节点:
  .handleRequest()                    desc='Handle incoming HTTP requests — routes to the appropriate handler.'
  .handleRegister()                   desc='POST /auth/register — register a new user account.'
  .handleLogin()                      desc='POST /auth/login — authenticate and receive a JWT token.'
  .handleRefresh()                    desc='POST /auth/refresh — refresh an expired JWT token.'
  .register()                         desc='Register a new user — creates the user account and returns auth token.'
  .login()                            desc='Login — verifies credentials and returns auth token. User must be acti'
  .refreshToken()                     desc='Refresh an expired token — issues a new token from a valid-but-expired'
  .generateToken()                    desc='Generate a JWT token for a user. The token encodes userId, email, and '
```

> **验证点**：TS 方法的 JSDoc 注释被正确提取为 `desc` 字段。
> 30/81 节点带 desc（都是方法节点，class/file 节点因 TS JSDoc 提取限制暂未覆盖——这是已知限制，不影响 vector tier 验证：无 desc 的节点 fallback 到 label）。

---

## 步骤 4：生成 embedding sidecar

### 4.1 设置 backend 环境变量

```powershell
$env:GRAPHIFY_EMBED_BACKEND = "sentence-transformers"
```

### 4.2 生成 sidecar

创建脚本 `_gen_embeddings.py`：

```python
import sys
sys.path.insert(0, ".")
from pathlib import Path
from graphify.embeddings import generate_embeddings_for_graph

GRAPH = Path("tests/e2e/resources/user-management/src/.graph/graph.json")
print(f"输入: {GRAPH}")
print("生成 embedding sidecar (sentence-transformers + all-MiniLM-L6-v2)...")

npy_path = generate_embeddings_for_graph(
    GRAPH, backend="sentence-transformers", model="all-MiniLM-L6-v2"
)
print(f"输出: {npy_path}")

# 验证 sidecar 文件
emb_dir = GRAPH.parent / "embeddings"
for f in sorted(emb_dir.glob("all_minilm_l6_v2.*")):
    size = f.stat().st_size
    print(f"  {f.name:35s} {size:>8} bytes")

import json
idx = json.loads((emb_dir / "all_minilm_l6_v2.index.json").read_text(encoding="utf-8"))
print(f"index.json: {len(idx['node_ids'])} node_ids, dim={idx['dim']}, model={idx['model']}")
```

运行：

```powershell
python _gen_embeddings.py
```

**预期输出**：
```
输入: tests\e2e\resources\user-management\src\.graph\graph.json
生成 embedding sidecar (sentence-transformers + all-MiniLM-L6-v2)...
输出: tests\e2e\resources\user-management\src\.graph\embeddings\all_minilm_l6_v2.npy

  all_minilm_l6_v2.index.json             2993 bytes
  all_minilm_l6_v2.meta.json               147 bytes
  all_minilm_l6_v2.npy                  124544 bytes
index.json: 81 node_ids, dim=384, model=all-MiniLM-L6-v2
```

> **验证点**：
> - `.npy` 文件 124KB（81 节点 × 384 维 × 4 字节 = 124,416 字节，符合预期）
> - `.index.json` 含 81 个 node_id 到 row index 的映射
> - 模型维度 384（`all-MiniLM-L6-v2` 的标准维度）
> - 首次运行会从 HuggingFace Hub 下载 ~80MB 模型到 `~/.cache/huggingface/`，后续从缓存读

### 4.3 确认 sidecar 文件结构

```powershell
Get-ChildItem "tests\e2e\resources\user-management\src\.graph\embeddings" -Name
```

**预期输出**：
```
all_minilm_l6_v2.index.json
all_minilm_l6_v2.meta.json
all_minilm_l6_v2.npy
```

---

## 步骤 5：端到端查询验证（AC1 + AC2 + AC6）

这是最关键的验证——用真实项目对比 hybrid vs 纯词法。

### 5.1 创建验证脚本 `_e2e_verify.py`

```python
import sys, json, re
sys.path.insert(0, ".")
from pathlib import Path
from networkx.readwrite import json_graph
import networkx as nx
from graphify.hybrid_scorer import HybridScorer
from graphify.serve import _query_graph_text

GRAPH = Path("tests/e2e/resources/user-management/src/.graph/graph.json")
raw = json.loads(GRAPH.read_text(encoding="utf-8"))
if "links" not in raw and "edges" in raw:
    raw = dict(raw, links=raw["edges"])
raw = dict(raw, links=[
    {**l, "_src": l.get("_src", l.get("source")), "_tgt": l.get("_tgt", l.get("target"))}
    for l in raw.get("links", [])
])
try:
    G = json_graph.node_link_graph(raw, edges="links")
except TypeError:
    G = json_graph.node_link_graph(raw)

# 附加 HybridScorer (会自动加载 sidecar)
G.graph["_hybrid_scorer"] = HybridScorer(GRAPH.parent)
scorer = G.graph["_hybrid_scorer"]
print(f"图: {G.number_of_nodes()} 节点, {G.number_of_edges()} 边")
print(f"HybridScorer.available: {scorer.available}")
print(f"  matrix shape: {scorer._matrix.shape if scorer._matrix is not None else None}")
print(f"  model: {scorer._model!r}")
print(f"  backend: {scorer._embed_backend!r}")
print()

def get_seeds(result):
    if "No matching nodes found" in result:
        return "No match"
    m = re.search(r"Start: \[([^\]]+)\]", result)
    return m.group(1) if m else "?"

QUERIES = [
    "login",
    "how does authentication work",
    "verify password",
    "generate token",
    "AuthService",
]

print("=" * 80)
print("AC1: hybrid 模式 (semantic=True, vector+fuzzy tier 启用)")
print("=" * 80)
for q in QUERIES:
    result = _query_graph_text(G, q, graph_path=str(GRAPH), semantic=True, top_k=5)
    seeds = get_seeds(result)
    print(f"  {q:40s} -> {seeds}")

print()
print("=" * 80)
print("AC2: 纯词法对照 (semantic=False, vector+fuzzy 关闭)")
print("=" * 80)
for q in QUERIES:
    result = _query_graph_text(G, q, graph_path=str(GRAPH), semantic=False, top_k=5)
    seeds = get_seeds(result)
    print(f"  {q:40s} -> {seeds}")

print()
print("=" * 80)
print("AC6: 精确查询 'AuthService' — hybrid 不应干扰 EXACT 主导")
print("=" * 80)
r_hybrid = _query_graph_text(G, "AuthService", graph_path=str(GRAPH), semantic=True, top_k=5)
r_lex = _query_graph_text(G, "AuthService", graph_path=str(GRAPH), semantic=False, top_k=5)
print(f"  hybrid 模式 top seed: {get_seeds(r_hybrid)}")
print(f"  纯词法 模式 top seed: {get_seeds(r_lex)}")

print()
print("=" * 80)
print("关键对比: 'how does authentication work'")
print("=" * 80)
r_hybrid2 = _query_graph_text(G, "how does authentication work", graph_path=str(GRAPH), semantic=True, top_k=5)
r_lex2 = _query_graph_text(G, "how does authentication work", graph_path=str(GRAPH), semantic=False, top_k=5)
print(f"  纯词法: {get_seeds(r_lex2)}")
print(f"  hybrid: {get_seeds(r_hybrid2)}")
```

### 5.2 运行验证

```powershell
$env:GRAPHIFY_EMBED_BACKEND = "sentence-transformers"
python _e2e_verify.py
```

**预期输出**：
```
图: 81 节点, 204 边
HybridScorer.available: True
  matrix shape: (81, 384)
  model: 'all-MiniLM-L6-v2'
  backend: 'sentence-transformers'

================================================================================
AC1: hybrid 模式 (semantic=True, vector+fuzzy tier 启用)
================================================================================
  login                                    -> '.login()'
  how does authentication work             -> 'AuthenticatedRequest', '.login()', 'AuthController', '.handleLogin()', 'AuthMiddleware'
  verify password                          -> 'PasswordHasher', 'password.ts', '.verify()'
  generate token                           -> 'TokenPayload', '.generateToken()'
  AuthService                              -> 'AuthService'

================================================================================
AC2: 纯词法对照 (semantic=False, vector+fuzzy 关闭)
================================================================================
  login                                    -> '.login()'
  how does authentication work             -> No match
  verify password                          -> 'password.ts', 'PasswordHasher', '.verify()'
  generate token                           -> 'TokenPayload', '.generateToken()'
  AuthService                              -> 'AuthService'

================================================================================
AC6: 精确查询 'AuthService' — hybrid 不应干扰 EXACT 主导
================================================================================
  hybrid 模式 top seed: 'AuthService'
  纯词法 模式 top seed: 'AuthService'

================================================================================
关键对比: 'how does authentication work'
================================================================================
  纯词法: No match
  hybrid: 'AuthenticatedRequest', '.login()', 'AuthController', '.handleLogin()', 'AuthMiddleware'
```

### 5.3 验证结论

| AC | 查询 | 纯词法 | hybrid | 结论 |
|---|---|---|---|---|
| **AC1** | `how does authentication work` | No match | 命中 5 个 auth 节点 | ✅ vector tier 救回零词法重叠的节点 |
| **AC2** | 同上 | No match（对照） | 命中（实验组） | ✅ `--no-semantic` 确实关闭 vector tier |
| **AC6** | `AuthService` | AuthService (top-1) | AuthService (top-1) | ✅ 精确查询不受 vector bonus 干扰 |

> **关键证据**：`how does authentication work` 在纯词法模式下 `No match`（"how"/"does"/"work" 是停用词被过滤，"authentication" 不是任何节点 label 的子串），hybrid 模式命中 5 个 auth 相关节点——这是 vector tier 把语义相关但零词法重叠的节点救回来的直接证据。

---

## 步骤 6：benchmark 召回率对比（AC5）

### 6.1 运行 benchmark

```powershell
$env:PYTHONPATH = "."
$env:PYTHONIOENCODING = "utf-8"
$env:GRAPHIFY_EMBED_BACKEND = "sentence-transformers"
python tests/fixtures/search_benchmark/run_benchmark.py
```

**预期输出**：
```
Mode: hybrid (vector+fuzzy)
Pure lexical recall@5: 4/10 = 40.0%
Hybrid        recall@5: 10/10 = 100.0%

Per-query (✓=hit, ✗=miss):
  [✓] login
  [✓] authentication
  [✓] UserServise
  [✓] rate limiter
  [✓] credential validation
  [✓] create account
  [✓] throttle requests
  [✓] user profile management
  [✓] session token
  [✓] expire cache entries

PASS: hybrid recall (100.0%) >= pure lexical (40.0%)
```

> **验证点**：
> - `Mode: hybrid (vector+fuzzy)` —— 说明 sidecar 被识别并加载
> - 纯词法只命中 4/10（`UserServise` typo、`create account`、`throttle requests`、`expire cache entries`——这些有词法重叠）
> - hybrid 命中全部 10/10——vector tier 补上了 `login`/`authentication`/`rate limiter`/`credential validation`/`user profile management`/`session token` 这 6 个零词法重叠的语义查询

---

## 步骤 7：用 graphify CLI 命令验证（可选，证明 CLI 路径也能跑）

### 7.1 hybrid 模式查询

```powershell
$env:GRAPHIFY_EMBED_BACKEND = "sentence-transformers"
python -m graphify query "how does authentication work" --graph tests/e2e/resources/user-management/src/.graph/graph.json
```

**预期**：输出包含 `Start: [AuthenticatedRequest, .login(), AuthController, .handleLogin(), AuthMiddleware]` 和 BFS 遍历的子图文本。

### 7.2 纯词法对照查询

```powershell
python -m graphify query "how does authentication work" --no-semantic --graph tests/e2e/resources/user-management/src/.graph/graph.json
```

**预期**：输出 `No matching nodes found.`

> 如果 `--no-semantic` 也命中了节点，说明 vector tier 没有被正确关闭——这是验证 AC2 的直接方法。

---

## 清理临时脚本

验证完成后删除临时脚本：

```powershell
Remove-Item -Path "_check_desc.py","_gen_embeddings.py","_e2e_verify.py" -Force -ErrorAction SilentlyContinue
```

---

## 切换到其他 backend（可选）

如果你想用 Ollama 或 OpenAI 而非 sentence-transformers 重新验证。推荐用 `.graph/graphifyrc` 配置文件（无需 env var，配置持久化）：

### 用配置文件 `.graph/graphifyrc`（推荐）

在项目的 `.graph/` 目录下创建 `graphifyrc`（和 graph.json 同目录）：

```ini
# tests/e2e/resources/user-management/src/.graph/graphifyrc
embed_backend=openai-compatible
embed_base_url=http://my-embedding-server:8080/v1
embed_api_key=sk-your-key
embed_model=text-embedding-3-small
```

配置后无需 env var，直接生成 sidecar + 查询：

```powershell
python -c "from graphify.embeddings import generate_embeddings_for_graph; from pathlib import Path; generate_embeddings_for_graph(Path('tests/e2e/resources/user-management/src/.graph/graph.json'), backend='openai-compatible')"
python -m graphify query "how does authentication work" --graph tests/e2e/resources/user-management/src/.graph/graph.json
```

### 用 Ollama（env var 方式）

```powershell
# 1. 安装并启动 ollama
ollama serve
# 2. 拉模型
ollama pull nomic-embed-text
# 3. 重新生成 sidecar
$env:GRAPHIFY_EMBED_BACKEND = "ollama"
python -c "from graphify.embeddings import generate_embeddings_for_graph; from pathlib import Path; generate_embeddings_for_graph(Path('tests/e2e/resources/user-management/src/.graph/graph.json'), backend='ollama', model='nomic-embed-text')"
# 4. 查询 (sidecar 会自动用最新的)
python -m graphify query "how does authentication work" --graph tests/e2e/resources/user-management/src/.graph/graph.json
```

### 用 OpenAI（env var 方式）

```powershell
$env:OPENAI_API_KEY = "sk-..."
$env:GRAPHIFY_EMBED_BACKEND = "openai"
python -c "from graphify.embeddings import generate_embeddings_for_graph; from pathlib import Path; generate_embeddings_for_graph(Path('tests/e2e/resources/user-management/src/.graph/graph.json'), backend='openai', model='text-embedding-3-small')"
python -m graphify query "how does authentication work" --graph tests/e2e/resources/user-management/src/.graph/graph.json
```

### 配置优先级

```
CLI flag (--embed-backend) > .graph/graphifyrc > 环境变量 > graphify/.default-graphifyrc (出厂默认)
```

> **注意**：切换 backend 后需要重新生成 sidecar（不同模型的向量空间不兼容，不能混用）。
> `load_embedding_sidecar` 会按 mtime 选最新的 `.npy`，所以新 sidecar 会自动覆盖旧的。

---

## 验证证据汇总

| 验证项 | 步骤 | 命令 | 预期结果 | 实际结果 |
|---|---|---|---|---|
| 环境就绪 | 1 | `python -c "import sentence_transformers"` | OK | ✅ 6.0.0 |
| 真实项目存在 | 2 | `Get-ChildItem ... -Filter *.ts` | 12 个文件 | ✅ 12 |
| desc 提取 | 3 | `python -m graphify extract ... --force` | 81 节点，部分带 desc | ✅ 81 节点，30 带 desc |
| sidecar 生成 | 4 | `python _gen_embeddings.py` | .npy + .index.json + .meta.json | ✅ 124KB .npy, 81×384 维 |
| AC1 vector 救援 | 5 | `python _e2e_verify.py` | hybrid 命中，纯词法 No match | ✅ `how does authentication work` hybrid 命中 5 节点 |
| AC2 semantic 开关 | 5 | 同上 | `--no-semantic` 关闭 vector | ✅ 纯词法 No match |
| AC6 精确查询不退化 | 5 | 同上 | AuthService 两种模式都 top-1 | ✅ |
| AC5 召回率 | 6 | `python tests/fixtures/search_benchmark/run_benchmark.py` | hybrid ≥ 纯词法 | ✅ 100% vs 40% |

---

## 附：产物文件结构

验证完成后，`tests/e2e/resources/user-management/src/.graph/` 目录：

```
.graph/
├── graph.json                    # 81 节点 (含 desc 字段)
├── manifest.json
├── cache/
│   └── stat-index.json
└── embeddings/                   # ← embedding sidecar (本验证生成)
    ├── all_minilm_l6_v2.npy      # (81, 384) float32 矩阵
    ├── all_minilm_l6_v2.index.json  # node_id -> row 映射
    └── all_minilm_l6_v2.meta.json   # 模型/维度/生成时间
```

> 这些 sidecar 文件和 `graph.json` 一样是确定性产物（同模型 + 同输入产出相同向量），可以提交到代码仓。
