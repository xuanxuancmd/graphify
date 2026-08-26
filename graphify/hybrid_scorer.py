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


def _embed_backend_from_env() -> str | None:
    """Pick the embedding backend from env, mirroring llm.py auto-detect.

    Priority: ``GRAPHIFY_EMBED_BACKEND`` > same env vars as extraction backends.
    Returns ``None`` when nothing usable is configured so the HybridScorer can
    stay ``available=False`` and degrade to pure lexical at query time.
    """
    explicit = os.environ.get("GRAPHIFY_EMBED_BACKEND", "").strip().lower()
    if explicit:
        return explicit
    # Reuse whichever extraction backend the user has already configured.
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
    """Embedding model override env. Backend-specific defaults apply if unset."""
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
        self._embed_backend = embed_backend or _embed_backend_from_env()
        self._embed_model = embed_model or _embed_model_from_env()
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
