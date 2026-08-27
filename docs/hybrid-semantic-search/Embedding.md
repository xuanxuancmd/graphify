# Embedding 配置指南

hybrid 语义检索的 vector tier 需要一个 embedding 模型。本文档说明如何配置和启动 embedding 后端。

## 两种部署模式

| 模式 | 适用场景 | 是否需要服务进程 | 是否需要 API key | 数据是否出机器 |
|---|---|---|---|---|
| **在线模型** | 生产环境 | ❌（调云 API） | ✅ | ✅（数据发到云端） |
| **本地 Ollama** | 隐私敏感 / 离线 / 免费 | ✅（ollama daemon） | ❌ | ❌（完全本地） |
| **sentence-transformers**（仅测试/CI） | 测试 / CI | ❌（进程内加载） | ❌ | ❌（完全本地） |

---

## 模式 1：本地 Ollama（推荐用于本地开发 / 离线场景）

### 一键启动

```bash
# 1. 安装 ollama (首次, macOS/Linux/Windows 均可)
#    macOS:   brew install ollama
#    Linux:   curl -fsSL https://ollama.com/install.sh | sh
#    Windows: winget install Ollama.Ollama  (或从 https://ollama.com/download 下载)

# 2. 启动 ollama 服务 (后台常驻)
ollama serve &                           # Linux/macOS
# Windows PowerShell:
#   Start-Process ollama -ArgumentList "serve" -WindowStyle Hidden

# 3. 拉取 embedding 模型 (首次, ~270MB)
ollama pull nomic-embed-text

# 4. 验证模型可用
ollama run nomic-embed-text "hello world"   # 应返回向量

# 5. 生成 embedding sidecar (在项目根目录)
graphify extract . --embed-backend ollama

# 6. 查询 (自动加载 sidecar)
graphify query "how does login work?"
```

### 环境变量（可选）

```bash
# 指定 ollama 服务地址 (默认 http://localhost:11434)
export OLLAMA_BASE_URL=http://localhost:11434

# 指定 embedding 模型 (默认 nomic-embed-text)
export OLLAMA_MODEL=nomic-embed-text

# 或在 extract 时显式指定
graphify extract . --embed-backend ollama --embed-model nomic-embed-text
```

### 一键脚本（Windows PowerShell）

```powershell
# tests/e2e/resources/user-management/start-ollama.ps1
# 启动 ollama + 拉模型 + 生成 embedding sidecar
ollama serve &
Start-Sleep -Seconds 2
ollama pull nomic-embed-text
$env:GRAPHIFY_EMBED_BACKEND = "ollama"
python -m graphify extract tests/e2e/resources/user-management/src --embed-backend ollama --no-cluster --no-viz --code-only
```

### 一键脚本（Linux/macOS bash）

```bash
# tests/e2e/resources/user-management/start-ollama.sh
#!/usr/bin/env bash
set -e
ollama serve &
sleep 2
ollama pull nomic-embed-text
export GRAPHIFY_EMBED_BACKEND=ollama
python -m graphify extract tests/e2e/resources/user-management/src \
  --embed-backend ollama --no-cluster --no-viz --code-only
```

---

## 模式 2：在线模型（推荐用于生产 / 召回质量优先）

### OpenAI

```bash
# 1. 配置 API key
export OPENAI_API_KEY=sk-...
# (可选) 指定兼容端点: export OPENAI_BASE_URL=https://api.openai.com/v1

# 2. 生成 sidecar
graphify extract . --embed-backend openai

# 3. 查询
graphify query "how does login work?"
```

默认模型 `text-embedding-3-small`（384 维）。可用 `--embed-model text-embedding-3-large` 切换。

### Gemini / Kimi / DeepSeek / Azure

```bash
# Gemini
export GEMINI_API_KEY=...
graphify extract . --embed-backend gemini

# Kimi (Moonshot, 服务器在中国)
export MOONSHOT_API_KEY=...
graphify extract . --embed-backend kimi

# Azure OpenAI
export AZURE_OPENAI_API_KEY=...
export AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
graphify extract . --embed-backend azure
```

**注意**：Anthropic Claude 没有 embedding API。如果默认 backend 是 claude，必须显式指定 `--embed-backend openai`（或其他 embedding-capable backend），否则 query 时自动降级为纯词法。

---

## 模式 3：sentence-transformers（仅测试/CI）

纯本地 CPU 推理，无需 ollama 服务，无需 API key。**仅用于测试**，生产环境请用模式 1 或 2。

```bash
# 1. 安装
pip install sentence-transformers

# 2. 生成 sidecar (首次会下载 ~80MB 模型到 ~/.cache/huggingface/)
export GRAPHIFY_EMBED_BACKEND=sentence-transformers
python -c "
from graphify.embeddings import generate_embeddings_for_graph
from pathlib import Path
generate_embeddings_for_graph(
    Path('tests/e2e/resources/user-management/src/.graph/graph.json'),
    backend='sentence-transformers',
    model='all-MiniLM-L6-v2'
)
"

# 3. 查询
graphify query "how does login work?"
```

CPU 性能：`all-MiniLM-L6-v2`（384 维）在普通 CPU 上编码 81 节点 + 10 query ≈ 6 秒。

---

## 持久化文件

无论用哪种模式，生成的 sidecar 文件结构相同：

```
graphify-out/embeddings/       (或 <out_dir>/embeddings/)
├── <model_slug>.npy           # numpy 二进制矩阵 (N, D) float32
├── <model_slug>.index.json    # node_id -> row index 映射
└── <model_slug>.meta.json     # 生成时间 / 维度 / 模型名 / backend
```

**可以提交到代码仓**——和 `graph.json` 一样是确定性产物（同模型 + 同输入产出相同向量）。benchmark fixture 已提交：`tests/fixtures/search_benchmark/embeddings/`。

---

## 环境变量速查

| 变量 | 用途 | 默认值 |
|---|---|---|
| `GRAPHIFY_EMBED_BACKEND` | query 时自动检测的 embedding backend | 自动检测（按 OPENAI→GEMINI→KIMI→...→OLLAMA 优先级） |
| `GRAPHIFY_EMBED_MODEL` | embedding 模型名覆盖 | 按 backend 自动选 |
| `OPENAI_API_KEY` + `OPENAI_BASE_URL` | OpenAI / 兼容端点 | — |
| `GEMINI_API_KEY` 或 `GOOGLE_API_KEY` | Gemini | — |
| `MOONSHOT_API_KEY` | Kimi | — |
| `OLLAMA_BASE_URL` + `OLLAMA_MODEL` | Ollama | `http://localhost:11434` / `nomic-embed-text` |
| `AZURE_OPENAI_API_KEY` + `AZURE_OPENAI_ENDPOINT` | Azure OpenAI | — |

---

## 降级行为

- 无 sidecar 文件 → `HybridScorer.available=False`，query 自动退回纯词法（不报错）
- 有 sidecar 但无 backend 配置 → 同上，退回纯词法
- embedding API 调用失败 → build 时打 warning（不阻断 graph 生成），query 时退回纯词法

---

## 当前已验证的端到端结果

用 `tests/e2e/resources/user-management` 真实项目（81 节点，TS 代码）+ `sentence-transformers` 本地模型验证：

| 查询 | 纯词法 | hybrid (vector+fuzzy) | 说明 |
|---|---|---|---|
| `login` | `.login()` | `.login()` | 都命中（有词法重叠） |
| `how does authentication work` | **No match** | `AuthenticatedRequest`, `.login()`, `AuthController`, `.handleLogin()`, `AuthMiddleware` | vector 救回 5 个节点 |
| `AuthService` | `AuthService` | `AuthService` | 精确查询不受干扰（AC6） |

benchmark fixture（10 节点小图）：hybrid recall@5 = **100%** vs pure lexical **40%**。
