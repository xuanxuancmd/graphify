"""Hybrid scorer: vector similarity + fuzzy matching tiers.

Called by serve.py's ``_score_query`` as an ADDITIVE bonus on top of the
existing 3-tier lexical scoring (EXACT/PREFIX/SUBSTRING). Does NOT replace
the lexical tiers — the vector and fuzzy bonuses are added on top so a
precise query stays EXACT-dominated and a fuzzy/semantic query gets
rescued from a 0 lexical score.

Vector tier uses confidence-gated tiered weighting (see
docs/retrieval-overall-design/vector-tier-redesign-spec.md):

    bonus = _vector_tier_weight(sim) × sim

The tier_weight is a piecewise constant selected by the cosine similarity
value, mapping each confidence band into the lexical scoring hierarchy:

    T1  sim ≥ 0.85     → 80.0   (PREFIX-level, high-confidence semantic)
    T2  0.70 ≤ sim < 0.85 → 20.0   (between SUBSTRING and PREFIX)
    T3  0.55 ≤ sim < 0.70 → 5.0    (SUBSTRING-level)
    T4  0.40 ≤ sim < 0.55 → 1.0    (FUZZY/SOURCE-level)
    T5  sim < 0.40     → 0.0    (noise, discarded)

This replaces the old flat ``_VECTOR_SIMILARITY_BONUS = 5.0`` linear
multiplier which was "decorative" (0.5% of EXACT=1000) and effectively
rescue-only. The tiered approach lets a high-confidence vector match
(sim ≥ 0.85, bonus up to 80) genuinely influence ranking on semantic
queries while still staying below EXACT(1000) and PREFIX(100) on precise
queries. The bonus is ``tier_weight × sim`` (not tier_weight alone) so
magnitude is preserved within each tier and there's a deliberate jump at
tier boundaries (confidence-level transitions).

Thresholds are hardcoded (not user-configurable) — see
``_DEFAULT_VECTOR_SIM_TIERS`` below.

    _FUZZY_MATCH_BONUS = 2.0   (above SUBSTRING=1, below VECTOR T3=5)

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

# --- Vector tier: confidence-gated piecewise weights ----------------------
#
# Default sim thresholds (hardcoded, not user-configurable).
# Adapted for OpenAI-compatible embedding models.
#
# Each tier maps to a band in the lexical scoring hierarchy:
#   T1 [t1, 1.0]      → 80.0  (PREFIX-level, high-confidence semantic)
#   T2 [t2, t1)        → 20.0  (between SUBSTRING and PREFIX)
#   T3 [t3, t2)        → 5.0   (SUBSTRING-level, weak semantic)
#   T4 [t4, t3)        → 1.0   (FUZZY/SOURCE-level, marginal)
#   T5 [0, t4)         → 0.0   (noise, discarded)
#
# The bonus is tier_weight × sim (not tier_weight alone) so magnitude
# is preserved within each tier.
_DEFAULT_VECTOR_SIM_TIERS: tuple[float, ...] = (0.85, 0.70, 0.55, 0.40)
_VECTOR_TIER_WEIGHTS: tuple[float, ...] = (80.0, 20.0, 5.0, 1.0, 0.0)

_FUZZY_MATCH_BONUS = 2.0


def _vector_tier_weight(
    sim: float,
    tiers: tuple[float, ...] = _DEFAULT_VECTOR_SIM_TIERS,
) -> float:
    """Return the tier_weight for a cosine similarity value.

    Tiers (hardcoded — see ``_DEFAULT_VECTOR_SIM_TIERS``):
        sim ≥ tiers[0]          → 80.0  (T1: high-confidence, PREFIX-level)
        tiers[1] ≤ sim < tiers[0] → 20.0  (T2: medium, SUBSTRING~PREFIX)
        tiers[2] ≤ sim < tiers[1] → 5.0   (T3: weak, SUBSTRING-level)
        tiers[3] ≤ sim < tiers[2] → 1.0   (T4: marginal, FUZZY-level)
        sim < tiers[3]          → 0.0   (T5: noise, discarded)

    The caller multiplies this by sim to get the final bonus::

        bonus = _vector_tier_weight(sim) × sim

    So magnitude is preserved within each tier and there's a deliberate
    jump at tier boundaries (confidence-level transitions).
    """
    if sim >= tiers[0]:
        return _VECTOR_TIER_WEIGHTS[0]
    if sim >= tiers[1]:
        return _VECTOR_TIER_WEIGHTS[1]
    if sim >= tiers[2]:
        return _VECTOR_TIER_WEIGHTS[2]
    if sim >= tiers[3]:
        return _VECTOR_TIER_WEIGHTS[3]
    return _VECTOR_TIER_WEIGHTS[4]


def _load_embed_config_from_graphifyrc(graph_dir: "str | Path | None" = None) -> dict[str, str]:
    """Read embedding config keys from the project ``graphifyrc``.

    graphify writes graph.json under ``<project>/.graph/`` (default, or
    ``.graph/`` when GRAPHIFY_OUT is overridden). The per-project
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
    ``.graph/``). When None, falls back to CWD. Returns an empty dict when
    no config is found on either layer.
    """
    try:
        from graphify.hooks import _load_graphifyrc, _project_graphifyrc_path, _parse_graphifyrc_file
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
    # Also check for graphifyrc directly IN graph_dir (covers fixtures where
    # graph.json lives in a flat dir without the .graph/ subdirectory, e.g.
    # tests/fixtures/search_benchmark/). This direct-file check is a fallback;
    # when the _load_graphifyrc path already found it, the direct file is the
    # same file and the dict update is a no-op.
    if graph_dir is not None:
        direct_rc = Path(graph_dir) / "graphifyrc"
        if direct_rc.is_file():
            cfg.update(_parse_graphifyrc_file(direct_rc))
    # Extract embed-related keys. ``embed_*`` are the core embedding config
    # (backend/base_url/api_key/model). ``enable_embedding_proxy`` is the
    # proxy bypass switch (default false = direct connect, see embeddings.py
    # _build_embed_http_client). Other keys like viz_node_limit are not
    # relevant here.
    return {
        k: str(v)
        for k, v in cfg.items()
        if k.startswith("embed_") or k == "enable_embedding_proxy"
    }


def _embed_backend_from_env() -> str | None:
    """Pick the embedding backend from config file only.

    Reads ``embed_backend`` from ``.default-graphifyrc`` (shipped default)
    + ``.graph/graphifyrc`` (project override). Returns ``None`` when
    nothing is configured — the sole "skip" signal. When None, embedding
    generation is silently skipped at build time and queries degrade to
    pure lexical at query time. This is the intended behavior for an
    environment with no embedding endpoint: the graph is the primary
    artifact, embedding is an optional enhancement.

    Environment variables (GRAPHIFY_EMBED_BACKEND etc.) are no longer
    supported — use ``.graph/graphifyrc`` instead. This avoids "works on
    my machine" issues where env vars are set in one shell session but
    not visible to the python subprocess that actually runs the extract.
    """
    rc_cfg = _load_embed_config_from_graphifyrc()
    rc_backend = rc_cfg.get("embed_backend", "").strip().lower()
    return rc_backend or None


def _embed_model_from_env() -> str | None:
    """Embedding model name from ``.graph/graphifyrc``. Backend defaults apply if unset."""
    rc_cfg = _load_embed_config_from_graphifyrc()
    rc_model = rc_cfg.get("embed_model", "").strip()
    return rc_model or None


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
        # Load .graph/graphifyrc config (merged over .default-graphifyrc).
        # The embed_base_url / embed_api_key from the config file are stored
        # on the instance so _resolve_embed_backend_config can read them via
        # the rc_cfg getter — no env vars needed, avoiding "works on my
        # machine" issues where env vars are set in one shell but not visible
        # to a subprocess.
        self._rc_cfg = _load_embed_config_from_graphifyrc(graph_dir)
        # Backend: explicit arg > .graph/graphifyrc embed_backend.
        self._embed_backend = (
            embed_backend
            or self._rc_cfg.get("embed_backend", "").strip().lower()
            or None
        )
        # Model: explicit arg > .graph/graphifyrc embed_model.
        self._embed_model = (
            embed_model
            or self._rc_cfg.get("embed_model", "").strip()
            or None
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
    def vector_bonus(
        sim: float,
        tiers: tuple[float, ...] = _DEFAULT_VECTOR_SIM_TIERS,
    ) -> float:
        """Vector tier bonus for a cosine similarity value.

        Confidence-gated: ``tier_weight × sim``. See
        docs/retrieval-overall-design/vector-tier-redesign-spec.md §3.

        Public so tests can assert the exact bonus formula matches the spec.
        """
        return _vector_tier_weight(sim, tiers) * float(sim)
