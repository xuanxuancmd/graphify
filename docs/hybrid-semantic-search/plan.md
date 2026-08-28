# Plan: 混合语义检索（语义 + fuzzy 重排）

> 关联：spec.md（同目录）。本 plan 是逐步实施文件级改动清单，目标是解耦可回 upstream。

## 0. 改动总览

| 改动 | 文件 | 类型 | 解耦策略 |
|---|---|---|---|
| 新建 desc 提取模块 | `graphify/desc.py` | 新文件 | 按语言分派 docstring/注释提取，被 engine.py 和 markdown.py 调用 |
| 修改 `_extract_generic` 的 `add_node` | `graphify/extractors/engine.py` | 修改（加 desc 参数 + 调用 desc 提取） | `add_node` 加 `desc` 可选参数；`walk` 在创建函数/类节点时提取 desc |
| 修改 `extract_markdown` 的 `add_node` | `graphify/extractors/markdown.py` | 修改（加 desc 参数 + 正文首段提取） | file/heading 节点加 `desc`，取正文首段 |
| 新建 embedding 生成模块 | `graphify/embeddings.py` | 新文件 | 独立模块，仅被 build-time 和 serve.py 引用；文本源只用 `desc`（fallback label） |
| 新建 fuzzy matcher 模块 | `graphify/fuzzy.py` | 新文件 | 独立模块，复用 rapidfuzz（已有依赖） |
| 新建 hybrid scorer | `graphify/hybrid_scorer.py` | 新文件 | 独立模块，封装 vector tier + fuzzy tier，被 serve.py 调用 |
| 修改 `_score_query` | `graphify/serve.py` | 修改（加参数 + 加法 tier） | 新增 `query_embedding`/`semantic` 参数；既有 3 层 if/elif 不变，新 tier 在 L590 后加法 |
| 修改 `_query_graph_text` | `graphify/serve.py` | 修改（加参数 + top_n 多结果返回） | 新增 `semantic`/`top_k`/`top_n` 参数；`top_n>1` 时循环 BFS 返回多个子图 |
| 修改 MCP `query_graph` schema | `graphify/serve.py` | 修改（加字段） | inputSchema 加 `semantic`/`top_k`/`top_n` |
| 修改 `_tool_query_graph` | `graphify/serve.py` | 修改（透传参数） | 从 arguments 取 `semantic`/`top_k`/`top_n` 传给 `_query_graph_text` |
| 修改 graph loading | `graphify/serve.py` | 修改（加 sidecar 加载） | `_load_graph` / `_GraphContextCache._load_entry` 加载 embedding sidecar |
| 新建 build-time embed 命令 | `graphify/cli.py` | 修改（加 flag） | `--embed-backend` / `--embed-model` flag |
| 新建测试 | `tests/test_hybrid_search.py` | 新文件 | 独立测试 |
| 新建 desc 提取测试 | `tests/test_desc_extraction.py` | 新文件 | 测试各语言 docstring/注释提取 |

**不改的文件**：`extract.py`（`_extract_generic` 在 engine.py，不在 extract.py）、`build.py`、`llm.py`（build-time embedding 在 `embeddings.py` 独立实现，不侵入 extract pipeline）、`_score_query` 既有 3 层 if/elif/elif 逻辑。

---

## 1. 步骤 1：创建 `graphify/desc.py`（节点 desc 字段提取）

### 1.1 职责

- `_extract_node_desc(node, source, language) -> str`：从 AST 节点提取 docstring/注释作为 desc
- 按语言分派：Python（body 首个 string statement）/ JS-TS（JSDoc comment）/ C-Go-Rust（函数上方 comment）/ Java-C#-Swift（同 C 模式）
- Markdown 文档节点的 desc 提取在 `markdown.py` 内联实现（不走本模块）

### 1.2 文件内容

```python
# graphify/desc.py
"""Node desc field extraction for hybrid semantic search.

Extracts docstrings/comments as per-node `desc` fields, used as the sole
embedding text source. Decoupled from extract.py — called by engine.py's
_extract_generic walk and markdown.py's extract_markdown.

Supported languages (others leave desc empty, fallback to label at embed time):
- Python: module/function/class docstring (first string in body)
- JS/TS: JSDoc comment (/** ... */) immediately before declaration
- C/C++/Go/Rust/Java/C#/Swift: block comment immediately before declaration
"""
from __future__ import annotations

_DESC_MAX_CHARS = 512  # cap desc length (embedding models use ~512 tokens)


def _clean_desc(raw: str) -> str:
    """Strip comment markers, dedent, collapse whitespace, cap length."""
    if not raw:
        return ""
    lines = []
    for line in raw.splitlines():
        stripped = line.strip()
        # Strip comment markers: #, //, /*, */, *, --
        for prefix in ("#", "//", "/*", "*/", "*", "--"):
            if stripped.startswith(prefix):
                stripped = stripped[len(prefix):].strip()
                break
        if stripped:
            lines.append(stripped)
    desc = " ".join(lines).strip()
    return desc[:_DESC_MAX_CHARS]


def _extract_node_desc(node, source: bytes, language: str) -> str:
    """Extract desc from an AST node. Returns '' if no docstring/comment found.

    Called by engine.py walk() when creating function/class/file nodes.
    """
    if language == "python":
        return _extract_python_docstring(node, source)
    if language in ("javascript", "typescript"):
        return _extract_jsdoc(node, source)
    if language in ("c", "cpp", "go", "rust", "java", "c_sharp", "swift"):
        return _extract_preceding_comment(node, source)
    return ""


def _extract_python_docstring(node, source: bytes) -> str:
    """Python: first statement in block body is a string literal (docstring)."""
    body = node.child_by_field_name("body")
    if body is None:
        # Module-level: node IS the module, body is first child block
        for child in node.children:
            if child.type == "block":
                body = child
                break
    if body is None or len(body.children) == 0:
        return ""
    first = body.children[0]
    # docstring is expression_statement containing a string
    if first.type == "expression_statement":
        for sub in first.children:
            if sub.type == "string":
                raw = _node_text(sub, source)
                return _clean_desc(_strip_quotes(raw))
    return ""


def _extract_jsdoc(node, source: bytes) -> str:
    """JS/TS: JSDoc comment /** ... */ immediately before the declaration."""
    prev = node.prev_sibling
    if prev is not None and prev.type == "comment":
        raw = _node_text(prev, source)
        if raw.startswith("/**"):
            return _clean_desc(raw)
    return ""


def _extract_preceding_comment(node, source: bytes) -> str:
    """C/Go/Rust/Java/C#/Swift: block comment immediately before declaration."""
    prev = node.prev_sibling
    if prev is not None and prev.type in ("comment", "block_comment"):
        raw = _node_text(prev, source)
        # Only block comments (/* ... */), not line comments trailing code
        if raw.startswith("/*"):
            return _clean_desc(raw)
    return ""


def _node_text(node, source: bytes) -> str:
    return source[node.start_byte:node.end_byte].decode("utf-8", errors="replace")


def _strip_quotes(s: str) -> str:
    """Strip Python string quotes/triple-quotes."""
    s = s.strip()
    for q in ('"""', "'''", '"', "'"):
        if s.startswith(q) and s.endswith(q) and len(s) >= 2 * len(q):
            return s[len(q):-len(q)]
    return s
```

### 1.3 LOC 估算：~100 LOC

---

## 2. 步骤 2：创建 `graphify/embeddings.py`

### 2.1 职责

- `_embed_batch(texts, backend, model) -> np.ndarray`：批量 embed 文本
- `generate_embeddings_for_graph(graph_json_path, backend, model) -> sidecar files`：build-time 为图所有节点生成 embedding（文本源只用 `desc`，fallback `label`）
- `load_embedding_sidecar(graph_dir) -> (np.ndarray, dict[str, int]) | None`：加载 sidecar
- `embed_query(query, backend, model, cache) -> np.ndarray`：查询时 embed query

### 2.2 文件结构

```python
# graphify/embeddings.py
"""Embedding generation and storage for hybrid semantic search.

Build-time: generates per-node embeddings from `desc` (fallback `label`),
stores as binary sidecar under .graph/embeddings/.
Query-time: loads sidecar + embeds query string for cosine similarity.

Decoupled from extract.py / llm.py — called as a post-build step.
Text source: ONLY `desc` field. norm_label / nid / source_file are NOT
embedded — they stay in the lexical tier to avoid path-noise in cosine sim.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

# ---------------------------------------------------------------------------
# Node embed text: desc only (fallback to label)
# ---------------------------------------------------------------------------

def _node_embed_text(node: dict) -> str:
    """The sole embedding text source.

    desc = docstring (code) / first paragraph (docs).
    When desc is empty, fall back to label so every node still gets a vector.
    norm_label / nid / source_file are deliberately excluded — path fragments
    pollute cosine similarity with directory-structure coincidence rather than
    semantic content.
    """
    desc = node.get("desc", "")
    if desc:
        return desc
    return node.get("label", "")


# ---------------------------------------------------------------------------
# Model slug + sidecar paths
# ---------------------------------------------------------------------------

def _model_slug(model: str) -> str:
    """Normalize model name to filesystem-safe slug."""
    return model.replace("/", "_").replace("-", "_").replace(".", "_").lower()


def _sidecar_paths(graph_dir: Path, model: str) -> dict[str, Path]:
    slug = _model_slug(model)
    return {
        "npy": graph_dir / "embeddings" / f"{slug}.npy",
        "index": graph_dir / "embeddings" / f"{slug}.index.json",
        "meta": graph_dir / "embeddings" / f"{slug}.meta.json",
    }


# ---------------------------------------------------------------------------
# Batch embedding (backend-agnostic)
# ---------------------------------------------------------------------------

def _embed_batch(
    texts: list[str], *, backend: str, model: str | None = None, root: Path | None = None
) -> tuple[np.ndarray, str]:
    """Embed a batch of texts. Returns (embeddings, actual_model_used)."""
    # Dispatch to backend (reuse llm.py BACKENDS config for base_url/env_key)
    # ... implementation mirrors llm.py's backend dispatch
    pass  # ~60 LOC


# ---------------------------------------------------------------------------
# Build-time: generate embeddings for all graph nodes
# ---------------------------------------------------------------------------

def generate_embeddings_for_graph(
    graph_json_path: Path, *, backend: str, model: str | None = None
) -> Path:
    """Generate embeddings for all nodes in graph.json. Writes sidecar .npy + .index.json.

    Text source: ONLY `desc` (fallback `label`). See _node_embed_text.
    """
    graph_dir = graph_json_path.parent
    data = json.loads(graph_json_path.read_text(encoding="utf-8"))
    nodes = data.get("nodes", [])
    if not nodes:
        raise ValueError("graph has no nodes to embed")

    texts = [_node_embed_text(n) for n in nodes]  # desc-only, fallback label
    embeddings, actual_model = _embed_batch(texts, backend=backend, model=model)

    paths = _sidecar_paths(graph_dir, actual_model)
    paths["npy"].parent.mkdir(parents=True, exist_ok=True)

    # Save .npy (float32, shape (N, D))
    np.save(paths["npy"], embeddings)

    # Save .index.json (node_id -> row index)
    index = {n["id"]: i for i, n in enumerate(nodes)}
    paths["index"].write_text(
        json.dumps({"node_ids": list(index.keys()), "model": actual_model, "dim": embeddings.shape[1]}),
        encoding="utf-8",
    )

    # Save .meta.json
    paths["meta"].write_text(
        json.dumps({
            "generated_at": ...,  # ISO timestamp
            "node_count": len(nodes),
            "dim": embeddings.shape[1],
            "model": actual_model,
        }),
        encoding="utf-8",
    )
    return paths["npy"]


# ---------------------------------------------------------------------------
# Query-time: load sidecar + embed query
# ---------------------------------------------------------------------------

def load_embedding_sidecar(graph_dir: Path) -> tuple[np.ndarray, dict[str, int], str] | None:
    """Load the most recent embedding sidecar. Returns (matrix, id_to_row, model) or None."""
    emb_dir = graph_dir / "embeddings"
    if not emb_dir.is_dir():
        return None
    # Find any .npy (if multiple models, pick the newest by mtime)
    npy_files = sorted(emb_dir.glob("*.npy"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not npy_files:
        return None
    npy_path = npy_files[0]
    slug = npy_path.stem
    index_path = emb_dir / f"{slug}.index.json"
    if not index_path.is_file():
        return None
    matrix = np.load(npy_path)
    index_data = json.loads(index_path.read_text(encoding="utf-8"))
    id_to_row = {nid: i for i, nid in enumerate(index_data["node_ids"])}
    return matrix, id_to_row, index_data.get("model", "")


def embed_query(
    query: str, *, backend: str, model: str, cache: dict[str, np.ndarray] | None = None
) -> np.ndarray | None:
    """Embed a query string. Uses LRU cache if provided."""
    if cache is not None and query in cache:
        return cache[query]
    try:
        vec, _ = _embed_batch([query], backend=backend, model=model)
    except Exception:
        return None
    if cache is not None:
        cache[query] = vec[0]
    return vec[0]


# ---------------------------------------------------------------------------
# Cosine similarity (numpy brute-force)
# ---------------------------------------------------------------------------

def cosine_similarity(query_vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """Cosine similarity of query_vec against each row of matrix. Returns (N,) array."""
    # Normalize
    q_norm = query_vec / (np.linalg.norm(query_vec) + 1e-8)
    m_norm = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-8)
    return m_norm @ q_norm  # (N,)
```

### 2.3 LOC 估算：~250 LOC

---

## 3. 步骤 3：修改 `graphify/extractors/engine.py`（desc 字段提取）

### 3.1 职责

- 修改 `_extract_generic` 的 `add_node`，增加 `desc` 可选参数
- 在 `walk` 处理 `function_definition` / `class_declaration` 时调用 `desc._extract_node_desc` 提取 docstring
- 节点 JSON 增加 `desc` 字段

### 3.2 改动点

```python
# engine.py — add_node 加 desc 参数 (原 L2995)：
from graphify.desc import _extract_node_desc

def add_node(nid: str, label: str, line: int, *, node_type: str | None = None,
             metadata: dict | None = None, desc: str = "") -> None:  # 新增 desc
    if nid in seen_ids:
        return
    seen_ids.add(nid)
    merged = dict(metadata or {})
    if namespace_stack:
        merged.setdefault("namespace", ".".join(namespace_stack))
    if scope_stack and node_type != "namespace":
        merged.setdefault("scope_chain", list(scope_stack))
    node = {
        "id": nid,
        "label": label,
        "file_type": "code",
        "source_file": str_path,
        "source_location": f"L{line}",
    }
    if node_type:
        node["type"] = node_type
    if desc:                                     # 新增：非空时写入
        node["desc"] = sanitize_label(desc)      # 复用安全过滤
    if merged:
        node["metadata"] = sanitize_metadata(merged)
    nodes.append(node)
```

```python
# engine.py — walk() 处理 function_definition / class_declaration 时提取 desc：
# 在 add_node(class_nid, class_name, line, ...) 调用处加 desc 参数：

# 语言名从 config 推导
language = config.ts_module.replace("tree_sitter_", "")  # "python" / "javascript" / ...

# 函数节点
if t in config.function_types:
    # ... 既有逻辑取 name/body ...
    desc = _extract_node_desc(node, source, language)
    add_node(fn_nid, fn_name, line, node_type=..., desc=desc)

# 类节点
if t in config.class_types:
    # ... 既有逻辑 ...
    desc = _extract_node_desc(node, source, language)
    add_node(class_nid, class_name, line, metadata=metadata, desc=desc)

# 文件节点（模块级 docstring）
add_node(file_nid, path.name, 1, desc=_extract_node_desc(root, source, language))
```

### 3.3 影响面控制

- `_extract_generic` 是 40+ 语言共用引擎，加 `desc` 参数**向后兼容**（默认 `""`，不传则不写 desc 字段）
- desc 提取只处理有明确 docstring 模式的语言（Python/JS/TS/C/C++/Go/Rust/Java/C#/Swift），其余语言 `_extract_node_desc` 返回 `""`，节点无 desc（fallback 到 label）
- 既有测试不受影响（desc 是新增字段，不改变既有字段语义）

### 3.4 LOC 估算：~40 LOC（改动）+ 依赖步骤 1 的 desc.py

---

## 4. 步骤 4：修改 `graphify/extractors/markdown.py`（文档节点 desc）

### 4.1 职责

- file 节点（`node_kind: "page"`）的 `desc` 取正文首段
- heading 节点的 `desc` 取该标题下首个段落

### 4.2 改动点

```python
# markdown.py — add_node 加 desc 参数 (原 L288)：
def add_node(nid: str, label: str, line: int, file_type: str = "document",
             node_kind: str = "heading", extra: "dict | None" = None,
             desc: str = "") -> None:  # 新增 desc
    if nid not in seen_ids:
        seen_ids.add(nid)
        node = {"id": nid, "label": label, "file_type": file_type,
                "node_kind": node_kind,
                "source_file": str_path, "source_location": f"L{line}"}
        if desc:                                  # 新增
            node["desc"] = sanitize_label(desc)   # 复用安全过滤
        if extra:
            node.update(extra)
        nodes.append(node)
```

```python
# markdown.py — 提取正文首段作为 file 节点 desc：
# 在 walk 循环中收集正文段落，首个段落作为 file 节点的 desc
first_paragraph_lines: list[str] = []
for line_num_0, line_text in enumerate(lines):
    if line_num_0 < body_start:
        continue
    # ... 既有 heading/code-block 逻辑 ...
    stripped = line_text.strip()
    if stripped and not stripped.startswith("#") and not stripped.startswith("```"):
        first_paragraph_lines.append(stripped)
        # 连续非空行组成首段
        if line_num_0 + 1 < len(lines) and not lines[line_num_0 + 1].strip():
            break  # 空行结束首段
    elif first_paragraph_lines:
        break
first_paragraph = " ".join(first_paragraph_lines)[:512]

# file 节点加 desc
add_node(file_nid, path.name, 1, node_kind="page",
         extra={"frontmatter": frontmatter} if frontmatter else None,
         desc=first_paragraph)
```

### 4.3 LOC 估算：~40 LOC（改动）

---

## 5. 步骤 5：创建 `graphify/fuzzy.py`

### 5.1 职责

- 用 `rapidfuzz`（已有依赖 `pyproject.toml:17`）做 Jaro-Winkler 相似度
- 对 query token 和节点 label 做 fuzzy 匹配
- 仅当词法 3 层都未命中时触发（避免干扰精确匹配）

### 5.2 文件内容

```python
# graphify/fuzzy.py
"""Fuzzy string matching tier for hybrid search.

Uses rapidfuzz (already a dependency) for Jaro-Winkler similarity.
Triggered only when the lexical 3-tier (exact/prefix/substring) misses,
so it never interferes with precise queries.
"""
from __future__ import annotations

from rapidfuzz.distance import JaroWinkler

FUZZY_THRESHOLD = 0.85  # Only match if similarity >= 0.85


def fuzzy_score(query_token: str, label: str) -> float:
    """Jaro-Winkler similarity in [0, 1]. Returns 0 if below threshold."""
    if not query_token or not label:
        return 0.0
    sim = JaroWinkler.similarity(query_token.lower(), label.lower())
    return sim if sim >= FUZZY_THRESHOLD else 0.0


def fuzzy_best_match(query_token: str, labels: list[str]) -> tuple[float, str | None]:
    """Find the best fuzzy match for query_token among labels.
    Returns (score, best_label) or (0.0, None)."""
    best_score = 0.0
    best_label = None
    for label in labels:
        score = fuzzy_score(query_token, label)
        if score > best_score:
            best_score = score
            best_label = label
    return best_score, best_label
```

### 5.3 LOC 估算：~50 LOC

---

## 6. 步骤 6：创建 `graphify/hybrid_scorer.py`

### 6.1 职责

- 封装 vector tier + fuzzy tier 的打分逻辑
- 被 `serve.py` 的 `_score_query` 调用，作为既有 3 层词法的加法补充
- 加载 embedding sidecar + query embedding

### 6.2 文件内容

```python
# graphify/hybrid_scorer.py
"""Hybrid scorer: vector similarity + fuzzy matching tiers.

Called by serve.py._score_query as an ADDITIVE bonus on top of the existing
3-tier lexical scoring (EXACT/PREFIX/SUBSTRING). Does NOT replace lexical tiers.

Bonus constants:
    _VECTOR_SIMILARITY_BONUS = 5.0   (between SUBSTRING=1 and PREFIX=100)
    _FUZZY_MATCH_BONUS = 2.0         (above SUBSTRING=1, below VECTOR=5)
"""
from __future__ import annotations

import numpy as np

from graphify.embeddings import cosine_similarity, embed_query, load_embedding_sidecar
from graphify.fuzzy import fuzzy_score

_VECTOR_SIMILARITY_BONUS = 5.0
_FUZZY_MATCH_BONUS = 2.0


class HybridScorer:
    """Holds loaded embedding matrix + query embedding cache. Per-graph instance."""

    def __init__(self, graph_dir=None, *, embed_backend=None, embed_model=None):
        self._matrix: np.ndarray | None = None
        self._id_to_row: dict[str, int] | None = None
        self._model: str = ""
        self._query_cache: dict[str, np.ndarray] = {}
        self._embed_backend = embed_backend
        self._embed_model = embed_model
        if graph_dir is not None:
            self._load(graph_dir)

    def _load(self, graph_dir) -> None:
        result = load_embedding_sidecar(graph_dir)
        if result is not None:
            self._matrix, self._id_to_row, self._model = result

    @property
    def available(self) -> bool:
        return self._matrix is not None and self._id_to_row is not None

    def vector_scores(self, query: str) -> dict[str, float] | None:
        """Return {node_id: cosine_sim} for all nodes, or None if unavailable."""
        if not self.available:
            return None
        if not self._embed_backend:
            return None
        q_vec = embed_query(
            query, backend=self._embed_backend,
            model=self._embed_model, cache=self._query_cache,
        )
        if q_vec is None:
            return None
        sims = cosine_similarity(q_vec, self._matrix)
        return {
            nid: float(sims[row])
            for nid, row in self._id_to_row.items()
            if 0 <= row < len(sims)
        }

    def fuzzy_score_for_node(self, query_token: str, node_label: str) -> float:
        """Return fuzzy bonus for a (query_token, node_label) pair."""
        return _FUZZY_MATCH_BONUS * fuzzy_score(query_token, node_label)

    @staticmethod
    def vector_bonus(sim: float) -> float:
        return _VECTOR_SIMILARITY_BONUS * sim
```

### 6.3 LOC 估算：~80 LOC

---

## 7. 步骤 7：修改 `graphify/serve.py`

### 7.1 加载 embedding sidecar（在 `_GraphContextCache._load_entry`）

参考既有 `_trigram_index` 的 eager warm 模式（`serve.py:124`）：

```python
# serve.py — 在 _GraphContextCache._load_entry 里，L124 _get_trigram_index(graph) 之后：
from graphify.hybrid_scorer import HybridScorer

# ... 在 graph 加载后：
graph_dir = Path(graph_path).parent
hybrid_scorer = HybridScorer(graph_dir)
graph.graph["_hybrid_scorer"] = hybrid_scorer  # 缓存到 graph 对象上
```

### 7.2 修改 `_score_query`（加参数 + 加法 tier）

**关键：不修改既有 3 层 if/elif/elif（L578-587），只在 L590 后加法补充**：

```python
# serve.py:462 — 修改签名
def _score_query(
    G: nx.Graph,
    terms: list[str],
    *,
    collect_per_term_seeds: bool,
    query_embedding_scores: dict[str, float] | None = None,  # 新增：{node_id: cosine_sim}
    hybrid_scorer: HybridScorer | None = None,                # 新增
    semantic: bool = True,                                     # 新增
) -> _QueryScores:

    # ... 既有逻辑不变，直到 L590 score += source_value 之后：

    # --- NEW: vector similarity tier (additive, like source_value) ---
    if semantic and query_embedding_scores is not None:
        vec_sim = query_embedding_scores.get(nid, 0.0)
        if vec_sim > 0:
            score += _VECTOR_SIMILARITY_BONUS * w * vec_sim  # 加法，不参与 tier 互斥

    # --- NEW: fuzzy tier (only if lexical 3-tier all missed this token) ---
    if semantic and hybrid_scorer is not None and matched == 0:
        # 仅当 EXACT/PREFIX/SUBSTRING 都未命中时触发
        fuzzy_bonus = hybrid_scorer.fuzzy_score_for_node(t, label)
        if fuzzy_bonus > 0:
            score += fuzzy_bonus * w

    # L591: tiered += tier_value  # 既有逻辑不变
```

### 7.3 修改 `_query_graph_text`（加参数 + 准备 hybrid scorer + top_n 多结果）

```python
# serve.py:1187 — 修改签名
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
    terms = _query_terms(question)

    # NEW: prepare hybrid scoring
    query_embedding_scores = None
    hybrid_scorer = None
    if semantic:
        hybrid_scorer = G.graph.get("_hybrid_scorer")
        if hybrid_scorer and hybrid_scorer.available:
            query_embedding_scores = hybrid_scorer.vector_scores(question)

    qs = _score_query(
        G, terms,
        collect_per_term_seeds=True,
        query_embedding_scores=query_embedding_scores,  # 新增
        hybrid_scorer=hybrid_scorer,                     # 新增
        semantic=semantic,                               # 新增
    )

    # NEW: top_n 多结果返回逻辑
    ranked = qs.ranked
    if not ranked:
        return "No matching nodes found."

    resolved_filters, filter_source = _resolve_context_filters(question, context_filters)
    traversal_graph = _filter_graph_by_context(G, resolved_filters)

    # top_n=1（默认）：当前行为不变——单 seed → 单 BFS → 单子图
    if top_n <= 1:
        start_nodes = _pick_seeds(ranked, G=G, best_seed_by_term=best_seed_by_term, max_seeds=top_k)
        if not start_nodes:
            return "No matching nodes found."
        nodes, edges = _dfs(traversal_graph, start_nodes, depth) if mode == "dfs" else _bfs(traversal_graph, start_nodes, depth)
        # ... 既有 header 逻辑 ...
        return header + _subgraph_to_text(traversal_graph, nodes, edges, token_budget, seeds=start_nodes)

    # top_n>1：取 ranked 前 top_n 个种子，各自独立 BFS，返回多个子图
    top_seeds = [nid for nid, _score in ranked[:top_n]]
    per_result_budget = max(token_budget // top_n, 500)  # 均分预算，保底 500
    results = []
    for i, seed_nid in enumerate(top_seeds, 1):
        seed_nodes = [seed_nid]
        nodes, edges = _dfs(traversal_graph, seed_nodes, depth) if mode == "dfs" else _bfs(traversal_graph, seed_nodes, depth)
        sub_text = _subgraph_to_text(traversal_graph, nodes, edges, per_result_budget, seeds=seed_nodes)
        seed_label = G.nodes[seed_nid].get("label", seed_nid)
        seed_score = dict(ranked).get(seed_nid, 0.0)
        results.append(
            f"=== Result {i}/{top_n} (seed: {seed_label}, score: {seed_score:.2f}) ===\n{sub_text}"
        )
    return "\n\n".join(results)
```

### 7.4 修改 MCP `query_graph` schema（加字段）

```python
# serve.py:1582 — inputSchema 加字段
types.Tool(
    name="query_graph",
    description="Search the knowledge graph using BFS or DFS. Returns relevant nodes and edges as text context.",
    inputSchema={
        "type": "object",
        "properties": {
            "question": {"type": "string", "description": "Natural language question or keyword search"},
            "semantic": {"type": "boolean", "default": True,
                         "description": "Enable hybrid semantic+fuzzy retrieval (default true)"},
            "top_k": {"type": "integer", "default": 3,
                      "description": "Number of seed nodes to return before BFS expansion"},
            "top_n": {"type": "integer", "default": 1,
                      "description": "Number of independent subgraph results to return (default 1)"},
            "mode": {"type": "string", "enum": ["bfs", "dfs"], "default": "bfs"},
            "depth": {"type": "integer", "default": 3},
            "token_budget": {"type": "integer", "default": 2000},
            "context_filter": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["question"],
    },
),
```

### 7.5 修改 `_tool_query_graph`（透传参数）

```python
# serve.py:1730 — 从 arguments 取新参数
def _tool_query_graph(arguments: dict) -> str:
    question = arguments.get("question", "")
    mode = arguments.get("mode", "bfs")
    depth = arguments.get("depth", 3)
    token_budget = arguments.get("token_budget", 2000)
    context_filters = arguments.get("context_filter")
    semantic = arguments.get("semantic", True)      # 新增
    top_k = arguments.get("top_k", 3)                # 新增
    top_n = arguments.get("top_n", 1)                # 新增
    # ...
    result = _query_graph_text(
        G, question,
        mode=mode, depth=depth, token_budget=token_budget,
        context_filters=context_filters, graph_path=active_graph_path,
        semantic=semantic, top_k=top_k, top_n=top_n,  # 新增
    )
```

### 7.6 修改 CLI query 命令（加 `--no-semantic` / `--top-n` flag）

```python
# cli.py — query 命令的 argparse 加：
parser.add_argument("--no-semantic", action="store_true",
                    help="Disable hybrid semantic+fuzzy retrieval (pure lexical matching)")
parser.add_argument("--top-k", type=int, default=3,
                    help="Number of seed nodes before BFS expansion")
parser.add_argument("--top-n", type=int, default=1,
                    help="Number of independent subgraph results to return (default 1)")
# 调用时：
semantic = not args.no_semantic
result = _query_graph_text(G, question, semantic=semantic, top_k=args.top_k, top_n=args.top_n, ...)
```

---

## 8. 步骤 8：修改 `graphify/cli.py`（build-time embed 命令）

### 8.1 新增 `--embed-backend` flag

在 `graphify extract` 命令的 argparse 加：

```python
parser.add_argument("--embed-backend", default=None,
                    help="Generate embeddings after extraction (openai/gemini/ollama/kimi/deepseek/azure/bedrock)")
parser.add_argument("--embed-model", default=None,
                    help="Embedding model name (auto-detected per backend if omitted)")
```

### 8.2 extract 完成后触发 embedding 生成

```python
# cli.py — extract 命令处理末尾：
if args.embed_backend:
    from graphify.embeddings import generate_embeddings_for_graph
    graph_path = Path(".graph/graph.json")
    if graph_path.is_file():
        generate_embeddings_for_graph(graph_path, backend=args.embed_backend, model=args.embed_model)
        print(f"embeddings generated at .graph/embeddings/", file=sys.stderr)
```

---

## 9. 步骤 9：测试

### 9.1 新建 `tests/test_hybrid_search.py`

```python
# tests/test_hybrid_search.py
"""Tests for hybrid semantic + fuzzy search. Does not modify existing tests."""
import numpy as np
from pathlib import Path
from graphify.hybrid_scorer import HybridScorer
from graphify.fuzzy import fuzzy_score
from graphify.embeddings import cosine_similarity


def test_fuzzy_score_exact_match():
    assert fuzzy_score("UserService", "UserService") > 0.85


def test_fuzzy_score_typo():
    """UserServise (typo) should fuzzy-match UserService."""
    assert fuzzy_score("UserServise", "UserService") >= 0.85


def test_fuzzy_score_no_match():
    assert fuzzy_score("login", "authservice") < 0.85


def test_cosine_similarity():
    q = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    m = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.7, 0.7, 0.0]], dtype=np.float32)
    sims = cosine_similarity(q, m)
    assert sims[0] > 0.99   # identical
    assert sims[1] < 0.01   # orthogonal
    assert 0.6 < sims[2] < 0.8  # 45 degrees


def test_hybrid_scorer_no_sidecar(tmp_path: Path):
    """When no embedding sidecar exists, HybridScorer.available is False."""
    scorer = HybridScorer(tmp_path)
    assert not scorer.available
    assert scorer.vector_scores("test") is None


def test_score_query_pure_lexical_when_no_embeddings():
    """_score_query with semantic=True but no embeddings == pure lexical."""
    # ... build a small nx.Graph, call _score_query with semantic=True + no hybrid_scorer
    # ... assert result == same as semantic=False


def test_score_query_vector_tier_adds_bonus():
    """When query_embedding_scores provided, vector bonus added to matching nodes."""
    # ... build graph with "AuthService" node
    # ... provide query_embedding_scores = {"authservice": 0.9}
    # ... call _score_query with query "login" (no lexical overlap)
    # ... assert "authservice" gets non-zero score from vector tier


def test_score_query_fuzzy_tier_catches_typo():
    """Fuzzy tier matches 'UserServise' typo to 'UserService'."""
    # ... build graph with "UserService" node
    # ... call _score_query with query "UserServise" (no lexical exact/prefix/substring)
    # ... assert "UserService" gets non-zero score from fuzzy tier


def test_mcp_query_graph_semantic_param():
    """MCP query_graph tool accepts semantic parameter."""
    # ... call _tool_query_graph with arguments={"question": "auth", "semantic": False}
    # ... verify _query_graph_text called with semantic=False
```

### 9.2 新建 `tests/test_desc_extraction.py`

```python
# tests/test_desc_extraction.py
"""Tests for node desc field extraction."""
from graphify.desc import _extract_node_desc, _clean_desc


def test_clean_desc_strips_comment_markers():
    assert _clean_desc("# Validate user credentials") == "Validate user credentials"
    assert _clean_desc("/** Manages auth sessions */") == "Manages auth sessions"
    assert _clean_desc("/* Block comment */") == "Block comment"


def test_clean_desc_caps_length():
    long = "x" * 600
    assert len(_clean_desc(long)) == 512


def test_python_docstring_extraction():
    """Python function with docstring gets desc."""
    # ... parse a small .py file with tree-sitter, call _extract_node_desc
    # ... assert desc == "Validate user credentials against stored hash."


def test_jsdoc_extraction():
    """JS function with JSDoc gets desc."""
    # ... parse a small .js file, call _extract_node_desc
    # ... assert desc starts with "Manages authentication"


def test_no_docstring_returns_empty():
    """Function without docstring returns empty desc (fallback to label)."""
    # ... parse a function without any comments
    # ... assert _extract_node_desc returns ""
```

### 9.3 Benchmark fixture

```
tests/fixtures/search_benchmark/
├── graph.json           # 预构建的小图（含 code 节点 + doc 节点，节点含 desc 字段）
├── embeddings/          # 预生成的 embedding sidecar
└── queries.json         # 10 个 NL 问题 + 期望命中节点
```

```json
// queries.json
[
  {"query": "login", "expected": ["AuthService"]},
  {"query": "authentication", "expected": ["AuthService"]},
  {"query": "UserServise", "expected": ["UserService"]},
  {"query": "rate limiter", "expected": ["ThrottleService"]},
  {"query": "credential validation", "expected": ["verify_password"]}
]
```

### 9.4 top_n 多结果测试

```python
def test_query_top_n_returns_multiple_subgraphs():
    """top_n>1 returns multiple === Result N/M === separated subgraphs."""
    # ... build graph with multiple seed candidates
    # ... call _query_graph_text with top_n=3
    # ... assert result contains "=== Result 1/3 ===" and "=== Result 2/3 ==="


def test_query_top_n_default_is_one():
    """top_n=1 (default) returns single subgraph without separator."""
    # ... call _query_graph_text without top_n
    # ... assert "=== Result" NOT in result
```

---

## 10. 步骤 10：验证

### 10.1 单元测试

```bash
uv run pytest tests/test_hybrid_search.py tests/test_desc_extraction.py -q
```

### 10.2 集成测试

```bash
# 1. 构建图 + embedding（节点会自动携带 desc 字段）
uv run graphify extract tests/fixtures/search_benchmark/ --embed-backend openai

# 2. 混合模式查询（默认）
uv run graphify query "login" --top-k 5

# 3. 纯词法查询（对照）
uv run graphify query "login" --no-semantic --top-k 5

# 4. top_n 多结果查询
uv run graphify query "auth" --top-n 3

# 5. 对比召回
uv run python tests/fixtures/search_benchmark/run_benchmark.py
```

### 10.3 回 upstream 兼容性

```bash
# 删掉：desc.py / embeddings.py / fuzzy.py / hybrid_scorer.py / serve.py 的修改 / cli.py 的 flag / engine.py + markdown.py 的 desc 参数
# 跑既有测试：
uv run pytest tests/ -q
```

---

## 11. 回 upstream 策略

| 场景 | 操作 |
|---|---|
| graphify upstream 发版 | 保留 `desc.py` / `embeddings.py` / `fuzzy.py` / `hybrid_scorer.py` + serve.py 的加法 tier + cli.py 的 flag + engine.py/markdown.py 的 desc 字段；合并 upstream 其余改动。若 upstream 改了 `_score_query`，re-apply 加法 tier 到新版 L590 之后 |
| upstream 也加了语义检索 | 评估是否弃用自己的 hybrid_scorer，迁移到 upstream 机制；保留 desc 字段 + fuzzy.py 作为补充 |
| 完全回原始 graphify | 删 `desc.py` / `embeddings.py` / `fuzzy.py` / `hybrid_scorer.py` / `test_hybrid_search.py` / `test_desc_extraction.py` / serve.py 的修改 / cli.py 的 flag / engine.py + markdown.py 的 desc 参数 |

> **注意**：`desc` 字段是纯增量（新字段，不改变既有字段语义），即使回 upstream 也可以保留——它只是给节点多了个描述字段，不影响既有逻辑。

---

## 12. 实施顺序（推荐）

1. ✅ 步骤 1：`desc.py`（独立，可单测 docstring/comment 提取）
2. ✅ 步骤 2：`embeddings.py`（独立，可单测 cosine_similarity + `_node_embed_text`）
3. ✅ 步骤 3：`engine.py` 加 desc 参数 + 调用 `desc._extract_node_desc`（依赖步骤 1）
4. ✅ 步骤 4：`markdown.py` 加 desc 参数 + 正文首段提取
5. ✅ 步骤 5：`fuzzy.py`（独立，可单测 JaroWinkler）
6. ✅ 步骤 6：`hybrid_scorer.py`（依赖 2+5）
7. ✅ 步骤 7.1-7.2：serve.py 加载 sidecar + `_score_query` 加法 tier
8. ✅ 步骤 7.3-7.5：`_query_graph_text` + MCP schema + `_tool_query_graph` 加参数（含 top_n）
9. ✅ 步骤 7.6：cli.py query 命令加 `--no-semantic` / `--top-n` flag
10. ✅ 步骤 8：cli.py extract 命令加 `--embed-backend` flag
11. ✅ 步骤 9：测试 + benchmark（含 desc 提取测试 + top_n 测试）
12. ✅ 步骤 10：验证

---

## 13. 关键设计决策记录

| 决策 | 选择 | 理由 |
|---|---|---|
| vector tier 是替换还是加法 | **加法** | 精确查询时词法 EXACT x1000 仍主导；模糊查询时 vector 补偿 |
| embedding 文本源 | **仅 `desc`（fallback `label`）** | desc 承载语义（docstring/正文首段）；路径信息（nid/source_file）只走词法 tier，避免污染 cosine |
| norm_label 是否向量化 | **不向量化** | 代码符号名 camelCase 不拆词语义弱；文档文件名语义为零。有 desc 时不缺，无 desc 时作为 fallback 已足够 |
| 节点 desc 字段来源 | **代码：docstring/注释；文档：正文首段** | 统一的语义描述字段，让 embedding 能捕获符号名无法表达的语义（如 "Validate credentials"） |
| DDD doc-anchor 的 summary 字段 | **改名为 `desc`** | 与所有节点统一；避免维护两个字段 |
| embedding 生成时机 | **build-time** | 确定性、可复现、查询时无需 API key |
| embedding 存储 | **二进制 sidecar `.npy`** | 避免 graph.json 膨胀（384 float JSON 化每节点 4KB） |
| vector search 引擎 | **numpy brute-force** | 10k-100k 节点 sub-ms，无需 faiss 依赖 |
| fuzzy 触发条件 | **仅当词法 3 层全未命中** | 避免干扰精确匹配 |
| `semantic` 默认值 | **True** | 用户期望"混合检索"为默认行为 |
| `top_n` 默认值 | **1** | 默认行为与当前完全一致（单子图）；`>1` 时返回多个候选给 AI 选择 |
| 是否改 explain/path | **不改** | 这两个命令需要精确匹配语义，不适合 fuzzy |
| desc 长度上限 | **512 字符** | embedding model 通常 512 token 上下文；desc 是节点级摘要不应过长 |
| Anthropic 无 embedding API | **fallback 到 OpenAI/Ollama 或降级** | `GRAPHIFY_EMBED_BACKEND` 显式指定 |
