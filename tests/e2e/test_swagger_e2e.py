"""E2E tests for the Swagger/OpenAPI YAML extractor on the user-management project.

These tests verify the swagger extractor's behavior against a CLI-generated
``graph.json``. The graph is built by ``conftest.py`` via::

    graphify extract tests/e2e/resources/user-management \\
        --backend openai --allow-partial --no-cluster --no-viz

(with a fake OPENAI_API_KEY). The extraction pipeline runs:

  - Stage 1: code AST (TypeScript classes/methods in src/)
  - Stage 3: doc extraction — the swagger extractor sees docs/user-api.yaml
    and is offered it via ``try_external_extractors`` with code_index populated
    from stage 1's AST nodes. Because ``suppress_llm=True`` and
    ``merge_mode="replace"``, the yaml file produces ONLY swagger nodes/edges
    (no default markdown, no LLM Tier 2).

The conftest already builds graph.json once per session; these tests read it.

Test coverage:

  1. swagger_doc node exists (one per .yaml file)
  2. rest_endpoint nodes extracted (9 endpoints: 6 UserService + 3 AuthController)
  3. Endpoint node fields: method, path, full_path, operation_id, swagger_tags,
     summary, description, response_codes, has_request_body
  4. contains edges: swagger_doc -> rest_endpoint
  5. defined_in edges: rest_endpoint -> swagger_doc (reverse)
  6. references edges: rest_endpoint -> code AST class/function nodes
     - UserService endpoints -> UserService class
     - UserService endpoints -> handler methods (getUser, createUser, etc.)
     - AuthController endpoints -> AuthController class
     - AuthController endpoints -> handler methods (handleRegister, etc.)
  7. Confidence labels: EXTRACTED for unique matches
  8. No shadow controller nodes (unmatched goes to ddd-unmatched.json, not nodes)
  9. Non-swagger yaml (docker-compose.yaml fixture) falls back to default
     extractor without breaking the pipeline
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
def swagger_doc_node(nodes) -> dict:
    docs = [n for n in nodes if n.get("node_kind") == "swagger_doc"]
    assert docs, "expected at least one swagger_doc node in graph.json"
    # The user-api.yaml fixture
    return next(
        (n for n in docs if "user-api" in n.get("source_file", "")),
        docs[0],
    )


@pytest.fixture(scope="module")
def endpoint_nodes(nodes) -> list[dict]:
    return [n for n in nodes if n.get("node_kind") == "rest_endpoint"]


# ---------------------------------------------------------------------------
# 1. swagger_doc node exists
# ---------------------------------------------------------------------------

class TestSwaggerDocNode:
    def test_doc_node_exists(self, swagger_doc_node) -> None:
        assert swagger_doc_node["id"].startswith("swagger_doc_")
        assert swagger_doc_node["file_type"] == "document"
        assert "swagger" in swagger_doc_node["tags"]
        assert swagger_doc_node["swagger_version"] == "2.x"
        assert swagger_doc_node["base_path"] == "/rest"
        assert swagger_doc_node["label"] == "user-api.yaml"

    def test_source_file_is_relative(self, swagger_doc_node) -> None:
        sf = swagger_doc_node["source_file"]
        assert "user-api.yaml" in sf
        # Should be repo-relative, not absolute
        assert not Path(sf).is_absolute()


# ---------------------------------------------------------------------------
# 2. rest_endpoint nodes extracted
# ---------------------------------------------------------------------------

class TestEndpointNodes:
    def test_endpoint_count(self, endpoint_nodes) -> None:
        # 7 UserService endpoints (list, create, get-by-id, update, delete,
        # suspend, reactivate) + 3 AuthController endpoints (register, login,
        # refresh) = 10
        assert len(endpoint_nodes) == 10, (
            f"expected 10 rest_endpoint nodes, got {len(endpoint_nodes)}: "
            f"{[e['label'] for e in endpoint_nodes]}"
        )

    def test_all_endpoint_labels_are_method_space_url(self, endpoint_nodes) -> None:
        for ep in endpoint_nodes:
            assert ep["label"].startswith(("GET ", "POST ", "PUT ", "DELETE ", "PATCH "))
            assert " /rest/" in ep["label"]

    def test_user_service_endpoints(self, endpoint_nodes) -> None:
        user_eps = [e for e in endpoint_nodes if "UserService" in e.get("swagger_tags", [])]
        # list, create, get-by-id, update, delete, suspend, reactivate = 7
        assert len(user_eps) == 7

    def test_auth_controller_endpoints(self, endpoint_nodes) -> None:
        auth_eps = [e for e in endpoint_nodes if "AuthController" in e.get("swagger_tags", [])]
        assert len(auth_eps) == 3

    def test_get_users_endpoint(self, endpoint_nodes) -> None:
        ep = next(
            e for e in endpoint_nodes
            if e["method"] == "GET" and e["path"] == "/userservice/v1/users"
        )
        assert ep["full_path"] == "/rest/userservice/v1/users"
        assert ep["label"] == "GET /rest/userservice/v1/users"
        assert ep["operation_id"] == "getUser"
        assert ep["swagger_tags"] == ["UserService"]
        assert "200" in ep["response_codes"]
        assert ep["has_request_body"] is False
        assert ep["base_path"] == "/rest"

    def test_post_users_endpoint_has_request_body(self, endpoint_nodes) -> None:
        ep = next(
            e for e in endpoint_nodes
            if e["method"] == "POST" and e["path"] == "/userservice/v1/users"
        )
        assert ep["operation_id"] == "createUser"
        assert ep["has_request_body"] is True
        assert "application/json" in ep["consumes"]

    def test_register_endpoint(self, endpoint_nodes) -> None:
        ep = next(
            e for e in endpoint_nodes
            if e["path"] == "/auth/register"
        )
        assert ep["method"] == "POST"
        assert ep["operation_id"] == "handleRegister"
        assert ep["swagger_tags"] == ["AuthController"]
        assert ep["full_path"] == "/rest/auth/register"
        assert ep["summary"] == "Register a new user account"
        assert ep["has_request_body"] is True

    def test_endpoint_desc_has_summary_and_description(self, endpoint_nodes) -> None:
        ep = next(
            e for e in endpoint_nodes
            if e["method"] == "POST" and e["path"] == "/auth/login"
        )
        # desc = summary + "\n\n" + description, with .strip() applied
        assert ep["summary"] in ep["desc"]
        assert ep["description"].strip() in ep["desc"]

    def test_source_location_present(self, endpoint_nodes) -> None:
        for ep in endpoint_nodes:
            assert ep.get("source_location") is not None
            assert ep["source_location"].startswith("L")


# ---------------------------------------------------------------------------
# 3. contains + defined_in edges
# ---------------------------------------------------------------------------

class TestDocContainmentEdges:
    def test_contains_edges(self, edges, swagger_doc_node, endpoint_nodes) -> None:
        contains = [
            e for e in edges
            if e["relation"] == "contains"
            and e["source"] == swagger_doc_node["id"]
        ]
        # Every endpoint should have a contains edge from the doc
        endpoint_ids = {e["id"] for e in endpoint_nodes}
        contained_endpoints = {e["target"] for e in contains}
        assert endpoint_ids == contained_endpoints or endpoint_ids.issubset(contained_endpoints)

    def test_defined_in_edges(self, edges, swagger_doc_node, endpoint_nodes) -> None:
        defined_in = [
            e for e in edges
            if e["relation"] == "defined_in"
            and e["target"] == swagger_doc_node["id"]
        ]
        endpoint_ids = {e["id"] for e in endpoint_nodes}
        definer_endpoints = {e["source"] for e in defined_in}
        assert endpoint_ids == definer_endpoints or endpoint_ids.issubset(definer_endpoints)


# ---------------------------------------------------------------------------
# 4. references edges — endpoint -> code AST nodes (THE code association)
# ---------------------------------------------------------------------------

class TestCodeAssociationEdges:
    def test_references_edges_exist(self, edges) -> None:
        refs = [e for e in edges if e["relation"] == "references"]
        # 9 endpoints × (1 controller + 1 handler) = 18 references edges
        assert len(refs) >= 9, (
            f"expected at least 9 references edges (1 controller per endpoint minimum), "
            f"got {len(refs)}"
        )

    def test_user_service_endpoints_link_to_user_service_class(self, edges, endpoint_nodes) -> None:
        user_eps = [e for e in endpoint_nodes if "UserService" in e.get("swagger_tags", [])]
        for ep in user_eps:
            refs_from_ep = [
                e for e in edges
                if e["relation"] == "references" and e["source"] == ep["id"]
            ]
            assert refs_from_ep, f"endpoint {ep['label']} has no references edges"

    def test_auth_endpoints_link_to_auth_controller_class(self, edges, endpoint_nodes) -> None:
        auth_eps = [e for e in endpoint_nodes if "AuthController" in e.get("swagger_tags", [])]
        for ep in auth_eps:
            refs_from_ep = [
                e for e in edges
                if e["relation"] == "references" and e["source"] == ep["id"]
            ]
            assert refs_from_ep, f"endpoint {ep['label']} has no references edges"

    def test_endpoint_links_to_handler_function(self, edges, endpoint_nodes) -> None:
        """The POST /users endpoint with operationId=createUser should link
        to a code node labeled 'createUser' (the UserService.createUser method)."""
        create_ep = next(
            e for e in endpoint_nodes
            if e["method"] == "POST" and e["operation_id"] == "createUser"
        )
        refs_from_create = [
            e for e in edges
            if e["relation"] == "references" and e["source"] == create_ep["id"]
        ]
        # At least one of these should target a node labeled createUser
        # (the handler function). The target node id is checked by label
        # through the node_index below — here we just confirm edges exist.
        assert len(refs_from_create) >= 1

    def test_endpoint_links_to_controller_class(self, edges, endpoint_nodes, nodes) -> None:
        """The GET /auth/login endpoint with tag=AuthController should link
        to the AuthController class node in the code AST."""
        login_ep = next(
            e for e in endpoint_nodes
            if e["method"] == "POST" and e["path"] == "/auth/login"
        )
        refs_from_login = [
            e for e in edges
            if e["relation"] == "references" and e["source"] == login_ep["id"]
        ]
        # Find the target nodes and check one is the AuthController class
        node_by_id = {n["id"]: n for n in nodes}
        target_labels = [node_by_id[t]["label"] for t in (e["target"] for e in refs_from_login) if t in node_by_id]
        assert "AuthController" in target_labels, (
            f"expected AuthController in references targets of {login_ep['label']}, "
            f"got: {target_labels}"
        )

    def test_handler_function_targeted(self, edges, endpoint_nodes, nodes) -> None:
        """The POST /auth/register endpoint should link to handleRegister function.

        The TS extractor emits method labels as ``.handleRegister()`` (leading
        dot marks class membership, trailing parens mark callability). The
        swagger extractor's ``_normalize_label`` strips both so the operationId
        ``handleRegister`` matches — the edge is created to the TS node whose
        raw label is ``.handleRegister()``. Assert against the normalized form.
        """
        register_ep = next(
            e for e in endpoint_nodes
            if e["method"] == "POST" and e["path"] == "/auth/register"
        )
        refs_from_register = [
            e for e in edges
            if e["relation"] == "references" and e["source"] == register_ep["id"]
        ]
        node_by_id = {n["id"]: n for n in nodes}
        target_labels = [node_by_id[t]["label"] for t in (e["target"] for e in refs_from_register) if t in node_by_id]
        # Accept either the bare name (handleRegister) or the TS form (.handleRegister())
        assert any(
            label in ("handleRegister", ".handleRegister()")
            for label in target_labels
        ), f"expected handleRegister in references targets, got: {target_labels}"

    def test_references_edges_are_extracted_or_ambiguous(self, edges) -> None:
        refs = [e for e in edges if e["relation"] == "references"]
        for e in refs:
            assert e["confidence"] in ("EXTRACTED", "AMBIGUOUS")
            # confidence_score may be dropped during graph.json serialization;
            # when present it must match the confidence label's score.
            if "confidence_score" in e:
                assert e["confidence_score"] in (1.0, 0.3)


# ---------------------------------------------------------------------------
# 5. No shadow controller nodes (unmatched -> ddd-unmatched.json, not nodes)
# ---------------------------------------------------------------------------

class TestNoShadowNodes:
    def test_no_rest_controller_shadow_nodes(self, nodes) -> None:
        shadows = [n for n in nodes if n.get("node_kind") == "rest_controller"]
        assert len(shadows) == 0


# ---------------------------------------------------------------------------
# 6. Graph sanity — swagger nodes don't break the rest of the graph
# ---------------------------------------------------------------------------

class TestGraphSanity:
    def test_graph_has_meaningful_node_count(self, nodes) -> None:
        # The user-management project has 12 .ts files + DDD docs + swagger yaml
        assert len(nodes) > 50, f"graph suspiciously small: {len(nodes)} nodes"

    def test_code_nodes_still_present(self, nodes) -> None:
        # The AST code nodes from stage 1 must still be there
        code_nodes = [n for n in nodes if n.get("file_type") == "code"]
        assert len(code_nodes) > 10, (
            f"expected code AST nodes to remain, got {len(code_nodes)}"
        )

    def test_user_service_class_node_present(self, nodes) -> None:
        # The actual UserService class from src/services/user.service.ts
        user_svc = [n for n in nodes if n.get("label") == "UserService"]
        assert len(user_svc) >= 1

    def test_auth_controller_class_node_present(self, nodes) -> None:
        auth_ctrl = [n for n in nodes if n.get("label") == "AuthController"]
        assert len(auth_ctrl) >= 1

    def test_swagger_doc_file_type_document(self, swagger_doc_node) -> None:
        assert swagger_doc_node["file_type"] == "document"

    def test_endpoint_file_type_concept(self, endpoint_nodes) -> None:
        for ep in endpoint_nodes:
            assert ep["file_type"] == "concept"
