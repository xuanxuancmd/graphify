"""Tests for the Evaluation Agent (graphify.evaluate).

Tests cover:
  - Evidence collection (heuristic rules, no LLM)
  - LLM response parsing (tolerant of fences, extra text, score clamping)
  - Score application (edges and nodes)
  - Graceful degradation (no backend → skip)
  - stamp_node_confidence (AST vs semantic origin)
  - Discrete three-tier scoring (0.95 / 0.50 / 0.05)
"""
from __future__ import annotations

import json
import networkx as nx
import pytest

from graphify.evaluate import (
    evaluate_graph,
    stamp_node_confidence,
    _collect_edge_evidence,
    _collect_node_evidence,
    _collect_items,
    _batch_items,
    _build_prompt,
    _parse_response,
    _clamp_to_tier,
    _apply_score,
    SCORE_CORRECT,
    SCORE_UNCERTAIN,
    SCORE_WRONG,
    _INFERRED_DEFAULT_SCORE,
)


# ---------------------------------------------------------------------------
# Test graphs
# ---------------------------------------------------------------------------

def _make_test_graph() -> nx.Graph:
    """Build a small test graph with EXTRACTED, INFERRED, and AMBIGUOUS edges."""
    G = nx.Graph()
    # AST nodes (should get EXTRACTED, 1.0)
    G.add_node("auth_service", label="AuthService", file_type="code",
               _origin="ast", source_file="auth.py")
    G.add_node("user_repo", label="UserRepository", file_type="code",
               _origin="ast", source_file="repo.py")
    # Semantic/LLM nodes (should get INFERRED, 0.55)
    G.add_node("auth_concept", label="AuthenticationFlow", file_type="concept",
               _origin="semantic", source_file="design.md")
    # An unverified semantic node
    G.add_node("fabricated", label="NonExistentSymbol", file_type="code",
               _origin="semantic", source_file="design.md",
               verification="unverified")

    # EXTRACTED edge (AST, should not be evaluated)
    G.add_edge("auth_service", "user_repo", relation="calls",
               confidence="EXTRACTED", confidence_score=1.0,
               source_file="auth.py", _origin="ast")
    # INFERRED edge (should be evaluated by Agent)
    G.add_edge("auth_service", "auth_concept", relation="references",
               confidence="INFERRED", confidence_score=0.55,
               source_file="design.md", _origin="semantic")
    # AMBIGUOUS edge (should NOT be evaluated — deterministic low score)
    G.add_edge("auth_concept", "user_repo", relation="references",
               confidence="AMBIGUOUS", confidence_score=0.2,
               source_file="design.md", _origin="semantic")
    return G


# ---------------------------------------------------------------------------
# stamp_node_confidence
# ---------------------------------------------------------------------------

class TestStampNodeConfidence:
    def test_ast_nodes_get_extracted(self):
        G = _make_test_graph()
        stamp_node_confidence(G)
        assert G.nodes["auth_service"]["confidence"] == "EXTRACTED"
        assert G.nodes["auth_service"]["confidence_score"] == 1.0

    def test_semantic_nodes_get_inferred(self):
        G = _make_test_graph()
        stamp_node_confidence(G)
        assert G.nodes["auth_concept"]["confidence"] == "INFERRED"
        assert G.nodes["auth_concept"]["confidence_score"] == _INFERRED_DEFAULT_SCORE

    def test_unverified_node_gets_low_score(self):
        G = _make_test_graph()
        stamp_node_confidence(G)
        assert G.nodes["fabricated"]["confidence_score"] <= 0.2

    def test_does_not_overwrite_existing_confidence(self):
        G = nx.Graph()
        G.add_node("n1", label="N1", _origin="ast", confidence="INFERRED",
                    confidence_score=0.7)
        stamp_node_confidence(G)
        # Should not overwrite an existing explicit confidence
        assert G.nodes["n1"]["confidence"] == "INFERRED"
        assert G.nodes["n1"]["confidence_score"] == 0.7


# ---------------------------------------------------------------------------
# Evidence collection
# ---------------------------------------------------------------------------

class TestEdgeEvidence:
    def test_collect_edge_evidence_has_fields(self):
        G = _make_test_graph()
        stamp_node_confidence(G)
        ev = _collect_edge_evidence(G, "auth_service", "auth_concept",
                                     G.edges["auth_service", "auth_concept"])
        assert "source_origin" in ev
        assert "llm_self_reported_score" in ev
        assert "has_ast_corroboration" in ev
        assert "is_self_loop" in ev
        assert "source_mentions_target" in ev
        # Type compatibility is conveyed via individual type fields + relation
        assert "source_file_type" in ev
        assert "target_file_type" in ev
        assert "source_node_kind" in ev
        assert "target_node_kind" in ev
        assert "relation" in ev
        assert "source_verified" in ev
        assert "target_verified" in ev

    def test_self_loop_detected(self):
        G = nx.Graph()
        G.add_node("n1", label="Foo", file_type="code", _origin="ast")
        G.add_edge("n1", "n1", relation="calls", confidence="INFERRED",
                   confidence_score=0.55, _origin="semantic")
        ev = _collect_edge_evidence(G, "n1", "n1", G.edges["n1", "n1"])
        assert ev["is_self_loop"] is True

    def test_ast_corroboration_detected(self):
        """has_ast_corroboration returns True when an EXTRACTED edge
        already connects the same pair."""
        G = _make_test_graph()
        stamp_node_confidence(G)
        # The auth_service→user_repo edge is EXTRACTED. Check that
        # _has_ast_edge finds it by querying evidence for that pair.
        # (We can't add a second INFERRED edge between the same pair in a
        # plain Graph, so we test _collect_edge_evidence on the existing
        # EXTRACTED edge — the evidence collector doesn't care about the
        # edge's own confidence, it checks if ANY edge between the pair
        # is EXTRACTED.)
        ev = _collect_edge_evidence(G, "auth_service", "user_repo",
                                     G.edges["auth_service", "user_repo"])
        assert ev["has_ast_corroboration"] is True

    def test_no_ast_corroboration_when_only_inferred(self):
        """has_ast_corroboration returns False when no EXTRACTED edge
        connects the pair."""
        G = _make_test_graph()
        stamp_node_confidence(G)
        # auth_service→auth_concept is only INFERRED, no AST edge
        ev = _collect_edge_evidence(G, "auth_service", "auth_concept",
                                     G.edges["auth_service", "auth_concept"])
        assert ev["has_ast_corroboration"] is False


class TestNodeEvidence:
    def test_collect_node_evidence_has_fields(self):
        G = _make_test_graph()
        stamp_node_confidence(G)
        ev = _collect_node_evidence(G, "auth_concept",
                                     G.nodes["auth_concept"])
        assert "origin" in ev
        assert "verification" in ev
        assert "file_type" in ev
        assert "degree" in ev
        assert "edge_confidences" in ev

    def test_fabricated_node_verification(self):
        G = _make_test_graph()
        stamp_node_confidence(G)
        ev = _collect_node_evidence(G, "fabricated", G.nodes["fabricated"])
        assert ev["verification"] == "unverified"


# ---------------------------------------------------------------------------
# Item collection
# ---------------------------------------------------------------------------

class TestCollectItems:
    def test_only_inferred_items_collected(self):
        G = _make_test_graph()
        stamp_node_confidence(G)
        items = _collect_items(G)
        # Should collect the 1 INFERRED edge + 2 INFERRED nodes
        # (auth_concept and fabricated, but fabricated has score<=0.2 so
        # it's still collected because confidence="INFERRED")
        edge_items = [i for i in items if i["kind"] == "edge"]
        node_items = [i for i in items if i["kind"] == "node"]
        assert len(edge_items) == 1  # the auth_service→auth_concept edge
        assert len(node_items) == 2  # auth_concept + fabricated

    def test_extracted_edge_not_collected(self):
        G = _make_test_graph()
        stamp_node_confidence(G)
        items = _collect_items(G)
        ids = [i["id"] for i in items]
        # The EXTRACTED edge should NOT appear
        assert not any("auth_service|user_repo" in i for i in ids)

    def test_ambiguous_edge_not_collected(self):
        G = _make_test_graph()
        stamp_node_confidence(G)
        items = _collect_items(G)
        ids = [i["id"] for i in items]
        # The AMBIGUOUS edge should NOT appear
        assert not any("auth_concept|user_repo" in i for i in ids)


# ---------------------------------------------------------------------------
# Batching
# ---------------------------------------------------------------------------

class TestBatching:
    def test_batch_size(self):
        items = [{"id": f"item_{i}"} for i in range(25)]
        batches = _batch_items(items, 20)
        assert len(batches) == 2
        assert len(batches[0]) == 20
        assert len(batches[1]) == 5

    def test_empty_items(self):
        assert _batch_items([], 20) == []

    def test_batch_size_1(self):
        items = [{"id": "a"}, {"id": "b"}]
        batches = _batch_items(items, 1)
        assert len(batches) == 2


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

class TestPromptConstruction:
    def test_prompt_contains_system_instructions(self):
        batch = [{"id": "edge::a|b|calls", "kind": "edge",
                  "source": "A", "target": "B", "relation": "calls",
                  "source_label": "A", "target_label": "B",
                  "source_file": "a.py",
                  "evidence": {"has_ast_corroboration": True}}]
        prompt = _build_prompt(batch)
        assert "0.95" in prompt
        assert "0.50" in prompt
        assert "0.05" in prompt
        assert "DISCRETE" in prompt
        assert "edge::a|b|calls" in prompt

    def test_prompt_strips_none_evidence(self):
        batch = [{"id": "node::n1", "kind": "node", "label": "N1",
                  "file_type": "concept", "source_file": "n1.md",
                  "evidence": {"has_source_file": True, "verification": None}}]
        prompt = _build_prompt(batch)
        # None values should not appear in the JSON
        assert "verification" not in json.loads(
            prompt.split("Items to evaluate:\n")[1]
        )[0]["evidence"]


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

class TestParseResponse:
    def test_valid_json_array(self):
        resp = '[{"id": "edge::a|b|calls", "score": 0.95, "reason": "AST corroboration"}]'
        results = _parse_response(resp)
        assert len(results) == 1
        assert results[0]["id"] == "edge::a|b|calls"
        assert results[0]["score"] == 0.95

    def test_markdown_fences_stripped(self):
        resp = '```json\n[{"id": "n1", "score": 0.05, "reason": "wrong"}]\n```'
        results = _parse_response(resp)
        assert len(results) == 1
        assert results[0]["score"] == 0.05

    def test_extra_text_around_json(self):
        resp = 'Here are the results:\n[{"id": "n1", "score": 0.50, "reason": "unclear"}]\nDone.'
        results = _parse_response(resp)
        assert len(results) == 1
        assert results[0]["score"] == 0.50

    def test_empty_response(self):
        assert _parse_response("") == []
        assert _parse_response("   ") == []

    def test_no_json_array(self):
        assert _parse_response("no json here") == []

    def test_score_clamped_to_tier(self):
        resp = '[{"id": "n1", "score": 0.7, "reason": "medium"}]'
        results = _parse_response(resp)
        assert len(results) == 1
        # 0.7 should clamp to nearest tier — 0.50 is closer than 0.95
        assert results[0]["score"] == SCORE_UNCERTAIN

    def test_score_0_8_clamps_to_correct(self):
        resp = '[{"id": "n1", "score": 0.85, "reason": "high"}]'
        results = _parse_response(resp)
        # 0.85 is closer to 0.95 than to 0.50
        assert results[0]["score"] == SCORE_CORRECT

    def test_malformed_json_skipped(self):
        resp = '[{"id": "n1", "score": 0.95}, {"bad": "entry"}]'
        results = _parse_response(resp)
        # Only the valid entry survives
        assert len(results) == 1
        assert results[0]["id"] == "n1"


# ---------------------------------------------------------------------------
# Score clamping
# ---------------------------------------------------------------------------

class TestClampToTier:
    def test_exact_tiers_unchanged(self):
        assert _clamp_to_tier(0.95) == 0.95
        assert _clamp_to_tier(0.50) == 0.50
        assert _clamp_to_tier(0.05) == 0.05

    def test_near_correct_clamps_up(self):
        assert _clamp_to_tier(0.9) == SCORE_CORRECT
        assert _clamp_to_tier(0.8) == SCORE_CORRECT

    def test_near_wrong_clamps_down(self):
        assert _clamp_to_tier(0.1) == SCORE_WRONG
        assert _clamp_to_tier(0.2) == SCORE_WRONG

    def test_midrange_clamps_to_uncertain(self):
        assert _clamp_to_tier(0.4) == SCORE_UNCERTAIN
        assert _clamp_to_tier(0.6) == SCORE_UNCERTAIN
        assert _clamp_to_tier(0.7) == SCORE_UNCERTAIN


# ---------------------------------------------------------------------------
# Score application
# ---------------------------------------------------------------------------

class TestApplyScore:
    def test_edge_score_applied(self):
        G = _make_test_graph()
        stamp_node_confidence(G)
        result = {"id": "edge::auth_service|auth_concept|references",
                  "score": SCORE_CORRECT, "reason": "AST supports this"}
        delta = _apply_score(G, result)
        assert delta["edges_evaluated"] == 1
        assert delta["high"] == 1
        assert G.edges["auth_service", "auth_concept"]["confidence_score"] == SCORE_CORRECT
        assert G.edges["auth_service", "auth_concept"]["evaluated"] is True
        assert G.edges["auth_service", "auth_concept"]["evaluation_reason"] == "AST supports this"

    def test_node_score_applied(self):
        G = _make_test_graph()
        stamp_node_confidence(G)
        result = {"id": "node::auth_concept", "score": SCORE_WRONG,
                  "reason": "Fabricated concept"}
        delta = _apply_score(G, result)
        assert delta["nodes_evaluated"] == 1
        assert delta["low"] == 1
        assert G.nodes["auth_concept"]["confidence_score"] == SCORE_WRONG
        assert G.nodes["auth_concept"]["evaluated"] is True

    def test_unknown_id_ignored(self):
        G = _make_test_graph()
        result = {"id": "edge::nonexistent|node|x", "score": 0.95, "reason": ""}
        delta = _apply_score(G, result)
        assert delta == {"high": 0, "uncertain": 0, "low": 0,
                         "edges_evaluated": 0, "nodes_evaluated": 0}

    def test_multi_result_accumulation(self):
        """Verify that multiple _apply_score deltas accumulate correctly
        when the caller uses the stats[k] += delta[k] pattern (not
        stats.update(delta) which would overwrite)."""
        G = _make_test_graph()
        stamp_node_confidence(G)
        stats = {"edges_evaluated": 0, "nodes_evaluated": 0,
                 "high": 0, "uncertain": 0, "low": 0,
                 "llm_calls": 0, "skipped": 0}

        # Simulate 3 results: 1 high edge, 1 low node, 1 uncertain edge
        results = [
            {"id": "edge::auth_service|auth_concept|references",
             "score": SCORE_CORRECT, "reason": "correct"},
            {"id": "node::auth_concept",
             "score": SCORE_WRONG, "reason": "wrong"},
            {"id": "edge::auth_concept|user_repo|references",
             "score": SCORE_UNCERTAIN, "reason": "unclear"},
        ]

        for r in results:
            delta = _apply_score(G, r)
            for k, v in delta.items():
                stats[k] = stats.get(k, 0) + v

        # All 3 should accumulate — NOT just the last one
        assert stats["edges_evaluated"] == 2  # 2 edges, not 1
        assert stats["nodes_evaluated"] == 1  # 1 node
        assert stats["high"] == 1
        assert stats["low"] == 1
        assert stats["uncertain"] == 1


# ---------------------------------------------------------------------------
# Graceful degradation
# ---------------------------------------------------------------------------

class TestGracefulDegradation:
    def test_skip_flag_returns_skipped(self):
        G = _make_test_graph()
        stamp_node_confidence(G)
        stats = evaluate_graph(G, skip=True)
        assert stats["skipped"] == 1
        assert stats["llm_calls"] == 0
        # Scores should NOT be modified when skipped
        assert G.edges["auth_service", "auth_concept"]["confidence_score"] == 0.55

    def test_no_backend_skips_silently(self):
        G = _make_test_graph()
        stamp_node_confidence(G)
        # detect_backend() will return None in CI/test env without API keys
        stats = evaluate_graph(G, backend=None)
        assert stats["skipped"] == 1
        assert stats["llm_calls"] == 0

    def test_no_inferred_items_skips(self):
        G = nx.Graph()
        G.add_node("n1", label="N1", confidence="EXTRACTED",
                    confidence_score=1.0, _origin="ast")
        stats = evaluate_graph(G, skip=False, backend="claude")
        # No INFERRED items → nothing to evaluate
        assert stats["edges_evaluated"] == 0
        assert stats["nodes_evaluated"] == 0
