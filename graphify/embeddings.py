"""Embedding generation and storage for hybrid semantic search.

Build-time: generates per-node embeddings from ``desc`` (fallback ``label``),
stored as a binary sidecar under ``graphify-out/embeddings/``. Query-time:
loads the sidecar and embeds the query string for cosine similarity.

Decoupled from extract.py / llm.py — called as a post-build step (CLI
``--embed-backend``) and from serve.py at graph-load time. Text source: ONLY
the ``desc`` field. ``norm_label`` / ``nid`` / ``source_file`` are NOT
embedded — they stay in the lexical tier to avoid path-noise polluting the
cosine similarity.

Backends supported (all via the OpenAI SDK's ``embeddings.create``):
    openai / gemini / kimi / deepseek / ollama / azure
Anthropic Claude has no embedding API — pass an explicit ``--embed-backend``
that points at an embedding-capable provider, or the build silently degrades
to pure lexical at query time.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import numpy as np

# ---------------------------------------------------------------------------
# Node embed text: desc only (fallback to label)
# ---------------------------------------------------------------------------


def _node_embed_text(node: dict) -> str:
    """The sole embedding text source.

    ``desc`` carries the semantic content (docstring for code, first paragraph
    for docs). When desc is empty the label is used so every node still gets a
    vector — a label-only vector is a weak signal (code identifiers are
    camelCase symbols the embedding model does not split into words) but it
    keeps the matrix rectangular.

    ``norm_label`` / ``nid`` / ``source_file`` are deliberately excluded:
    path fragments pollute cosine similarity with directory-structure
    coincidence rather than semantic content, and those signals already have
    a dedicated lexical tier in ``_score_query``.
    """
    desc = node.get("desc", "")
    if desc:
        return desc
    return node.get("label", "")


# ---------------------------------------------------------------------------
# Model slug + sidecar paths
# ---------------------------------------------------------------------------


def _model_slug(model: str) -> str:
    """Normalize a model name to a filesystem-safe slug.

    ``text-embedding-3-small`` -> ``text_embedding_3_small``. Used as the
    sidecar filename stem so multiple models can coexist under
    ``graphify-out/embeddings/``.
    """
    return model.replace("/", "_").replace("-", "_").replace(".", "_").lower()


def _sidecar_paths(graph_dir: Path, model: str) -> dict[str, Path]:
    slug = _model_slug(model)
    base = graph_dir / "embeddings"
    return {
        "npy": base / f"{slug}.npy",
        "index": base / f"{slug}.index.json",
        "meta": base / f"{slug}.meta.json",
    }


# ---------------------------------------------------------------------------
# Backend config (mirrors llm.py BACKENDS for embedding-capable providers)
# ---------------------------------------------------------------------------


def _resolve_embed_backend_config(backend: str, model: str | None) -> tuple[str, str, str]:
    """Resolve (base_url, api_key, model) for an embedding backend.

    Configuration sources (later wins):
    1. Hardcoded per-backend defaults below.
    2. Backend-specific env vars (``OPENAI_BASE_URL`` etc.) — same as llm.py.
    3. **Unified embedding env vars** ``GRAPHIFY_EMBED_BASE_URL`` and
       ``GRAPHIFY_EMBED_API_KEY`` — let the user point any OpenAI-compatible
       endpoint at one place without learning each backend's env var name.
    4. ``.graphifyrc`` file keys (``embed_backend`` / ``embed_model`` /
       ``embed_base_url`` / ``embed_api_key``) — read by hybrid_scorer.py
       before this function is called, so the backend/model args already
       reflect the file when we get here.

    Raises ``ValueError`` for unknown backends or missing API keys (the
    caller surfaces this as a CLI error rather than silently degrading —
    silent degrade only happens at query time when no sidecar is present).

    The ``sentence-transformers`` backend is supported for **test/CI
    fixtures**: it does not call any API, so no API key is required and no
    network is touched. Production deployments should use ``openai`` /
    ``gemini`` / ``ollama`` / ``openai-compatible`` / etc.
    """
    backend = (backend or "").lower()
    if backend == "sentence-transformers":
        # Test/CI-only backend: no API, no key. The model name carries through
        # to the sidecar so cosine similarity is computed across a consistent
        # embedding space. Default is paraphrase-multilingual-MiniLM-L12-v2
        # (384-dim, 120MB, supports 50+ languages incl. Chinese-English
        # cross-lingual retrieval). all-MiniLM-L6-v2 is NOT used because it
        # fails on Chinese-English mixed queries (cosine ≈ 0).
        return "", "", model or "paraphrase-multilingual-MiniLM-L12-v2"
    if backend == "openai-compatible":
        # Generic OpenAI-compatible endpoint (vLLM / LM Studio / llama.cpp /
        # OpenRouter / any /v1/embeddings shim). The user MUST supply
        # GRAPHIFY_EMBED_BASE_URL and GRAPHIFY_EMBED_API_KEY (via env var or
        # .graphifyrc); there are no defaults because there is no canonical
        # endpoint. This is the recommended backend for self-hosted remote
        # embedding services that aren't Ollama.
        base_url = os.environ.get("GRAPHIFY_EMBED_BASE_URL", "")
        api_key = os.environ.get("GRAPHIFY_EMBED_API_KEY", "")
        if not base_url:
            raise ValueError(
                "openai-compatible backend requires GRAPHIFY_EMBED_BASE_URL "
                "(or embed_base_url in .graphifyrc). Set it to your /v1 endpoint."
            )
        if not api_key:
            raise ValueError(
                "openai-compatible backend requires GRAPHIFY_EMBED_API_KEY "
                "(or embed_api_key in .graphifyrc). Local servers accept any "
                "non-empty value."
            )
        # Model: explicit arg > GRAPHIFY_EMBED_MODEL env > "default" placeholder.
        # The user must name the model their endpoint serves — there is no
        # canonical default for a self-hosted endpoint.
        model = model or os.environ.get("GRAPHIFY_EMBED_MODEL", "") or "default"
        return base_url, api_key, model
    if backend == "openai":
        base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        api_key = os.environ.get("OPENAI_API_KEY", "")
        model = model or "text-embedding-3-small"
    elif backend == "gemini":
        base_url = os.environ.get(
            "GEMINI_BASE_URL",
            "https://generativelanguage.googleapis.com/v1beta/openai/",
        )
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")
        model = model or "text-embedding-004"
    elif backend == "kimi":
        base_url = os.environ.get("KIMI_BASE_URL", "https://api.moonshot.ai/v1")
        api_key = os.environ.get("MOONSHOT_API_KEY", "")
        model = model or "embedding-2"
    elif backend == "deepseek":
        # DeepSeek has no public embedding endpoint as of 2025-Q4 — route to
        # OpenAI-compatible base URL and let the user override the model.
        base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        model = model or "deepseek-embed"
    elif backend == "ollama":
        # Ollama exposes embeddings at /api/embeddings but the OpenAI-compat
        # /v1/embeddings shim also works and reuses the same SDK path.
        base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        api_key = os.environ.get("OLLAMA_API_KEY", "ollama")  # ollama accepts any non-empty key
        model = model or os.environ.get("OLLAMA_MODEL", "nomic-embed-text")
    elif backend == "azure":
        base_url = os.environ.get("AZURE_OPENAI_ENDPOINT", "").rstrip("/")
        api_key = os.environ.get("AZURE_OPENAI_API_KEY", "")
        model = model or os.environ.get("AZURE_OPENAI_DEPLOYMENT") or os.environ.get(
            "GRAPHIFY_AZURE_MODEL", "text-embedding-3-small"
        )
        # Azure needs /openai/deployments/<deployment>/embeddings on its base URL.
        # If the user gave a bare endpoint, append the standard path.
        if base_url and "/openai/deployments/" not in base_url:
            base_url = f"{base_url}/openai/deployments/{model}/embeddings"
        # Azure uses api-version query param; the SDK passes it via extra_body.
    else:
        raise ValueError(
            f"Unknown embedding backend {backend!r}. "
            "Supported: openai/openai-compatible/gemini/kimi/deepseek/ollama/azure/sentence-transformers. "
            "Anthropic Claude has no embedding API — use a different backend."
        )
    # Unified override: GRAPHIFY_EMBED_BASE_URL / GRAPHIFY_EMBED_API_KEY win
    # over any backend-specific env var. Lets the user repoint e.g. an
    # `openai` backend at a self-hosted OpenAI-compatible endpoint without
    # setting OPENAI_BASE_URL (which would also affect extraction backends).
    base_url = os.environ.get("GRAPHIFY_EMBED_BASE_URL") or base_url
    api_key = os.environ.get("GRAPHIFY_EMBED_API_KEY") or api_key
    if not api_key and backend not in ("ollama",):
        # Local Ollama accepts any non-empty key; everything else needs a real one.
        raise ValueError(
            f"No API key set for embedding backend {backend!r}. "
            f"Set GRAPHIFY_EMBED_API_KEY (or the backend-specific env var), "
            f"or use the .graphifyrc file with embed_api_key=..."
        )
    return base_url, api_key, model


# ---------------------------------------------------------------------------
# Batch embedding (backend-agnostic)
# ---------------------------------------------------------------------------

_EMBED_BATCH_SIZE = 100  # OpenAI /v1/embeddings accepts up to 2048 inputs; 100 is a safe batch


def _embed_batch_sentence_transformers(
    texts: list[str], model: str | None
) -> tuple[np.ndarray, str]:
    """Embed texts with a local SentenceTransformer model. Test/CI only.

    No API call, no network — the model is loaded once and cached on this
    function object so repeated ``embed_query`` calls (e.g. in a benchmark
    loop) don't reload it. Production deployments use the OpenAI-compatible
    backends (openai/gemini/ollama/etc.) via ``_embed_batch``.

    Raises ``ImportError`` if ``sentence_transformers`` isn't installed;
    falls back to ``paraphrase-multilingual-MiniLM-L12-v2`` (384-dim,
    ~120MB) when ``model`` is unset. This model supports 50+ languages
    including Chinese-English cross-lingual retrieval — verified on real
    code-corpus queries (中文 query vs English JSDoc desc = 0.58-0.66
    cosine, unrelated nodes 0.31, 7/7 retrieval accuracy). The older
    ``all-MiniLM-L6-v2`` is NOT used because it fails on Chinese-English
    mixed queries (cosine ≈ 0).
    """
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise ImportError(
            "sentence-transformers backend requires the 'sentence-transformers' package. "
            "Install with: pip install sentence-transformers"
        ) from exc

    model_name = model or "paraphrase-multilingual-MiniLM-L12-v2"
    # Cache the loaded model on the function object — SentenceTransformer
    # loading is ~1s and the benchmark loop calls embed_query per question.
    cached = getattr(_embed_batch_sentence_transformers, "_model", None)
    if cached is None or cached[0] != model_name:
        st_model = SentenceTransformer(model_name)
        _embed_batch_sentence_transformers._model = (model_name, st_model)  # type: ignore[attr-defined]
    else:
        st_model = cached[1]

    sanitized = [(t or " ").strip() or " " for t in texts]
    embeddings = st_model.encode(sanitized, convert_to_numpy=True, show_progress_bar=False)
    return np.asarray(embeddings, dtype=np.float32), model_name


def _embed_batch(
    texts: list[str], *, backend: str, model: str | None = None
) -> tuple[np.ndarray, str]:
    """Embed a batch of texts. Returns (embeddings (N, D) float32, actual_model).

    Uses the OpenAI SDK's ``embeddings.create`` against the configured
    backend's base_url for online backends (openai/gemini/kimi/deepseek/
    ollama/azure). For the ``sentence-transformers`` backend (test/CI only),
    uses the local SentenceTransformer model — no API call, no network.

    Batches in chunks of ``_EMBED_BATCH_SIZE`` to stay under provider input
    limits. Empty / whitespace-only texts are replaced with a single space
    so the API does not reject them (the resulting vector is meaningless but
    keeps the matrix rectangular).
    """
    backend_lower = (backend or "").lower()
    # Test/CI-only path: local SentenceTransformer, no API. The model is
    # loaded once and cached on the function object so repeated query-time
    # embed_query calls don't reload it.
    if backend_lower == "sentence-transformers":
        return _embed_batch_sentence_transformers(texts, model)

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ImportError(
            "embedding requires the 'openai' package. "
            "Install with: uv tool install 'graphifyy[openai]'"
        ) from exc

    base_url, api_key, actual_model = _resolve_embed_backend_config(backend, model)
    client = OpenAI(api_key=api_key, base_url=base_url)

    # Sanitize: empty strings would 400 from most providers.
    sanitized = [(t or " ").strip() or " " for t in texts]

    out_rows: list[list[float]] = []
    for i in range(0, len(sanitized), _EMBED_BATCH_SIZE):
        chunk = sanitized[i : i + _EMBED_BATCH_SIZE]
        resp = client.embeddings.create(model=actual_model, input=chunk)
        for datum in resp.data:
            out_rows.append(list(datum.embedding))

    if not out_rows:
        raise ValueError("embedding API returned no vectors")
    matrix = np.asarray(out_rows, dtype=np.float32)
    return matrix, actual_model


# ---------------------------------------------------------------------------
# Build-time: generate embeddings for all graph nodes
# ---------------------------------------------------------------------------


def generate_embeddings_for_graph(
    graph_json_path: Path, *, backend: str | None = None, model: str | None = None
) -> Path | None:
    """Generate embeddings for all nodes in ``graph.json``. Writes sidecar files.

    Text source: ONLY ``desc`` (fallback ``label``). See ``_node_embed_text``.
    Returns the path to the written ``.npy`` file, or ``None`` when no embedding
    backend is configured (default + project config + env all empty = skip).

    When ``backend`` is ``None`` (the default — ``graphify .`` / ``graphify
    extract .`` without ``--embed-backend``), the function auto-detects the
    backend from the same resolution chain as query-time
    (``graphify/.default-graphifyrc`` -> ``.graph/graphifyrc`` -> env vars ->
    extraction-backend env auto-detect). When that chain resolves to nothing,
    embedding generation is silently skipped — the graph is still valid, and
    queries will run in pure-lexical mode until a backend is configured.

    Raises ``ValueError`` if the graph has no nodes or the backend is
    misconfigured (e.g. ``openai-compatible`` without ``embed_base_url``).
    """
    # Auto-resolve backend when not explicitly passed. This makes embedding
    # generation default-on for `graphify .` / `graphify extract .` — the
    # only skip case is "no backend configured anywhere", which is the
    # correct behavior for an environment with no embedding endpoint.
    if backend is None:
        from graphify.hybrid_scorer import _embed_backend_from_env
        backend = _embed_backend_from_env()
        if backend is None:
            # Nothing configured — skip silently rather than crash. The graph
            # is still valid; queries degrade to pure lexical automatically.
            return None
        # Also auto-resolve model from the same config chain when unset.
        if model is None:
            from graphify.hybrid_scorer import _embed_model_from_env
            model = _embed_model_from_env()

    graph_dir = graph_json_path.parent
    data = json.loads(graph_json_path.read_text(encoding="utf-8"))
    nodes = data.get("nodes", [])
    if not nodes:
        raise ValueError("graph has no nodes to embed")

    texts = [_node_embed_text(n) for n in nodes]
    embeddings, actual_model = _embed_batch(texts, backend=backend, model=model)

    paths = _sidecar_paths(graph_dir, actual_model)
    paths["npy"].parent.mkdir(parents=True, exist_ok=True)

    # Save .npy (float32, shape (N, D))
    np.save(paths["npy"], embeddings)

    # Save .index.json (node_id -> row index)
    index = {n["id"]: i for i, n in enumerate(nodes)}
    paths["index"].write_text(
        json.dumps(
            {
                "node_ids": list(index.keys()),
                "model": actual_model,
                "dim": int(embeddings.shape[1]),
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    # Save .meta.json
    paths["meta"].write_text(
        json.dumps(
            {
                "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
                "node_count": len(nodes),
                "dim": int(embeddings.shape[1]),
                "model": actual_model,
                "backend": backend,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return paths["npy"]


# ---------------------------------------------------------------------------
# Query-time: load sidecar + embed query
# ---------------------------------------------------------------------------


def load_embedding_sidecar(
    graph_dir: Path,
) -> tuple[np.ndarray, dict[str, int], str] | None:
    """Load the most recent embedding sidecar in ``graph_dir/embeddings/``.

    Returns ``(matrix, id_to_row, model)`` or ``None`` when no sidecar is
    present (the caller falls back to pure lexical scoring in that case).
    When multiple models have been generated, picks the newest by mtime.
    """
    emb_dir = graph_dir / "embeddings"
    if not emb_dir.is_dir():
        return None
    npy_files = sorted(
        emb_dir.glob("*.npy"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    if not npy_files:
        return None
    npy_path = npy_files[0]
    slug = npy_path.stem
    index_path = emb_dir / f"{slug}.index.json"
    if not index_path.is_file():
        return None
    matrix = np.load(npy_path)
    if matrix.ndim != 2:
        # Defensive: a malformed sidecar should not crash query path
        return None
    index_data = json.loads(index_path.read_text(encoding="utf-8"))
    node_ids = index_data.get("node_ids", [])
    id_to_row = {nid: i for i, nid in enumerate(node_ids)}
    return matrix, id_to_row, index_data.get("model", "")


def embed_query(
    query: str,
    *,
    backend: str,
    model: str,
    cache: dict[str, np.ndarray] | None = None,
) -> np.ndarray | None:
    """Embed a query string. Returns ``None`` on failure (caller degrades).

    Uses an LRU cache when provided so a repeated query does not re-call the
    API. The cache is a plain dict (caller caps its size); the query string
    is the cache key.
    """
    if cache is not None and query in cache:
        return cache[query]
    try:
        vec, _ = _embed_batch([query], backend=backend, model=model)
    except Exception:
        return None
    if vec is None or len(vec) == 0:
        return None
    if cache is not None:
        cache[query] = vec[0]
    return vec[0]


# ---------------------------------------------------------------------------
# Cosine similarity (numpy brute-force)
# ---------------------------------------------------------------------------


def cosine_similarity(query_vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """Cosine similarity of ``query_vec`` against each row of ``matrix``.

    Returns an ``(N,)`` float32 array. Both sides are L2-normalised first;
    a small epsilon guards against zero-vector division. Brute-force dot
    product is sub-millisecond for 10k-100k nodes — faiss is unnecessary at
    graphify's scale (the spec caps the non-goal at 500k nodes).
    """
    q_norm = query_vec / (np.linalg.norm(query_vec) + 1e-8)
    m_norm = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-8)
    return (m_norm @ q_norm).astype(np.float32, copy=False)
