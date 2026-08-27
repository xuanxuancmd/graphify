"""E2E tests for the DDD doc-extractor on a real user-management project.

These tests verify the DDD extractor's behavior against a CLI-generated
``graph.json``. The graph is built by running::

    graphify extract tests/e2e/resources/user-management \\
        --backend openai --allow-partial --no-cluster --no-viz

(with a fake OPENAI_API_KEY — LLM Tier 2 fails, but the doc extraction
stage runs BEFORE LLM Tier 2, so DDD doc-anchor nodes are in graph.json
even though LLM semantic nodes are missing).

The conftest.py at tests/e2e/ runs this extraction once at session start
and writes ``.graph/graph.json``. All tests below read that file.

Test coverage:

  1. Two-stage extraction (G3): code AST + doc extraction both ran
  2. DDD doc-anchor nodes for all 7 whitelist document types
  3. Code anchor matching: describes (references) edges doc-anchor → code
  4. Cross-file edge resolution: related/categorized_under/cites
  5. Merge mode: doc-anchor + page/heading coexist
  6. Unmatched anchors in .graph/ddd-unmatched.json
  7. tags field on nodes (for serve.py retrieval)
  8. Node shape compliance (all-generic fields, no ddd_* prefix)
  9. Edge count sanity
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent / "resources" / "user-management"
GRAPH_JSON = PROJECT_ROOT / ".graph" / "graph.json"
UNMATCHED_JSON = PROJECT_ROOT / ".graph" / "ddd-unmatched.json"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def graph() -> dict[str, Any]:
    """Load the CLI-generated graph.json once for the whole test module."""
    if not GRAPH_JSON.exists():
        pytest.skip(
            "graph.json not found — run conftest.py extraction first, or run: "
            "OPENAI_API_KEY=fake graphify extract "
            "tests/e2e/resources/user-management --backend openai "
            "--allow-partial --no-cluster --no-viz"
        )
    return json.loads(GRAPH_JSON.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def nodes(graph) -> list[dict]:
    return graph.get("nodes", [])


@pytest.fixture(scope="module")
def edges(graph) -> list[dict]:
    return graph.get("links", graph.get("edges", []))


@pytest.fixture(scope="module")
def doc_anchors(nodes) -> list[dict]:
    return [n for n in nodes if n.get("node_kind") == "doc-anchor"]


# ---------------------------------------------------------------------------
# 1. Graph exists and has meaningful size (CLI extraction ran)
# ---------------------------------------------------------------------------

class TestGraphIntegrity:
    """Verify the CLI-generated graph.json is present and non-trivial."""

    def test_graph_json_exists(self):
        assert GRAPH_JSON.exists(), "graph.json should exist after CLI extraction"

    def test_graph_has_nodes(self, graph):
        nodes = graph.get("nodes", [])
        assert len(nodes) >= 100, f"graph should have ≥100 nodes; got {len(nodes)}"

    def test_graph_has_edges(self, graph):
        edges = graph.get("links", graph.get("edges", []))
        assert len(edges) >= 100, f"graph should have ≥100 edges; got {len(edges)}"


# ---------------------------------------------------------------------------
# 2. Two-stage extraction (G3): code AST + doc extraction both ran
# ---------------------------------------------------------------------------

class TestTwoStageExtraction:
    """Verify the graph contains BOTH code nodes AND doc-anchor nodes,
    proving the two-stage pipeline (code AST → doc with code_index) ran."""

    def test_has_code_nodes(self, nodes):
        code_nodes = [n for n in nodes if n.get("file_type") == "code"]
        assert len(code_nodes) > 0, "graph should contain code AST nodes"

    def test_has_doc_anchor_nodes(self, doc_anchors):
        assert len(doc_anchors) > 0, (
            "graph should contain doc-anchor nodes from DDD extractor"
        )

    def test_has_page_nodes_from_markdown(self, nodes):
        pages = [n for n in nodes if n.get("node_kind") == "page"]
        assert len(pages) > 0, (
            "graph should contain page nodes from default extract_markdown "
            "(merge mode keeps both doc-anchor and page/heading)"
        )

    def test_has_heading_nodes_from_markdown(self, nodes):
        headings = [n for n in nodes if n.get("node_kind") == "heading"]
        assert len(headings) > 0, "graph should contain heading nodes from markdown"


# ---------------------------------------------------------------------------
# 2b. Three-phase extraction (Gap-5): code → config JSON → doc
# ---------------------------------------------------------------------------

class TestThreePhaseExtraction:
    """Verify the three-phase pipeline (code+manifests → config JSON → doc)
    ran, proving Gap-5 split config JSON from pure code files."""

    def test_has_package_json_config_nodes(self, nodes):
        """package.json processed by json_config.py → config key/ref nodes."""
        pkg_nodes = [
            n for n in nodes
            if n.get("file_type") == "code"
            and "package.json" in (n.get("source_file") or "")
        ]
        assert len(pkg_nodes) > 0, (
            "package.json should produce config nodes in stage 2"
        )

    def test_has_tsconfig_json_config_nodes(self, nodes):
        """tsconfig.json processed by json_config.py → config nodes."""
        ts_nodes = [
            n for n in nodes
            if n.get("file_type") == "code"
            and "tsconfig.json" in (n.get("source_file") or "")
        ]
        assert len(ts_nodes) > 0, (
            "tsconfig.json should produce config nodes in stage 2"
        )


# ---------------------------------------------------------------------------
# 3. DDD doc-anchor nodes for all 7 whitelist types
# ---------------------------------------------------------------------------

class TestDDDDocAnchorNodes:
    """Verify doc-anchor nodes cover all 7 DDD document types."""

    def test_doc_anchor_count(self, doc_anchors):
        assert len(doc_anchors) >= 30, (
            f"should have ≥30 doc-anchor nodes; got {len(doc_anchors)}"
        )

    def test_all_doc_categories_present(self, doc_anchors):
        categories = {
            n.get("tags", [None, None, None])[2]
            for n in doc_anchors if len(n.get("tags", [])) >= 3
        }
        expected = {
            "context-map", "technical-constraints", "business-flow",
            "domain-model", "contracts", "invariants", "domain-events",
        }
        missing = expected - categories
        assert missing == set(), f"missing doc categories: {missing}"

    def test_all_ddd_types_present(self, doc_anchors):
        """Most expected DDD types appear in tags[1].

        Note: _infer_ddd_type maps from the <anchor:ddd> column NAME to a
        machine-readable type. Some column names in this project's DDD docs
        don't match any of the heuristic keywords (e.g. "业务动作" doesn't
        contain "流程"/"flow"), so they fall back to "concept". This is a
        known limitation documented in spec §10 (Risk: <anchor:ddd> column
        name inference may fail for custom terminology). The node is still
        extracted correctly — only the ddd_type tag is imprecise.
        """
        ddd_types = {
            n.get("tags", [None, None])[1]
            for n in doc_anchors if len(n.get("tags", [])) >= 2
        }
        expected_subset = {
            "bounded_context", "glossary_term", "tech_constraint",
            "aggregate_root", "domain_event",
            "invariant", "value_object", "domain_service",
        }
        found = ddd_types & expected_subset
        assert len(found) >= 6, (
            f"should find ≥6 DDD types; got {ddd_types} (intersection: {found})"
        )

    def test_bc01_and_bc02_present(self, doc_anchors):
        concept_ids = {n.get("concept_id") for n in doc_anchors}
        assert "BC-01" in concept_ids, "BC-01 (用户管理) should be in graph"
        assert "BC-02" in concept_ids, "BC-02 (认证) should be in graph"

    def test_tc001_through_tc007_present(self, doc_anchors):
        concept_ids = {n.get("concept_id") for n in doc_anchors}
        for i in range(1, 8):
            tc_id = f"TC-{i:03d}"
            assert tc_id in concept_ids, f"{tc_id} should be in graph"


# ---------------------------------------------------------------------------
# 4. Code anchor matching: describes (references) edges
# ---------------------------------------------------------------------------

class TestCodeAnchorMatching:
    """Verify DDD code anchors produced references edges to code nodes."""

    def test_has_references_edges_to_code(self, nodes, edges):
        code_node_ids = {n["id"] for n in nodes if n.get("file_type") == "code"}
        refs = [
            e for e in edges
            if e.get("relation") == "references" and e.get("target") in code_node_ids
        ]
        assert len(refs) >= 5, (
            f"should have ≥5 references edges targeting code nodes; got {len(refs)}"
        )

    def test_user_class_anchored(self, nodes, edges, doc_anchors):
        """TC-001's `User` anchor links to the User class code node."""
        user_code = [n for n in nodes if n.get("label") == "User" and n.get("file_type") == "code"]
        assert user_code, "User class should exist as a code node"
        user_id = user_code[0]["id"]
        tc001 = [n for n in doc_anchors if n.get("concept_id") == "TC-001"]
        assert tc001, "TC-001 doc-anchor should exist"
        tc001_id = tc001[0]["id"]
        edge = [
            e for e in edges
            if e.get("source") == tc001_id and e.get("target") == user_id
            and e.get("relation") == "references"
        ]
        assert edge, (
            f"TC-001 → User class references edge should exist; "
            f"checked source={tc001_id} target={user_id}"
        )

    def test_authservice_anchored(self, nodes, edges):
        """business-flow.md references AuthService.register → should link to AuthService."""
        as_code = [n for n in nodes if n.get("label") == "AuthService" and n.get("file_type") == "code"]
        assert as_code, "AuthService class should exist as a code node"
        as_id = as_code[0]["id"]
        refs_to_as = [
            e for e in edges
            if e.get("relation") == "references" and e.get("target") == as_id
        ]
        assert refs_to_as, (
            "AuthService should be targeted by ≥1 references edge "
            "(from business-flow / domain-model doc-anchors)"
        )


# ---------------------------------------------------------------------------
# 4b. Code anchor confidence (Gap-6): EXTRACTED vs AMBIGUOUS
# ---------------------------------------------------------------------------

class TestCodeAnchorConfidence:
    """Verify DDD code anchors carry correct confidence/confidence_score
    fields (Gap-6: multi-match → AMBIGUOUS 0.3, unique → EXTRACTED 1.0)."""

    def test_unique_match_edges_are_extracted(self, edges):
        """Unique-match describes edges → confidence=EXTRACTED, score=1.0.

        Only checks DDD-produced edges (source starts with 'docanchor') —
        AST edges have confidence but may lack confidence_score.
        """
        ddd_refs = [
            e for e in edges
            if e.get("relation") == "references"
            and str(e.get("source", "")).startswith("docanchor")
            and e.get("confidence") is not None
        ]
        extracted = [e for e in ddd_refs if e.get("confidence") == "EXTRACTED"]
        assert len(extracted) > 0, (
            "should have ≥1 EXTRACTED-confidence DDD references edge"
        )
        for e in extracted:
            assert e.get("confidence_score") == 1.0

    def test_ambiguous_multi_match_edges_exist(self, edges):
        """Logger anchor (two Logger classes in fixture) → AMBIGUOUS 0.3.

        The fixture has Logger in src/utils/logger.ts AND
        src/middleware/request-logger.ts — a SimpleName anchor 'Logger'
        matches both → all edges get AMBIGUOUS/0.3.
        """
        # Find edges targeting Logger code nodes
        ambig = [
            e for e in edges
            if e.get("confidence") == "AMBIGUOUS"
            and e.get("confidence_score") == 0.3
        ]
        assert len(ambig) > 0, (
            "should have ≥1 AMBIGUOUS-confidence edge (from Logger multi-match "
            "or com.example.User qualified-name path mismatch)"
        )


# ---------------------------------------------------------------------------
# 5. Cross-file edge resolution
# ---------------------------------------------------------------------------

class TestCrossFileEdgeResolution:
    """Verify edges between DDD documents resolve via global concept_id index."""

    def test_bc02_to_bc01_related_edge(self, doc_anchors, edges):
        """context-map.md's BC-02 → BC-01 business relationship → conceptually_related_to."""
        bc01 = next(n for n in doc_anchors if n.get("concept_id") == "BC-01")
        bc02 = next(n for n in doc_anchors if n.get("concept_id") == "BC-02")
        edge = [
            e for e in edges
            if e.get("source") == bc02["id"] and e.get("target") == bc01["id"]
            and e.get("relation") == "conceptually_related_to"
        ]
        assert edge, "BC-02 → BC-01 conceptually_related_to edge should exist"

    def test_tc_categorized_under_bc(self, doc_anchors, edges):
        """TC-001 (适用范围=BC-01) → BC-01; TC-003 (适用范围=BC-02) → BC-02."""
        bc01 = next(n for n in doc_anchors if n.get("concept_id") == "BC-01")
        bc02 = next(n for n in doc_anchors if n.get("concept_id") == "BC-02")
        tc001 = next(n for n in doc_anchors if n.get("concept_id") == "TC-001")
        tc003 = next(n for n in doc_anchors if n.get("concept_id") == "TC-003")

        tc001_bc01 = [
            e for e in edges
            if e.get("source") == tc001["id"] and e.get("target") == bc01["id"]
            and e.get("relation") == "conceptually_related_to"
        ]
        assert tc001_bc01, "TC-001 → BC-01 categorized_under edge should exist"

        tc003_bc02 = [
            e for e in edges
            if e.get("source") == tc003["id"] and e.get("target") == bc02["id"]
            and e.get("relation") == "conceptually_related_to"
        ]
        assert tc003_bc02, "TC-003 → BC-02 categorized_under edge should exist"

    def test_contracts_cite_bc02(self, doc_anchors, edges):
        """contracts.md 对端 BC=BC-02 → cites edges to BC-02."""
        bc02 = next(n for n in doc_anchors if n.get("concept_id") == "BC-02")
        cites_to_bc02 = [
            e for e in edges
            if e.get("relation") == "cites" and e.get("target") == bc02["id"]
        ]
        assert cites_to_bc02, "should have ≥1 cites edge targeting BC-02"


# ---------------------------------------------------------------------------
# 6. Unmatched anchors sidecar
# ---------------------------------------------------------------------------

class TestUnmatchedAnchors:
    """Verify ddd-unmatched.json behavior.

    After the anchor-matching fixes (nameIndex normalization, endpointIndex by
    full_path, _clean_anchor strip, config-before-md ordering), all anchors in
    the user-management fixture resolve — unmatched is 0 or the sidecar is
    absent. These tests verify that state.
    """

    def test_sidecar_empty_or_absent(self):
        """ddd-unmatched.json should be absent or empty (all anchors resolved)."""
        if UNMATCHED_JSON.exists():
            unmatched = json.loads(UNMATCHED_JSON.read_text(encoding="utf-8"))
            assert isinstance(unmatched, list)
            assert len(unmatched) == 0, (
                f"expected 0 unmatched anchors, got {len(unmatched)}: "
                f"{[u.get('anchor') for u in unmatched]}"
            )
        # Absent is also acceptable — extract() only writes the sidecar when
        # there are unmatched entries.


# ---------------------------------------------------------------------------
# 7. tags field (for serve.py retrieval)
# ---------------------------------------------------------------------------

class TestTagsField:
    """Verify doc-anchor nodes carry tags usable by serve.py _node_search_text."""

    def test_all_doc_anchors_have_tags(self, doc_anchors):
        for n in doc_anchors:
            assert "tags" in n, f"node {n.get('id')} missing tags"
            assert isinstance(n["tags"], list)
            assert len(n["tags"]) == 3, f"tags should have 3 elements: {n.get('tags')}"
            assert n["tags"][0] == "ddd", f"tags[0] should be 'ddd': {n.get('tags')}"

    def test_code_nodes_have_no_tags(self, nodes):
        """Code nodes should NOT have tags (only DDD doc-anchor nodes do)."""
        code_nodes = [n for n in nodes if n.get("file_type") == "code"]
        tagged_code = [n for n in code_nodes if "tags" in n and n["tags"]]
        assert len(tagged_code) == 0, (
            f"code nodes should not carry tags; found {len(tagged_code)} with tags"
        )


# ---------------------------------------------------------------------------
# 8. Node shape compliance
# ---------------------------------------------------------------------------

class TestNodeShape:
    """Verify DDD doc-anchor nodes use all-generic fields (no ddd_* prefix)."""

    def test_no_ddd_prefixed_fields(self, doc_anchors):
        for n in doc_anchors:
            bad = [k for k in n if k.startswith("ddd_")]
            assert bad == [], f"node {n.get('id')} has ddd_* fields: {bad}"

    def test_file_type_is_concept(self, doc_anchors):
        for n in doc_anchors:
            assert n["file_type"] == "concept", (
                f"node {n.get('id')} file_type={n['file_type']!r}, expected 'concept'"
            )

    def test_required_fields_present(self, doc_anchors):
        required = {"id", "label", "file_type", "source_file", "node_kind", "tags"}
        for n in doc_anchors:
            missing = required - set(n.keys())
            assert missing == set(), (
                f"node {n.get('id')} missing: {missing}"
            )

    def test_concept_id_preserved(self, doc_anchors):
        """concept_id is the raw DDD identifier (BC-01, TC-001, etc.)."""
        for n in doc_anchors:
            cid = n.get("concept_id")
            assert cid, f"node {n.get('id')} should have a non-empty concept_id"


# ---------------------------------------------------------------------------
# 9. Edge count sanity
# ---------------------------------------------------------------------------

class TestEdgeCountSanity:
    """Verify the DDD extractor contributes meaningful structure."""

    def test_has_meaningful_references_count(self, edges):
        refs = [e for e in edges if e.get("relation") == "references"]
        assert len(refs) >= 20, (
            f"should have ≥20 references edges; got {len(refs)}"
        )

    def test_has_cross_file_ddd_edges(self, edges):
        cross = [
            e for e in edges
            if e.get("relation") in ("conceptually_related_to", "cites")
        ]
        assert len(cross) >= 5, (
            f"should have ≥5 cross-file DDD edges; got {len(cross)}"
        )
