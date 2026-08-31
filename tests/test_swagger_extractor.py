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
    _detect_main_language,
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

    # --- Java codegen Impl suffix fallback ---

    def test_java_impl_fallback_when_direct_match_missing(self) -> None:
        """Java codegen emits <Name>Impl classes; fall back to Impl suffix
        when the swagger tag has no direct class match and the corpus
        contains .java files."""
        nodes = [_class_node("FooServiceImpl", source_file="src/FooServiceImpl.java")]
        idx = _build_code_indices(nodes)
        result = _match_controller("FooService", idx)
        assert len(result) == 1
        assert result[0][0]["label"] == "FooServiceImpl"
        assert result[0][1] == "EXTRACTED"
        assert result[0][2] == 1.0

    def test_java_impl_fallback_skipped_when_direct_class_exists(self) -> None:
        """When a direct class match exists, Impl fallback must not fire
        (avoid preferring an Impl class over the real controller)."""
        nodes = [
            _class_node("FooService", source_file="src/FooService.java"),
            _class_node("FooServiceImpl", source_file="src/FooServiceImpl.java"),
        ]
        idx = _build_code_indices(nodes)
        result = _match_controller("FooService", idx)
        assert len(result) == 1
        assert result[0][0]["label"] == "FooService"

    def test_java_impl_fallback_not_used_for_non_java_projects(self) -> None:
        """Impl suffix fallback must NOT fire for TypeScript/Python projects
        where XxxImpl is not a codegen convention."""
        nodes = [_class_node("FooServiceImpl", source_file="src/FooServiceImpl.ts")]
        idx = _build_code_indices(nodes)
        result = _match_controller("Foo", idx)
        assert result == []

    def test_java_impl_fallback_prefers_impl_class_over_non_class_node(self) -> None:
        """When the direct lookup finds only a non-class node (e.g. a function)
        but the Impl-suffixed lookup finds a class, prefer the Impl class."""
        nodes = [
            _function_node("Foo", source_file="src/Foo.java"),
            _class_node("FooImpl", source_file="src/FooImpl.java"),
        ]
        idx = _build_code_indices(nodes)
        result = _match_controller("Foo", idx)
        assert len(result) == 1
        assert result[0][0]["label"] == "FooImpl"
        assert result[0][1] == "EXTRACTED"

    def test_java_impl_fallback_ambiguous_multiple_impl_classes(self) -> None:
        """Multiple <Name>Impl classes -> AMBIGUOUS, same as direct matching."""
        nodes = [
            _class_node("FooImpl", source_file="src/v1/FooImpl.java"),
            _class_node("FooImpl", source_file="src/v2/FooImpl.java"),
        ]
        idx = _build_code_indices(nodes)
        result = _match_controller("Foo", idx)
        assert len(result) == 2
        for _node, conf, score in result:
            assert conf == "AMBIGUOUS"
            assert score == 0.3

    def test_java_impl_fallback_returns_empty_when_impl_also_missing(self) -> None:
        """main_language=java but neither <Name> nor <Name>Impl exists -> []."""
        nodes = [_class_node("BarServiceImpl", source_file="src/BarServiceImpl.java")]
        idx = _build_code_indices(nodes)
        assert _match_controller("Foo", idx) == []

    def test_main_language_java_detected(self) -> None:
        """_build_code_indices sets main_language='java' when .java files
        are the majority of code nodes."""
        nodes = [_class_node("Foo", source_file="src/Foo.java")]
        assert _build_code_indices(nodes)["main_language"] == "java"

    def test_main_language_non_java(self) -> None:
        """_build_code_indices sets main_language to the extension of the
        majority language."""
        nodes = [_class_node("Foo", source_file="src/Foo.ts")]
        assert _build_code_indices(nodes)["main_language"] == "ts"

    def test_main_language_mixed_java_dominant(self) -> None:
        """Mixed Java + TS project where Java has more nodes -> main_language='java'.
        Impl fallback fires and finds the Java <Name>Impl class."""
        nodes = [
            _class_node("UserClient", source_file="frontend/src/UserClient.ts"),
            _class_node("UserControllerImpl", source_file="backend/src/UserControllerImpl.java"),
            _function_node("query", source_file="backend/src/UserControllerImpl.java"),
            _function_node("create", source_file="backend/src/UserControllerImpl.java"),
        ]
        idx = _build_code_indices(nodes)
        assert idx["main_language"] == "java"
        # "UserController" has no direct match -> Impl fallback finds UserControllerImpl
        result = _match_controller("UserController", idx)
        assert len(result) == 1
        assert result[0][0]["label"] == "UserControllerImpl"

    def test_main_language_ts_dominant_no_impl_fallback(self) -> None:
        """Mixed Java + TS project where TS has more nodes -> main_language='ts'.
        Impl fallback must NOT fire even if a <Name>Impl.java class exists,
        because the backend is TypeScript-dominant."""
        nodes = [
            _class_node("UserControllerImpl", source_file="backend/src/UserControllerImpl.java"),
            _class_node("UserClient", source_file="frontend/src/UserClient.ts"),
            _function_node("render", source_file="frontend/src/UserClient.ts"),
            _function_node("mount", source_file="frontend/src/UserClient.ts"),
        ]
        idx = _build_code_indices(nodes)
        assert idx["main_language"] == "ts"
        # main_language != "java" -> no Impl fallback -> no match
        result = _match_controller("UserController", idx)
        assert result == []

    def test_main_language_build_scripts_dont_dominate(self) -> None:
        """Python/Shell build scripts have fewer nodes than Java app code,
        so main_language stays 'java' even in a polyglot repo."""
        nodes = [
            _class_node("FooController", source_file="src/FooController.java"),
            _function_node("handleGet", source_file="src/FooController.java"),
            _function_node("handlePost", source_file="src/FooController.java"),
            _function_node("build", source_file="scripts/build.py"),
            _function_node("deploy", source_file="scripts/deploy.sh"),
        ]
        idx = _build_code_indices(nodes)
        assert idx["main_language"] == "java"

    def test_main_language_empty_for_no_code_nodes(self) -> None:
        """No code nodes -> main_language=''."""
        assert _build_code_indices([])["main_language"] == ""


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


# ---------------------------------------------------------------------------
# End-to-end: Java codegen Impl fallback through extract_swagger
# ---------------------------------------------------------------------------

class TestJavaImplFallbackE2E:
    """Verify the Impl suffix fallback works end-to-end: swagger tag
    ``APPPublishService`` matches Java class ``APPPublishServiceImpl`` when
    no bare ``APPPublishService`` class exists in the code index."""

    @pytest.fixture
    def result_impl(self, tmp_path: Path) -> ExtractionResult:
        src_dir = tmp_path / "docs"
        src_dir.mkdir()
        fixture = src_dir / "apppublish.yaml"
        fixture.write_text(
            (FIXTURES / "apppublish.yaml").read_text(encoding="utf-8"), encoding="utf-8"
        )
        # Java codegen output: APPPublishServiceImpl class + handler methods.
        # Note: NO bare APPPublishService class — only the Impl-suffixed one.
        code_nodes = [
            _class_node("APPPublishServiceImpl", source_file="src/APPPublishServiceImpl.java"),
            _function_node("query", source_file="src/APPPublishServiceImpl.java"),
            _function_node("getById", source_file="src/APPPublishServiceImpl.java"),
            _function_node("create", source_file="src/APPPublishServiceImpl.java"),
        ]
        return extract_swagger(fixture, root=tmp_path, nodes=_code_index(code_nodes))

    def test_controller_matched_via_impl_fallback(self, result_impl: ExtractionResult) -> None:
        """Each endpoint should have a references edge to APPPublishServiceImpl."""
        refs = [e for e in result_impl.edges if e["relation"] == "references"]
        controller_refs = [
            e for e in refs if "apppublishserviceimpl" in e["target"]
        ]
        # 3 endpoints, each linking to the controller class
        assert len(controller_refs) == 3
        for e in controller_refs:
            assert e["confidence"] == "EXTRACTED"
            assert e["confidence_score"] == 1.0

    def test_handler_matched_same_file_as_impl_controller(self, result_impl: ExtractionResult) -> None:
        """Handler functions should match in the Impl class's source_file."""
        refs = [e for e in result_impl.edges if e["relation"] == "references"]
        handler_refs = [e for e in refs if "_fn" in e["target"]]
        # 3 endpoints x 1 handler each = 3 handler refs
        assert len(handler_refs) == 3
        for e in handler_refs:
            assert e["confidence"] == "EXTRACTED"

    def test_no_unmatched_anchors(self, result_impl: ExtractionResult) -> None:
        """All tags and operationIds should be matched via Impl fallback."""
        assert len(result_impl.unmatched) == 0

    def test_impl_fallback_not_triggered_for_ts_project(self, tmp_path: Path) -> None:
        """Same swagger yaml, but code index has only .ts files -> no Impl
        fallback, all controller anchors unmatched."""
        src_dir = tmp_path / "docs"
        src_dir.mkdir()
        fixture = src_dir / "apppublish.yaml"
        fixture.write_text(
            (FIXTURES / "apppublish.yaml").read_text(encoding="utf-8"), encoding="utf-8"
        )
        # TypeScript project: only APPPublishServiceImpl.ts (no .java files)
        code_nodes = [
            _class_node("APPPublishServiceImpl", source_file="src/APPPublishServiceImpl.ts"),
        ]
        result = extract_swagger(fixture, root=tmp_path, nodes=_code_index(code_nodes))
        assert result is not None
        # main_language="ts" -> no Impl fallback -> controller unmatched
        controller_unmatched = [
            u for u in result.unmatched if u["anchorKind"] == "controller_tag"
        ]
        assert len(controller_unmatched) == 3


# ---------------------------------------------------------------------------
# Unit tests for _detect_main_language
# ---------------------------------------------------------------------------

class TestDetectMainLanguage:
    def test_pure_java_project(self) -> None:
        nodes = [
            _class_node("FooController", source_file="src/FooController.java"),
            _function_node("handleGet", source_file="src/FooController.java"),
        ]
        assert _detect_main_language(nodes) == "java"

    def test_pure_typescript_project(self) -> None:
        nodes = [_class_node("Foo", source_file="src/Foo.ts")]
        assert _detect_main_language(nodes) == "ts"

    def test_python_build_scripts(self) -> None:
        nodes = [_function_node("main", source_file="build.py")]
        assert _detect_main_language(nodes) == "py"

    def test_mixed_java_dominant(self) -> None:
        """Java backend (3 nodes) + Python build script (1 node) -> java."""
        nodes = [
            _class_node("UserController", source_file="src/UserController.java"),
            _function_node("handleGet", source_file="src/UserController.java"),
            _function_node("handlePost", source_file="src/UserController.java"),
            _function_node("build", source_file="scripts/build.py"),
        ]
        assert _detect_main_language(nodes) == "java"

    def test_mixed_ts_dominant_over_java(self) -> None:
        """TS frontend (3 nodes) + Java backend (1 node) -> ts.
        Frontend-heavy repo: Impl fallback correctly stays off."""
        nodes = [
            _class_node("App", source_file="frontend/src/App.ts"),
            _function_node("render", source_file="frontend/src/App.ts"),
            _function_node("mount", source_file="frontend/src/App.ts"),
            _class_node("UserControllerImpl", source_file="backend/UserControllerImpl.java"),
        ]
        assert _detect_main_language(nodes) == "ts"

    def test_empty_nodes_returns_empty(self) -> None:
        assert _detect_main_language([]) == ""

    def test_no_code_file_type_returns_empty(self) -> None:
        """Non-code nodes (file_type != 'code') are ignored."""
        nodes = [{"id": "x", "label": "x", "file_type": "document", "source_file": "x.java"}]
        assert _detect_main_language(nodes) == ""

    def test_no_source_file_returns_empty(self) -> None:
        """Nodes without source_file are skipped."""
        nodes = [{"id": "x", "label": "x", "file_type": "code"}]
        assert _detect_main_language(nodes) == ""

    def test_no_extension_returns_empty(self) -> None:
        """source_file without extension contributes nothing."""
        nodes = [{"id": "x", "label": "x", "file_type": "code", "source_file": "Makefile"}]
        assert _detect_main_language(nodes) == ""

    def test_tie_returns_first_encountered(self) -> None:
        """When two languages have equal counts, the first encountered wins
        (Python dict preserves insertion order). This is acceptable — ties
        are rare and both languages are equally 'main'."""
        nodes = [
            _class_node("A", source_file="src/A.java"),
            _class_node("B", source_file="src/B.ts"),
        ]
        result = _detect_main_language(nodes)
        assert result in ("java", "ts")

    def test_counts_all_extensions(self) -> None:
        """Shell scripts are counted too, but won't dominate if app code
        has more nodes."""
        nodes = [
            _class_node("Foo", source_file="src/Foo.java"),
            _function_node("deploy", source_file="scripts/deploy.sh"),
        ]
        assert _detect_main_language(nodes) == "java"

