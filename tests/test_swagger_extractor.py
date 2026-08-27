"""Tests for the swagger/openapi YAML extractor.

Verifies:
  - Swagger 2.0 endpoint extraction (Issue #1 fixture)
  - OpenAPI 3.x endpoint extraction (servers/basePath, requestBody)
  - Code-index matching: tags -> controller class, operationId -> handler function
  - Unmatched anchors recorded (no shadow nodes)
  - Non-swagger yaml returns None (fall back to default)
  - merge_mode="replace", suppress_llm=True
"""
from __future__ import annotations

from pathlib import Path

import pytest

from graphify.extractors.custom.swagger import (
    extract_swagger,
    _is_swagger_spec,
    _match_controller,
    _match_handler,
    _build_code_indices,
)
from graphify.extractors.registry import ExtractionResult

FIXTURES = Path(__file__).parent / "fixtures" / "swagger"


# ---------------------------------------------------------------------------
# Helpers 鈥?build mock AST code nodes for the code_index parameter
# ---------------------------------------------------------------------------

def _class_node(name: str, source_file: str = "src/APPPublishService.java") -> dict:
    """A mock AST class node (Java/Spring style controller)."""
    return {
        "id": f"src_apppublishservice_{name.lower()}",
        "label": name,
        "file_type": "code",
        "source_file": source_file,
        "source_location": "L10",
        "node_kind": "class",
    }


def _function_node(name: str, source_file: str = "src/APPPublishService.java") -> dict:
    """A mock AST function node (handler method)."""
    return {
        "id": f"src_apppublishservice_{name.lower()}_fn",
        "label": name,
        "file_type": "code",
        "source_file": source_file,
        "source_location": "L42",
        "node_kind": "function",
    }


def _code_index(nodes: list[dict]) -> list[dict]:
    """Return the nodes list that extract() passes to external extractors."""
    return nodes


# ---------------------------------------------------------------------------
# _is_swagger_spec heuristic
# ---------------------------------------------------------------------------

class TestIsSwaggerSpec:
    def test_swagger_2_key(self) -> None:
        assert _is_swagger_spec({"swagger": "2.0", "paths": {}}) is True

    def test_openapi_3_key(self) -> None:
        assert _is_swagger_spec({"openapi": "3.0.3", "paths": {}}) is True

    def test_paths_with_http_methods_lenient(self) -> None:
        assert _is_swagger_spec({"paths": {"/users": {"get": {}}}}) is True

    def test_docker_compose_is_not_swagger(self) -> None:
        assert _is_swagger_spec({"version": "3.8", "services": {}}) is False

    def test_plain_dict_is_not_swagger(self) -> None:
        assert _is_swagger_spec({"foo": "bar"}) is False

    def test_non_dict_returns_false(self) -> None:
        assert _is_swagger_spec("not a spec") is False
        assert _is_swagger_spec(None) is False
        assert _is_swagger_spec([1, 2, 3]) is False


# ---------------------------------------------------------------------------
# extract_swagger 鈥?Issue #1 fixture (Swagger 2.0)
# ---------------------------------------------------------------------------

class TestSwagger2Extraction:
    @pytest.fixture
    def result(self, tmp_path: Path) -> ExtractionResult:
        # Copy fixture into tmp_path/src/ so root-relative paths are stable
        src_dir = tmp_path / "docs"
        src_dir.mkdir()
        fixture = src_dir / "apppublish.yaml"
        fixture.write_text((FIXTURES / "apppublish.yaml").read_text(encoding="utf-8"), encoding="utf-8")
        return extract_swagger(fixture, root=tmp_path, nodes=None)

    def test_returns_extraction_result(self, result: ExtractionResult) -> None:
        assert result is not None
        assert result.merge_mode == "replace"
        assert result.suppress_llm is True

    def test_doc_node(self, result: ExtractionResult) -> None:
        doc_nodes = [n for n in result.nodes if n.get("node_kind") == "swagger_doc"]
        assert len(doc_nodes) == 1
        doc = doc_nodes[0]
        assert doc["label"] == "apppublish.yaml"
        assert doc["file_type"] == "document"
        assert doc["swagger_version"] == "2.x"
        assert doc["base_path"] == "/rest"
        assert "swagger" in doc["tags"]

    def test_endpoint_count(self, result: ExtractionResult) -> None:
        eps = [n for n in result.nodes if n.get("node_kind") == "rest_endpoint"]
        # 3 endpoints: GET /list, GET /{id}, POST /
        assert len(eps) == 3

    def test_get_list_endpoint(self, result: ExtractionResult) -> None:
        eps = [n for n in result.nodes if n.get("node_kind") == "rest_endpoint"]
        get_list = next(e for e in eps if e["method"] == "GET" and "list" in e["path"])
        assert get_list["label"] == "GET /rest/apppublishservice/v1/app/list"
        assert get_list["method"] == "GET"
        assert get_list["path"] == "/apppublishservice/v1/app/list"
        assert get_list["base_path"] == "/rest"
        assert get_list["full_path"] == "/rest/apppublishservice/v1/app/list"
        assert get_list["summary"] == "查询所有APP信息"
        assert get_list["operation_id"] == "query"
        assert get_list["swagger_tags"] == ["APPPublishService"]
        assert get_list["produces"] == ["application/json"]
        assert get_list["has_request_body"] is False
        assert "200" in get_list["response_codes"]
        assert get_list["source_location"] is not None
        assert get_list["source_location"].startswith("L")

    def test_post_endpoint_has_request_body(self, result: ExtractionResult) -> None:
        eps = [n for n in result.nodes if n.get("node_kind") == "rest_endpoint"]
        post_ep = next(e for e in eps if e["method"] == "POST")
        assert post_ep["operation_id"] == "create"
        assert post_ep["has_request_body"] is True
        assert "application/json" in post_ep["consumes"]

    def test_contains_edges(self, result: ExtractionResult) -> None:
        contains = [e for e in result.edges if e["relation"] == "contains"]
        # 3 endpoints -> 3 contains edges from doc
        assert len(contains) == 3
        for e in contains:
            assert e["confidence"] == "EXTRACTED"

    def test_defined_in_edges(self, result: ExtractionResult) -> None:
        defined_in = [e for e in result.edges if e["relation"] == "defined_in"]
        assert len(defined_in) == 3

    def test_unmatched_when_no_code_index(self, result: ExtractionResult) -> None:
        # No code_index -> all tags and operationIds are unmatched
        assert len(result.unmatched) > 0
        controller_unmatched = [u for u in result.unmatched if u["anchorKind"] == "controller_tag"]
        op_unmatched = [u for u in result.unmatched if u["anchorKind"] == "operation_id"]
        # 3 endpoints, each with tags[0]=APPPublishService -> 3 controller unmatched
        assert len(controller_unmatched) == 3
        # 3 endpoints, each with operationId -> 3 handler unmatched
        assert len(op_unmatched) == 3

    def test_no_shadow_nodes(self, result: ExtractionResult) -> None:
        # Unmatched controllers must NOT create shadow nodes
        shadow = [n for n in result.nodes if n.get("node_kind") == "rest_controller"]
        assert len(shadow) == 0

    def test_no_references_edges_without_code_index(self, result: ExtractionResult) -> None:
        # No code_index -> no references edges (only contains + defined_in)
        refs = [e for e in result.edges if e["relation"] == "references"]
        assert len(refs) == 0


# ---------------------------------------------------------------------------
# extract_swagger 鈥?OpenAPI 3.x fixture
# ---------------------------------------------------------------------------

class TestOpenAPI3Extraction:
    @pytest.fixture
    def result(self, tmp_path: Path) -> ExtractionResult:
        src_dir = tmp_path / "docs"
        src_dir.mkdir()
        fixture = src_dir / "users_openapi3.yaml"
        fixture.write_text(
            (FIXTURES / "users_openapi3.yaml").read_text(encoding="utf-8"), encoding="utf-8"
        )
        return extract_swagger(fixture, root=tmp_path, nodes=None)

    def test_version_detected(self, result: ExtractionResult) -> None:
        doc = next(n for n in result.nodes if n.get("node_kind") == "swagger_doc")
        assert doc["swagger_version"] == "3.x"

    def test_base_path_from_servers(self, result: ExtractionResult) -> None:
        doc = next(n for n in result.nodes if n.get("node_kind") == "swagger_doc")
        # servers[0].url = https://api.example.com/v1 -> base_path = /v1
        assert doc["base_path"] == "/v1"

    def test_endpoint_count(self, result: ExtractionResult) -> None:
        eps = [n for n in result.nodes if n.get("node_kind") == "rest_endpoint"]
        # GET /users, POST /users, DELETE /users/{id}
        assert len(eps) == 3

    def test_post_has_request_body_3x(self, result: ExtractionResult) -> None:
        eps = [n for n in result.nodes if n.get("node_kind") == "rest_endpoint"]
        post_ep = next(e for e in eps if e["method"] == "POST")
        assert post_ep["has_request_body"] is True  # requestBody present in 3.x

    def test_get_no_request_body_3x(self, result: ExtractionResult) -> None:
        eps = [n for n in result.nodes if n.get("node_kind") == "rest_endpoint"]
        get_ep = next(e for e in eps if e["method"] == "GET" and e["path"] == "/users")
        assert get_ep["has_request_body"] is False

    def test_full_path_with_base(self, result: ExtractionResult) -> None:
        eps = [n for n in result.nodes if n.get("node_kind") == "rest_endpoint"]
        get_users = next(e for e in eps if e["method"] == "GET" and e["path"] == "/users")
        assert get_users["full_path"] == "/v1/users"
        assert get_users["label"] == "GET /v1/users"


# ---------------------------------------------------------------------------
# Code-index matching 鈥?controller (tags) and handler (operationId)
# ---------------------------------------------------------------------------

class TestCodeIndexMatching:
    @pytest.fixture
    def result_with_code(self, tmp_path: Path) -> ExtractionResult:
        """Issue #1 fixture + a mock code_index with APPPublishService class
        and query/getById/create functions in the same source_file."""
        src_dir = tmp_path / "docs"
        src_dir.mkdir()
        fixture = src_dir / "apppublish.yaml"
        fixture.write_text(
            (FIXTURES / "apppublish.yaml").read_text(encoding="utf-8"), encoding="utf-8"
        )
        code_nodes = [
            _class_node("APPPublishService", source_file="src/APPPublishService.java"),
            _function_node("query", source_file="src/APPPublishService.java"),
            _function_node("getById", source_file="src/APPPublishService.java"),
            _function_node("create", source_file="src/APPPublishService.java"),
        ]
        return extract_swagger(
            fixture, root=tmp_path, nodes=_code_index(code_nodes)
        )

    def test_references_edges_created(self, result_with_code: ExtractionResult) -> None:
        refs = [e for e in result_with_code.edges if e["relation"] == "references"]
        # 3 endpoints x (1 controller + 1 handler) = 6 references edges
        assert len(refs) == 6

    def test_controller_match_extracted(self, result_with_code: ExtractionResult) -> None:
        refs = [e for e in result_with_code.edges if e["relation"] == "references"]
        # All should be EXTRACTED (unique matches)
        for e in refs:
            assert e["confidence"] == "EXTRACTED"
            assert e["confidence_score"] == 1.0

    def test_endpoint_links_to_controller(self, result_with_code: ExtractionResult) -> None:
        eps = [n for n in result_with_code.nodes if n.get("node_kind") == "rest_endpoint"]
        get_list = next(e for e in eps if e["operation_id"] == "query")
        # get_list endpoint should have a references edge to the APPPublishService class node
        controller_id = "src_apppublishservice_apppublishservice"
        refs_to_controller = [
            e for e in result_with_code.edges
            if e["relation"] == "references"
            and e["source"] == get_list["id"]
            and e["target"] == controller_id
        ]
        assert len(refs_to_controller) == 1

    def test_endpoint_links_to_handler(self, result_with_code: ExtractionResult) -> None:
        eps = [n for n in result_with_code.nodes if n.get("node_kind") == "rest_endpoint"]
        get_list = next(e for e in eps if e["operation_id"] == "query")
        handler_id = "src_apppublishservice_query_fn"
        refs_to_handler = [
            e for e in result_with_code.edges
            if e["relation"] == "references"
            and e["source"] == get_list["id"]
            and e["target"] == handler_id
        ]
        assert len(refs_to_handler) == 1

    def test_no_unmatched_when_all_matched(self, result_with_code: ExtractionResult) -> None:
        assert len(result_with_code.unmatched) == 0


# ---------------------------------------------------------------------------
# Ambiguous matching 鈥?multiple class/function candidates
# ---------------------------------------------------------------------------

class TestAmbiguousMatching:
    def test_multiple_class_matches_ambiguous(self, tmp_path: Path) -> None:
        src_dir = tmp_path / "docs"
        src_dir.mkdir()
        fixture = src_dir / "apppublish.yaml"
        fixture.write_text(
            (FIXTURES / "apppublish.yaml").read_text(encoding="utf-8"), encoding="utf-8"
        )
        # Two classes with the same name in different files
        code_nodes = [
            _class_node("APPPublishService", source_file="src/v1/APPPublishService.java"),
            _class_node("APPPublishService", source_file="src/v2/APPPublishService.java"),
        ]
        result = extract_swagger(fixture, root=tmp_path, nodes=_code_index(code_nodes))
        assert result is not None
        refs = [e for e in result.edges if e["relation"] == "references"]
        # Only controller refs (no handler matches since no function nodes)
        controller_refs = [e for e in refs if "apppublishservice" in e["target"]]
        assert len(controller_refs) == 6  # 3 endpoints x 2 ambiguous class candidates
        for e in controller_refs:
            assert e["confidence"] == "AMBIGUOUS"
            assert e["confidence_score"] == 0.3

    def test_handler_prefers_same_file_as_controller(self, tmp_path: Path) -> None:
        """When operationId matches functions in multiple files, prefer the one
        co-located with the matched controller (PascalCase.method pattern)."""
        src_dir = tmp_path / "docs"
        src_dir.mkdir()
        fixture = src_dir / "apppublish.yaml"
        fixture.write_text(
            (FIXTURES / "apppublish.yaml").read_text(encoding="utf-8"), encoding="utf-8"
        )
        code_nodes = [
            _class_node("APPPublishService", source_file="src/APPPublishService.java"),
            # query function in the SAME file as the controller -> preferred
            _function_node("query", source_file="src/APPPublishService.java"),
            # query function in a DIFFERENT file -> should NOT be matched
            _function_node("query", source_file="src/OtherService.java"),
        ]
        result = extract_swagger(fixture, root=tmp_path, nodes=_code_index(code_nodes))
        assert result is not None
        eps = [n for n in result.nodes if n.get("node_kind") == "rest_endpoint"]
        get_list = next(e for e in eps if e["operation_id"] == "query")
        handler_refs = [
            e for e in result.edges
            if e["relation"] == "references"
            and e["source"] == get_list["id"]
            and "_fn" in e["target"]
        ]
        # Should match ONLY the same-file function (EXTRACTED), not the other-file one
        assert len(handler_refs) == 1
        assert handler_refs[0]["confidence"] == "EXTRACTED"
        assert handler_refs[0]["target"] == "src_apppublishservice_query_fn"


# ---------------------------------------------------------------------------
# Non-swagger yaml returns None
# ---------------------------------------------------------------------------

class TestNonSwaggerFallback:
    def test_docker_compose_returns_none(self, tmp_path: Path) -> None:
        fixture = tmp_path / "docker-compose.yaml"
        fixture.write_text(
            (FIXTURES / "docker-compose.yaml").read_text(encoding="utf-8"), encoding="utf-8"
        )
        result = extract_swagger(fixture, root=tmp_path, nodes=None)
        assert result is None

    def test_non_yaml_returns_none(self, tmp_path: Path) -> None:
        fixture = tmp_path / "readme.md"
        fixture.write_text("# not swagger", encoding="utf-8")
        result = extract_swagger(fixture, root=tmp_path, nodes=None)
        assert result is None

    def test_invalid_yaml_returns_none(self, tmp_path: Path) -> None:
        fixture = tmp_path / "broken.yaml"
        fixture.write_text(":\n  - [unterminated", encoding="utf-8")
        result = extract_swagger(fixture, root=tmp_path, nodes=None)
        assert result is None


# ---------------------------------------------------------------------------
# Unit tests for _match_controller / _match_handler
# ---------------------------------------------------------------------------

class TestMatchController:
    def test_unique_class_match(self) -> None:
        nodes = [_class_node("FooService")]
        idx = _build_code_indices(nodes)
        result = _match_controller("FooService", idx)
        assert len(result) == 1
        assert result[0][1] == "EXTRACTED"
        assert result[0][2] == 1.0

    def test_no_match(self) -> None:
        nodes = [_class_node("BarService")]
        idx = _build_code_indices(nodes)
        assert _match_controller("FooService", idx) == []

    def test_multiple_class_matches_ambiguous(self) -> None:
        nodes = [
            _class_node("FooService", "src/a/FooService.java"),
            _class_node("FooService", "src/b/FooService.java"),
        ]
        idx = _build_code_indices(nodes)
        result = _match_controller("FooService", idx)
        assert len(result) == 2
        for _node, conf, score in result:
            assert conf == "AMBIGUOUS"
            assert score == 0.3

    def test_empty_tag_returns_empty(self) -> None:
        assert _match_controller("", _build_code_indices([])) == []


class TestMatchHandler:
    def test_unique_match_with_controller(self) -> None:
        cls = _class_node("FooService", "src/FooService.java")
        fn = _function_node("doThing", "src/FooService.java")
        idx = _build_code_indices([cls, fn])
        ctrl = _match_controller("FooService", idx)
        result = _match_handler("doThing", ctrl, idx)
        assert len(result) == 1
        assert result[0][1] == "EXTRACTED"

    def test_prefers_same_file_as_controller(self) -> None:
        cls = _class_node("FooService", "src/FooService.java")
        fn_same = _function_node("doThing", "src/FooService.java")
        fn_other = _function_node("doThing", "src/Other.java")
        idx = _build_code_indices([cls, fn_same, fn_other])
        ctrl = _match_controller("FooService", idx)
        result = _match_handler("doThing", ctrl, idx)
        # Should only return the same-file function
        assert len(result) == 1
        assert result[0][0]["source_file"] == "src/FooService.java"

    def test_no_controller_falls_back_to_any_function(self) -> None:
        fn = _function_node("doThing", "src/FooService.java")
        idx = _build_code_indices([fn])
        result = _match_handler("doThing", [], idx)
        assert len(result) == 1

    def test_empty_operation_id_returns_empty(self) -> None:
        assert _match_handler("", [], _build_code_indices([])) == []

    def test_no_function_match_returns_empty(self) -> None:
        cls = _class_node("FooService", "src/FooService.java")
        idx = _build_code_indices([cls])
        ctrl = _match_controller("FooService", idx)
        assert _match_handler("doThing", ctrl, idx) == []

