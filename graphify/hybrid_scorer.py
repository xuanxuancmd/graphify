"""Hybrid scorer: vector similarity + fuzzy matching tiers.

Called by serve.py's ``_score_query`` as an ADDITIVE bonus on top of the
existing 3-tier lexical scoring (EXACT/PREFIX/SUBSTRING). Does NOT replace
the lexical tiers — the vector and fuzzy bonuses are added on top so a
precise query stays EXACT-dominated and a fuzzy/semantic query gets
rescued from a 0 lexical score.

Bonus constants (see spec §4.1):
    _VECTOR_SIMILARITY_BONUS = 5.0   (between SUBSTRING=1 and PREFIX=100)
    _FUZZY_MATCH_BONUS       = 2.0   (above SUBSTRING=1, below VECTOR=5)

The vector tier is computed in one numpy matrix multiply over the whole
graph (sub-ms for 10k nodes); the fuzzy tier is computed per
(token, node_label) pair inside the existing ``_score_query`` per-node loop,
but only when this token missed all three lexical tiers on that node so it
never disturbs a precise match.
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np

from graphify.embeddings import (
    cosine_similarity,
    embed_query,
    load_embedding_sidecar,
)
from graphify.fuzzy import fuzzy_score

_VECTOR_SIMILARITY_BONUS = 5.0
_FUZZY_MATCH_BONUS = 2.0


def _load_embed_config_from_graphifyrc(graph_dir: "str | Path | None" = None) -> dict[str, str]:
    """Read embedding config keys from the project ``graphifyrc``.

    graphify writes graph.json under ``<project>/.graph/`` (default, or
    ``graphify-out/`` when GRAPHIFY_OUT is overridden). The per-project
    config file ``graphifyrc`` lives IN that output dir — same place as
    graph.json — so embedding settings travel with the graph and aren't
    scattered at the repo root. A shipped ``.default-graphifyrc`` next to
    the graphify package provides out-of-the-box defaults (loaded first,
    overridden per-key by the project file).

    Four embedding keys are recognized:
        embed_backend=openai-compatible
        embed_base_url=http://localhost:8080/v1
        embed_api_key=sk-...
        embed_model=text-embedding-3-small

    ``graph_dir`` is the directory containing graph.json (typically
    ``.graph/``). When None, falls back to ``GRAPHIFY_OUT_DIR`` env or CWD.
    Returns an empty dict when no config is found on either layer.
    """
    try:
        from graphify.hooks import _load_graphifyrc, _project_graphifyrc_path
    except ImportError:
        return {}
    from pathlib import Path
    # Resolve the project root: graph_dir is the output dir (.graph/),
    # so the project root is its parent. _load_graphifyrc(root) reads
    # <root>/<GRAPHIFY_OUT>/graphifyrc, which is exactly graph_dir/graphifyrc.
    if graph_dir is not None:
        root = Path(graph_dir).resolve().parent
    else:
        root = Path(os.environ.get("GRAPHIFY_OUT_DIR", ".")).resolve()
    cfg = _load_graphifyrc(root)
    # Extract only the embed_* keys (others like viz_node_limit are not
    # relevant here).
    return {k: str(v) for k, v in cfg.items() if k.startswith("embed_")}


def _embed_backend_from_env() -> str | None:
    """Pick the embedding backend from config file or env.

    Priority (later wins):
    1. Auto-detect from extraction backend env vars (OPENAI_API_KEY etc.)
    2. ``GRAPHIFY_EMBED_BACKEND`` env var
    3. ``embed_backend`` key in ``.graph/graphifyrc`` (highest)

    Returns ``None`` when nothing usable is configured — the sole "skip"
    signal. When None, embedding generation is silently skipped at build
    time and queries degrade to pure lexical at query time. This is the
    intended behavior for an environment with no embedding endpoint: the
    graph is the primary artifact, embedding is an optional enhancement.
    """
    rc_cfg = _load_embed_config_from_graphifyrc()
    # 1. .graphifyrc file (highest priority)
    rc_backend = rc_cfg.get("embed_backend", "").strip().lower()
    if rc_backend:
        return rc_backend
    # 2. Explicit env var
    explicit = os.environ.get("GRAPHIFY_EMBED_BACKEND", "").strip().lower()
    if explicit:
        return explicit
    # 3. Auto-detect from extraction backend env vars
    for var, backend in (
        ("OPENAI_API_KEY", "openai"),
        ("GEMINI_API_KEY", "gemini"),
        ("GOOGLE_API_KEY", "gemini"),
        ("MOONSHOT_API_KEY", "kimi"),
        ("DEEPSEEK_API_KEY", "deepseek"),
        ("AZURE_OPENAI_API_KEY", "azure"),
        ("OLLAMA_BASE_URL", "ollama"),
    ):
        if os.environ.get(var, "").strip():
            return backend
    return None


def _embed_model_from_env() -> str | None:
    """Embedding model name from ``.graphifyrc`` or env. Backend defaults apply if unset."""
    rc_cfg = _load_embed_config_from_graphifyrc()
    rc_model = rc_cfg.get("embed_model", "").strip()
    if rc_model:
        return rc_model
    return os.environ.get("GRAPHIFY_EMBED_MODEL", "").strip() or None


class HybridScorer:
    """Holds loaded embedding matrix + query embedding cache.

    One instance per loaded graph, attached to ``G.graph['_hybrid_scorer']``
    by ``_GraphContextCache._load_entry`` (mirroring how ``_trigram_index``
    is warmed). When no sidecar exists, ``available`` is False and every
    method returns ``None`` — ``_score_query`` then runs in pure-lexical mode.
    """

    def __init__(
        self,
        graph_dir: str | Path | None = None,
        *,
        embed_backend: str | None = None,
        embed_model: str | None = None,
    ) -> None:
        self._matrix: np.ndarray | None = None
        self._id_to_row: dict[str, int] | None = None
        self._model: str = ""
        self._query_cache: dict[str, np.ndarray] = {}
        # Load .graph/graphifyrc config so embed_base_url/embed_api_key land
        # in env before _resolve_embed_backend_config reads them. This lets
        # the user configure any OpenAI-compatible endpoint in a file without
        # env vars. Pass graph_dir so the config lookup targets the right
        # project's .graph/ dir (not just CWD).
        rc_cfg = _load_embed_config_from_graphifyrc(graph_dir)
        if rc_cfg.get("embed_base_url"):
            os.environ.setdefault("GRAPHIFY_EMBED_BASE_URL", rc_cfg["embed_base_url"])
        if rc_cfg.get("embed_api_key"):
            os.environ.setdefault("GRAPHIFY_EMBED_API_KEY", rc_cfg["embed_api_key"])
        # Backend: explicit arg > .graph/graphifyrc embed_backend > env auto-detect.
        # The rc_cfg embed_backend comes from the project's .graph/graphifyrc
        # merged over the shipped default, so it already reflects both layers.
        self._embed_backend = (
            embed_backend
            or rc_cfg.get("embed_backend", "").strip().lower()
            or None
            or _embed_backend_from_env()
        )
        # Model: explicit arg > .graph/graphifyrc embed_model > env
        self._embed_model = (
            embed_model
            or rc_cfg.get("embed_model", "").strip()
            or None
            or _embed_model_from_env()
        )
        if graph_dir is not None:
            self._load(Path(graph_dir))

    def _load(self, graph_dir: Path) -> None:
        result = load_embedding_sidecar(graph_dir)
        if result is not None:
            self._matrix, self._id_to_row, self._model = result

    @property
    def available(self) -> bool:
        """True iff the embedding sidecar loaded AND a backend is configured."""
        return (
            self._matrix is not None
            and self._id_to_row is not None
            and bool(self._embed_backend)
        )

    def vector_scores(self, query: str) -> dict[str, float] | None:
        """Return ``{node_id: cosine_sim}`` for all nodes, or ``None`` if unavailable.

        The dict covers every node id in the sidecar — including nodes that
        the trigram prefilter would have excluded — so the vector tier can
        surface ``login`` -> ``AuthService`` even when the two share zero
        lexical trigrams. The caller merges these into the existing scored
        list as an additive bonus.
        """
        if not self.available:
            return None
        assert self._matrix is not None and self._id_to_row is not None
        assert self._embed_backend is not None
        # The model used at query time should match the one used at build time
        # for cosine similarity to be meaningful; the sidecar carries the build
        # model name, so reuse it unless an explicit override was set.
        model = self._embed_model or self._model or None
        q_vec = embed_query(
            query,
            backend=self._embed_backend,
            model=model,
            cache=self._query_cache,
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
        """Return the fuzzy bonus for a (query_token, node_label) pair.

        Returns 0.0 when the pair is below the JaroWinkler threshold, so the
        caller's ``if fuzzy_bonus > 0`` gate stays simple. The bonus already
        includes the ``_FUZZY_MATCH_BONUS`` multiplier — the caller adds it
        directly to the per-node score.
        """
        return _FUZZY_MATCH_BONUS * fuzzy_score(query_token, node_label)

    @staticmethod
    def vector_bonus(sim: float) -> float:
        """Vector tier bonus for a cosine similarity value.

        Public so tests can assert the exact bonus formula matches the spec.
        """
        return _VECTOR_SIMILARITY_BONUS * float(sim)
