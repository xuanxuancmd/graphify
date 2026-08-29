"""Embedding generation and storage for hybrid semantic search.

Build-time: generates per-node embeddings from ``desc`` (fallback ``label``),
stored as a binary sidecar under ``.graph/embeddings/``. Query-time:
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


def _sidecar_paths(graph_dir: Path, model: str) -> dict[str, Path]:
    """Paths for the embedding sidecar files.

    Uses fixed, generic filenames so the sidecar is a stable contract:
    ``.graph/embeddings/embedding.npy``, ``embedding.index.json``,
    ``embedding.meta.json``. The actual model name is stored inside
    ``embedding.meta.json`` (and ``embedding.index.json``) for anyone who
    needs to know which model produced the vectors — but the filename
    itself is always ``embedding.*``, so downstream readers (HybridScorer,
    query path, tests) never need to glob or guess the slug.
    """
    base = graph_dir / "embeddings"
    return {
        "npy": base / "embedding.npy",
        "index": base / "embedding.index.json",
        "meta": base / "embedding.meta.json",
    }


# ---------------------------------------------------------------------------
# Backend config (mirrors llm.py BACKENDS for embedding-capable providers)
# ---------------------------------------------------------------------------


def _resolve_embed_backend_config(
    backend: str, model: str | None, graph_dir: "str | Path | None" = None
) -> tuple[str, str, str]:
    """Resolve (base_url, api_key, model) for an embedding backend.

    Configuration is read ONLY from config files (no environment variables):
      1. ``.default-graphifyrc`` shipped with the package (base defaults)
      2. ``.graph/graphifyrc`` in the project (overrides per-key)

    The four ``embed_*`` keys recognized there:
      embed_backend  — selects the backend (handled by the caller)
      embed_base_url — OpenAI-compatible endpoint URL (for openai-compatible,
                       or to override any backend's default base_url)
      embed_api_key  — API key for the backend
      embed_model    — model name override

    The ``enable_embedding_proxy`` key (default false) is NOT read here — it
    is consumed directly in ``_embed_batch`` to decide whether the OpenAI
    SDK client bypasses system/env proxies (``trust_env=False``, the default)
    or uses the SDK default (``trust_env=True``) when the embedding endpoint
    requires a proxy.

    ``graph_dir`` is the directory containing graph.json — pass it so the
    config lookup finds the right project's ``.graph/graphifyrc``. When
    None, falls back to CWD (less reliable — prefer passing graph_dir).

    Environment variables (GRAPHIFY_EMBED_* / OPENAI_API_KEY etc.) are NOT
    read — use the config file instead. This avoids "works on my machine"
    issues where env vars are set in one shell session but not visible to
    the python subprocess that actually runs the extract.

    Raises ``ValueError`` for unknown backends or missing API keys.
    """
    # Read config files (default + project). Pass graph_dir so the lookup
    # finds .graph/graphifyrc next to this graph.json.
    from graphify.hybrid_scorer import _load_embed_config_from_graphifyrc
    rc_cfg = _load_embed_config_from_graphifyrc(graph_dir)
    rc_base_url = rc_cfg.get("embed_base_url", "").strip()
    rc_api_key = rc_cfg.get("embed_api_key", "").strip()
    rc_model = rc_cfg.get("embed_model", "").strip()

    backend = (backend or "").lower()
    if backend == "sentence-transformers":
        # Local PyTorch CPU model for test/CI. No API, no key. Default is
        # paraphrase-multilingual-MiniLM-L12-v2 (384-dim, 120MB, 50+ languages
        # incl. Chinese-English cross-lingual). all-MiniLM-L6-v2 NOT used —
        # it fails on Chinese-English mixed queries (cosine ≈ 0).
        return "", "", model or rc_model or "paraphrase-multilingual-MiniLM-L12-v2"
    if backend == "openai-compatible":
        # Generic OpenAI-compatible endpoint (vLLM / LM Studio / llama.cpp /
        # OpenRouter / any /v1/embeddings shim). The user MUST supply
        # embed_base_url and embed_api_key in .graph/graphifyrc; there are no
        # defaults because there is no canonical endpoint.
        base_url = rc_base_url
        api_key = rc_api_key
        if not base_url:
            raise ValueError(
                "openai-compatible backend requires embed_base_url in "
                ".graph/graphifyrc. Set it to your /v1 endpoint."
            )
        if not api_key:
            raise ValueError(
                "openai-compatible backend requires embed_api_key in "
                ".graph/graphifyrc. Local servers accept any non-empty value."
            )
        return base_url, api_key, model or rc_model or "default"
    if backend == "openai":
        base_url = rc_base_url or "https://api.openai.com/v1"
        api_key = rc_api_key
        model = model or rc_model or "text-embedding-3-small"
    elif backend == "gemini":
        base_url = rc_base_url or "https://generativelanguage.googleapis.com/v1beta/openai/"
        api_key = rc_api_key
        model = model or rc_model or "text-embedding-004"
    elif backend == "kimi":
        base_url = rc_base_url or "https://api.moonshot.ai/v1"
        api_key = rc_api_key
        model = model or rc_model or "embedding-2"
    elif backend == "deepseek":
        base_url = rc_base_url or "https://api.deepseek.com"
        api_key = rc_api_key
        model = model or rc_model or "deepseek-embed"
    elif backend == "ollama":
        base_url = rc_base_url or "http://localhost:11434/v1"
        api_key = rc_api_key or "ollama"  # ollama accepts any non-empty key
        model = model or rc_model or "nomic-embed-text"
    elif backend == "azure":
        base_url = (rc_base_url or "").rstrip("/")
        api_key = rc_api_key
        model = model or rc_model or "text-embedding-3-small"
        if base_url and "/openai/deployments/" not in base_url:
            base_url = f"{base_url}/openai/deployments/{model}/embeddings"
    else:
        raise ValueError(
            f"Unknown embedding backend {backend!r}. "
            "Supported: openai/openai-compatible/gemini/kimi/deepseek/ollama/azure/sentence-transformers. "
            "Anthropic Claude has no embedding API — use a different backend."
        )
    if not api_key and backend not in ("ollama",):
        raise ValueError(
            f"No embed_api_key set for embedding backend {backend!r} in "
            f".graph/graphifyrc. Set embed_api_key=... in the config file."
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


def _build_embed_http_client():
    """Build an httpx client with ``trust_env=False`` (direct connect, no proxy).

    This is the default for embedding requests. ``trust_env=False`` makes
    httpx ignore BOTH environment-variable proxies (``HTTP_PROXY`` etc.) AND
    the Windows system proxy registry (``ProxyEnable``/``ProxyServer``). This
    is necessary because httpx silently drops the Windows bypass list
    (``ProxyOverride`` — the "不代理"/"代码黑名单" entries) due to a
    CPython + httpx interaction: ``getproxies_registry()`` does not reliably
    expose ``ProxyOverride`` as the ``no`` key (cpython#149136), and httpx
    never calls ``proxy_bypass()`` per-host (httpx#1536). The result is that
    embedding requests to a directly-reachable endpoint get routed through
    a proxy that cannot reach it, causing spurious connection failures on
    Windows. The same fix applies to WSL, where env-var proxies
    (``HTTPS_PROXY`` pointing at the Windows host's Clash/V2Ray) cause the
    same misrouting.

    Set ``enable_embedding_proxy = true`` in ``.graph/graphifyrc`` to restore
    the OpenAI SDK default (``trust_env=True``) when the embedding endpoint
    genuinely requires a proxy.

    Uses the SDK's ``DefaultHttpxClient`` (preserves default timeout/limits/
    follow_redirects) when available, falling back to ``DefaultHttpx2Client``
    (newer SDK that aliases httpx as httpx2), and finally to a plain
    ``httpx.Client`` on SDK versions without either wrapper.
    """
    try:
        from openai import DefaultHttpxClient
    except ImportError:
        try:
            from openai import DefaultHttpx2Client as DefaultHttpxClient
        except ImportError:
            import httpx
            return httpx.Client(trust_env=False)
    return DefaultHttpxClient(trust_env=False)


def _embed_batch(
    texts: list[str], *, backend: str, model: str | None = None,
    graph_dir: "str | Path | None" = None,
) -> tuple[np.ndarray, str]:
    """Embed a batch of texts. Returns (embeddings (N, D) float32, actual_model).

    Uses the OpenAI SDK's ``embeddings.create`` against the configured
    backend's base_url for online backends (openai/gemini/kimi/deepseek/
    ollama/azure). For the ``sentence-transformers`` backend (test/CI only),
    uses the local SentenceTransformer model — no API call, no network.

    ``graph_dir`` is passed to ``_resolve_embed_backend_config`` so it can
    find ``.graph/graphifyrc`` for embed_base_url / embed_api_key. When
    None, falls back to CWD (less reliable).

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

    base_url, api_key, actual_model = _resolve_embed_backend_config(backend, model, graph_dir)

    # Proxy control. Default: OFF — embedding requests connect directly to
    # embed_base_url, bypassing both env-var proxies (HTTP_PROXY etc.) and
    # the Windows system proxy. See _build_embed_http_client for the full
    # rationale (Windows ProxyOverride bypass-list bug, WSL env-var proxies).
    # Set ``enable_embedding_proxy = true`` in .graph/graphifyrc to restore
    # the SDK default (trust_env=True) when the endpoint requires a proxy.
    from graphify.hybrid_scorer import _load_embed_config_from_graphifyrc
    rc_cfg = _load_embed_config_from_graphifyrc(graph_dir)
    enable_proxy = (
        rc_cfg.get("enable_embedding_proxy", "").strip().lower()
        in ("true", "1", "yes", "on")
    )
    http_client = None if enable_proxy else _build_embed_http_client()

    client = OpenAI(api_key=api_key, base_url=base_url, http_client=http_client)

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
        from graphify.hybrid_scorer import _load_embed_config_from_graphifyrc
        # Pass graph_dir so the config lookup finds .graph/graphifyrc next
        # to this graph.json. Without graph_dir the lookup falls back to CWD
        # and misses the project config — the "env var set but no effect" bug.
        rc_cfg = _load_embed_config_from_graphifyrc(graph_json_path.parent)
        backend = rc_cfg.get("embed_backend", "").strip().lower() or None
        if backend is None:
            # Nothing configured — skip silently rather than crash. The graph
            # is still valid; queries degrade to pure lexical automatically.
            return None
        # Also auto-resolve model from the same config.
        if model is None:
            model = rc_cfg.get("embed_model", "").strip() or None

    graph_dir = graph_json_path.parent
    data = json.loads(graph_json_path.read_text(encoding="utf-8"))
    nodes = data.get("nodes", [])
    if not nodes:
        raise ValueError("graph has no nodes to embed")

    texts = [_node_embed_text(n) for n in nodes]
    embeddings, actual_model = _embed_batch(texts, backend=backend, model=model,
                                            graph_dir=graph_json_path.parent)

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


def generate_embedding_sidecar(
    graph_json_path: Path,
    *,
    embed_backend: str | None = None,
    embed_model: str | None = None,
    log_prefix: str = "[graphify]",
) -> None:
    """Generate (or skip) the embedding sidecar after a successful graph build.

    This is the single shared entry point called by every code path that
    finishes a graph.json — cli.py's extract command AND watch.py's
    _rebuild_code (the git post-commit hook path). Keeping the call in one
    place avoids the two paths drifting: a desc change picked up by either
    the full `graphify .` extract or the incremental hook rebuild produces
    a refreshed sidecar.

    Default-on via config: when ``embed_backend`` is None (the common case
    — ``graphify .`` / ``graphify extract .`` / git commit hook all pass
    None), the backend is auto-detected from .default-graphifyrc,
    .graph/graphifyrc, and env vars. When nothing is configured,
    `generate_embeddings_for_graph` returns None silently — the graph is
    still valid, queries degrade to pure lexical. The config-file chain is
    the sole switch: configured = generate, unconfigured = skip.

    ``log_prefix`` labels the stderr output so the caller can identify
    which path produced the sidecar (e.g. ``[graphify extract]`` vs
    ``[graphify watch]``).

    Reads every node's `desc` field (fallback `label`) and writes
    ``<graph_dir>/embeddings/<model_slug>.{npy,index.json,meta.json}``.
    A failure here is a warning, not fatal — the graph is the primary
    artifact.
    """
    import sys
    try:
        _emb_path = generate_embeddings_for_graph(
            graph_json_path, backend=embed_backend, model=embed_model
        )
        if _emb_path is not None:
            print(
                f"{log_prefix} wrote embeddings: "
                f"{_emb_path.relative_to(graph_json_path.parent)}",
                file=sys.stderr,
            )
        # else: no backend configured -> silently skipped, no message
    except Exception as exc:
        print(
            f"{log_prefix} warning: embedding generation failed "
            f"(queries will run in pure-lexical mode until fixed): {exc}",
            file=sys.stderr,
        )


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
