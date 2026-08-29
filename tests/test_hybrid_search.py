"""Tests for hybrid semantic + fuzzy search.

Covers the spec's acceptance criteria (spec §8) at the unit-test level:
- AC2: semantic=False falls back to pure lexical (no behavior change)
- AC3: no embedding sidecar -> degrade to pure lexical, no error
- AC6: precise query (UserService) stays EXACT-dominated
- AC7: fuzzy tier catches "UserServise" typo -> UserService
- AC13: top_n>1 returns multiple `=== Result N/M ===` separated subgraphs
- AC14: top_n=1 (default) returns a single subgraph without separator
- AC9: 3-tier lexical if/elif/elif is unchanged (verified via behavior parity
  with semantic=False on a precise query)

Each test builds a small nx.Graph in memory and calls _score_query /
_query_graph_text directly — no MCP server, no API keys required. The
vector tier is exercised with a synthetic query_embedding_scores dict so
the OpenAI embedding API is not hit.
"""
from __future__ import annotations

from pathlib import Path

import networkx as nx
import numpy as np
import pytest

from graphify.embeddings import cosine_similarity, _node_embed_text
from graphify.fuzzy import fuzzy_score
from graphify.hybrid_scorer import (
    HybridScorer,
    _FUZZY_MATCH_BONUS,
    _VECTOR_SIMILARITY_BONUS,
)
from graphify.serve import _query_graph_text, _score_query


# ---------------------------------------------------------------------------
# fuzzy_score (AC7 building block)
# ---------------------------------------------------------------------------


class TestFuzzyScore:
    def test_exact_match_scores_high(self) -> None:
        assert fuzzy_score("UserService", "UserService") > 0.85

    def test_typo_scores_above_threshold(self) -> None:
        # UserServise (typo) vs UserService — JaroWinkler ~0.93
        assert fuzzy_score("UserServise", "UserService") >= 0.85

    def test_completely_different_returns_zero(self) -> None:
        assert fuzzy_score("login", "authservice") == 0.0

    def test_empty_input_returns_zero(self) -> None:
        assert fuzzy_score("", "anything") == 0.0
        assert fuzzy_score("anything", "") == 0.0

    def test_case_insensitive(self) -> None:
        # Case should not affect the JaroWinkler score
        assert fuzzy_score("USERSERVICE", "userservice") > 0.85


# ---------------------------------------------------------------------------
# cosine_similarity
# ---------------------------------------------------------------------------


class TestCosineSimilarity:
    def test_identical_vectors_score_one(self) -> None:
        q = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        m = np.array([[1.0, 0.0, 0.0]], dtype=np.float32)
        sims = cosine_similarity(q, m)
        assert sims[0] > 0.99

    def test_orthogonal_vectors_score_zero(self) -> None:
        q = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        m = np.array([[0.0, 1.0, 0.0]], dtype=np.float32)
        sims = cosine_similarity(q, m)
        assert sims[0] < 0.01

    def test_45_degrees_scores_about_0_707(self) -> None:
        q = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        m = np.array([[0.7071, 0.7071, 0.0]], dtype=np.float32)
        sims = cosine_similarity(q, m)
        assert 0.69 < sims[0] < 0.72

    def test_multiple_rows(self) -> None:
        q = np.array([1.0, 0.0], dtype=np.float32)
        m = np.array(
            [[1.0, 0.0], [0.0, 1.0], [0.7071, 0.7071]], dtype=np.float32
        )
        sims = cosine_similarity(q, m)
        assert len(sims) == 3
        assert sims[0] > 0.99
        assert sims[1] < 0.01
        assert 0.69 < sims[2] < 0.72


# ---------------------------------------------------------------------------
# _node_embed_text (spec §5.2)
# ---------------------------------------------------------------------------


class TestNodeEmbedText:
    def test_uses_desc_when_present(self) -> None:
        node = {"label": "AuthService", "desc": "Manages user authentication."}
        assert _node_embed_text(node) == "Manages user authentication."

    def test_falls_back_to_rationale_when_desc_empty(self) -> None:
        node = {"label": "AuthService", "desc": "", "rationale": "Handles auth tokens."}
        assert _node_embed_text(node) == "Handles auth tokens."

    def test_returns_empty_when_desc_and_rationale_missing(self) -> None:
        node = {"label": "AuthService"}
        assert _node_embed_text(node) == ""

    def test_does_not_use_norm_label_or_nid(self) -> None:
        # Per spec §5.2: norm_label / nid / source_file are NOT embedded
        node = {
            "label": "AuthService",
            "norm_label": "authservice",
            "id": "src_auth_service",
            "source_file": "src/auth/service.py",
            "desc": "Real description wins.",
        }
        assert _node_embed_text(node) == "Real description wins."


# ---------------------------------------------------------------------------
# HybridScorer (AC3: no sidecar -> degrade gracefully)
# ---------------------------------------------------------------------------


class TestHybridScorerNoSidecar:
    def test_available_false_when_no_sidecar(self, tmp_path: Path) -> None:
        scorer = HybridScorer(tmp_path)
        assert not scorer.available

    def test_vector_scores_returns_none_when_unavailable(self, tmp_path: Path) -> None:
        scorer = HybridScorer(tmp_path)
        assert scorer.vector_scores("any query") is None

    def test_lazy_load_from_graph_path_missing_sidecar(self, tmp_path: Path) -> None:
        # Even when graph_path points at a real dir, no embeddings/ subdir
        # means HybridScorer stays unavailable (AC3: degrade, don't crash).
        scorer = HybridScorer(tmp_path)
        assert not scorer.available
        assert scorer.vector_scores("login") is None


# ---------------------------------------------------------------------------
# _score_query — vector tier (AC1, AC6)
# ---------------------------------------------------------------------------


def _build_small_graph() -> nx.Graph:
    """A 3-node graph for tier tests: UserService (precise), AuthService
    (semantic-only), and an unrelated ThrottleService."""
    G = nx.Graph()
    G.add_node("userservice", label="UserService", norm_label="userservice",
               source_file="src/user/service.py", desc="Manages user accounts.")
    G.add_node("authservice", label="AuthService", norm_label="authservice",
               source_file="src/auth/service.py",
               desc="Validates user credentials and issues tokens.")
    G.add_node("throttleservice", label="ThrottleService",
               norm_label="throttleservice", source_file="src/throttle.py",
               desc="Rate-limits incoming requests.")
    return G


class TestScoreQueryVectorTier:
    def test_pure_lexical_when_no_embeddings(self) -> None:
        """AC2/AC3: semantic=True with no embedding scores == pure lexical."""
        G = _build_small_graph()
        terms = ["userservice"]  # exact match on the norm_label
        with_embeddings = _score_query(
            G, terms, collect_per_term_seeds=False,
            query_embedding_scores=None, hybrid_scorer=None, semantic=True,
        )
        without = _score_query(
            G, terms, collect_per_term_seeds=False, semantic=False,
        )
        # Identical ranking when no vector scores provided
        assert with_embeddings.ranked == without.ranked
        # And UserService is top-1 (EXACT x1000 dominates)
        assert with_embeddings.ranked[0][1] == "userservice"

    def test_vector_tier_adds_bonus_to_lexical_match(self) -> None:
        """AC6: precise query stays top-1, but vector tier adds bonus."""
        G = _build_small_graph()
        # UserService gets a high vector sim (0.95) — bonus should be added
        query_emb = {"userservice": 0.95, "authservice": 0.10, "throttleservice": 0.05}
        scored = _score_query(
            G, ["userservice"],
            collect_per_term_seeds=False,
            query_embedding_scores=query_emb, semantic=True,
        )
        # UserService still top-1
        assert scored.ranked[0][1] == "userservice"
        # Score includes EXACT (1000 * idf) + vector bonus (5.0 * 0.95 * idf)
        # Just verify it's strictly higher than pure lexical
        pure = _score_query(G, ["userservice"], collect_per_term_seeds=False)
        assert scored.ranked[0][0] > pure.ranked[0][0]

    def test_vector_tier_rescues_zero_lexical_node(self) -> None:
        """AC1: 'login' (zero lexical overlap with AuthService) is rescued by
        vector tier when query_embedding_scores says they're similar."""
        G = _build_small_graph()
        # 'login' has zero lexical overlap with any node label — pure lexical
        # scores 0 on all three. Vector tier should pull AuthService in.
        pure = _score_query(G, ["login"], collect_per_term_seeds=False)
        assert not pure.ranked  # nothing matched lexically
        # Now supply vector scores: AuthService is highly similar to "login"
        query_emb = {"authservice": 0.90, "userservice": 0.30, "throttleservice": 0.05}
        scored = _score_query(
            G, ["login"],
            collect_per_term_seeds=False,
            query_embedding_scores=query_emb, semantic=True,
        )
        assert scored.ranked, "vector tier should have rescued a node"
        assert scored.ranked[0][1] == "authservice"
        # Score is vector bonus only (5.0 * 0.90 = 4.5)
        assert scored.ranked[0][0] == pytest.approx(_VECTOR_SIMILARITY_BONUS * 0.90, rel=0.01)

    def test_semantic_false_disables_vector_tier(self) -> None:
        """AC2: semantic=False ignores query_embedding_scores entirely."""
        G = _build_small_graph()
        query_emb = {"authservice": 0.99, "userservice": 0.99}
        scored = _score_query(
            G, ["login"],
            collect_per_term_seeds=False,
            query_embedding_scores=query_emb, semantic=False,  # OFF
        )
        assert not scored.ranked  # vector tier did NOT fire


# ---------------------------------------------------------------------------
# _score_query — fuzzy tier (AC7)
# ---------------------------------------------------------------------------


class TestScoreQueryFuzzyTier:
    def test_fuzzy_catches_typo(self) -> None:
        """AC7: 'UserServise' (typo) should match UserService via fuzzy tier."""
        G = _build_small_graph()
        scorer = HybridScorer()  # no sidecar — fuzzy still works (rapidfuzz only)
        scored = _score_query(
            G, ["userservise"],  # typo
            collect_per_term_seeds=False,
            hybrid_scorer=scorer, semantic=True,
        )
        # UserService should be the top hit (typo fuzzy-matches it)
        assert scored.ranked, "fuzzy tier should have caught the typo"
        assert scored.ranked[0][1] == "userservice"

    def test_fuzzy_disabled_when_semantic_false(self) -> None:
        """AC2: semantic=False disables fuzzy tier too."""
        G = _build_small_graph()
        scorer = HybridScorer()
        scored = _score_query(
            G, ["userservise"],
            collect_per_term_seeds=False,
            hybrid_scorer=scorer, semantic=False,
        )
        # With semantic=False, fuzzy should NOT fire — 'userservise' has zero
        # lexical overlap with 'userservice' (typo misses all 3 tiers).
        assert not scored.ranked

    def test_fuzzy_does_not_disturb_exact_match(self) -> None:
        """AC6: precise query 'UserService' — fuzzy tier should not change
        the ranking because EXACT already fires (fuzzy only runs when
        tier_value == 0 AND substr_value == 0)."""
        G = _build_small_graph()
        scorer = HybridScorer()
        with_fuzzy = _score_query(
            G, ["userservice"],
            collect_per_term_seeds=False,
            hybrid_scorer=scorer, semantic=True,
        )
        without_fuzzy = _score_query(
            G, ["userservice"], collect_per_term_seeds=False,
        )
        # Same top node, same score (fuzzy didn't fire because EXACT matched)
        assert with_fuzzy.ranked[0][1] == without_fuzzy.ranked[0][1]
        assert with_fuzzy.ranked[0][0] == pytest.approx(without_fuzzy.ranked[0][0])


# ---------------------------------------------------------------------------
# _query_graph_text — top_n (AC13, AC14)
# ---------------------------------------------------------------------------


def _build_multi_seed_graph() -> nx.Graph:
    """Graph with several equally-matchable seed candidates for top_n tests."""
    G = nx.Graph()
    # Three exact-match candidates so top_n=3 picks each independently.
    G.add_node("authservice", label="AuthService", norm_label="authservice",
               source_file="a.py", desc="auth service")
    G.add_node("userservice", label="UserService", norm_label="userservice",
               source_file="u.py", desc="user service")
    G.add_node("throttleservice", label="ThrottleService",
               norm_label="throttleservice", source_file="t.py",
               desc="throttle service")
    # Connect them so BFS has something to traverse
    G.add_edge("authservice", "userservice", relation="calls",
               confidence="EXTRACTED", source_file="a.py", source_location="L1")
    G.add_edge("userservice", "throttleservice", relation="calls",
               confidence="EXTRACTED", source_file="u.py", source_location="L2")
    return G


class TestQueryGraphTextTopN:
    def test_default_top_n_one_no_separator(self) -> None:
        """AC14: default (top_n=1) returns single subgraph, no === Result."""
        G = _build_multi_seed_graph()
        result = _query_graph_text(G, "auth", graph_path=None)
        assert "=== Result" not in result
        assert "authservice" in result.lower() or "AuthService" in result

    def test_top_n_three_returns_three_subgraphs(self) -> None:
        """AC13: top_n=3 returns 3 subgraphs separated by === Result i/3 ===."""
        G = _build_multi_seed_graph()
        # Use a query that matches all three nodes (each by its own token).
        # 'auth user throttle' has one token per node, all exact-matching.
        result = _query_graph_text(G, "auth user throttle", top_n=3, graph_path=None)
        # Format is `=== Result i/N (seed: label, score: S) ===` — check the
        # i/N marker is present for each of the three results.
        assert "=== Result 1/3" in result
        assert "=== Result 2/3" in result
        assert "=== Result 3/3" in result

    def test_top_n_one_explicit_no_separator(self) -> None:
        """AC14: explicit top_n=1 also returns single subgraph."""
        G = _build_multi_seed_graph()
        result = _query_graph_text(G, "auth", top_n=1, graph_path=None)
        assert "=== Result" not in result

    def test_top_n_zero_falls_back_to_single(self) -> None:
        """top_n=0 should not crash — falls through to the top_n<=1 branch."""
        G = _build_multi_seed_graph()
        result = _query_graph_text(G, "auth", top_n=0, graph_path=None)
        assert "=== Result" not in result

    def test_top_n_with_no_matches_returns_no_match_message(self) -> None:
        """When the query matches nothing, top_n>1 returns the no-match message."""
        G = _build_multi_seed_graph()
        result = _query_graph_text(G, "nonexistentterm", top_n=3, graph_path=None)
        assert "No matching nodes found" in result


# ---------------------------------------------------------------------------
# _query_graph_text — semantic flag end-to-end (AC2)
# ---------------------------------------------------------------------------


class TestQueryGraphTextSemantic:
    def test_no_semantic_off_does_not_crash(self) -> None:
        """AC2: --no-semantic path runs in pure-lexical mode without error."""
        G = _build_multi_seed_graph()
        # No embedding sidecar attached — semantic=True should auto-degrade
        result = _query_graph_text(G, "auth", semantic=True, graph_path=None)
        assert "authservice" in result.lower() or "AuthService" in result
        # And semantic=False should also work (explicit pure lexical)
        result_off = _query_graph_text(G, "auth", semantic=False, graph_path=None)
        assert "authservice" in result_off.lower() or "AuthService" in result_off

    def test_lazy_load_scorer_on_first_query(self, tmp_path: Path) -> None:
        """The CLI path doesn't pre-warm the scorer via _GraphContextCache;
        _query_graph_text should lazy-build it from graph_path. With no
        sidecar present, this stays available=False (no crash)."""
        G = _build_multi_seed_graph()
        # Pass a graph_path that doesn't exist as a real file — the lazy-load
        # only uses it for the parent dir, and HybridScorer handles missing
        # embeddings/ dir gracefully (returns None).
        fake_path = str(tmp_path / "graph.json")
        result = _query_graph_text(
            G, "auth", semantic=True, graph_path=fake_path,
        )
        # Should not crash; AuthService should appear
        assert "authservice" in result.lower() or "AuthService" in result
        # Scorer should now be cached on the graph object
        assert "_hybrid_scorer" in G.graph


# ---------------------------------------------------------------------------
# Bonus constants (spec §4.1)
# ---------------------------------------------------------------------------


class TestBonusConstants:
    def test_vector_bonus_between_substring_and_prefix(self) -> None:
        """Spec §4.1: _VECTOR_SIMILARITY_BONUS is between SUBSTRING(1) and
        PREFIX(100) so a precise query stays EXACT-dominated."""
        from graphify.serve import _SUBSTRING_MATCH_BONUS, _PREFIX_MATCH_BONUS
        assert _SUBSTRING_MATCH_BONUS < _VECTOR_SIMILARITY_BONUS < _PREFIX_MATCH_BONUS

    def test_fuzzy_bonus_above_substring_below_vector(self) -> None:
        """Spec §4.1: _FUZZY_MATCH_BONUS is above SUBSTRING(1) but below
        VECTOR(5) so fuzzy never outscores a real vector hit."""
        from graphify.serve import _SUBSTRING_MATCH_BONUS
        assert _SUBSTRING_MATCH_BONUS < _FUZZY_MATCH_BONUS < _VECTOR_SIMILARITY_BONUS

    def test_vector_bonus_static_method(self) -> None:
        """The vector_bonus static helper matches the spec formula."""
        assert HybridScorer.vector_bonus(0.9) == pytest.approx(_VECTOR_SIMILARITY_BONUS * 0.9)
        assert HybridScorer.vector_bonus(0.0) == 0.0
        assert HybridScorer.vector_bonus(1.0) == pytest.approx(_VECTOR_SIMILARITY_BONUS)
