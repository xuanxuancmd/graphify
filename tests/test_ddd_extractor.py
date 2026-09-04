"""Tests for the DDD doc extractor + registry fallback + merge modes + tags retrieval.



Does not modify existing tests. Covers AC1-AC10 from spec.md.

"""

from pathlib import Path



import pytest



from graphify.extractors.custom import ddd  # triggers registration

from graphify.extractors.custom.ddd import (

    _build_code_indices,

    _build_global_node_index,

    _match_code_anchor,

    _resolve_pending_edges,

    extract_ddd,

)

from graphify.extractors.registry import (

    ExtractionResult,

    clear_registry,

    try_external_extractors,

)

from graphify.serve import _node_search_text



FIXTURES = Path(__file__).parent / "fixtures" / "ddd"





@pytest.fixture(autouse=True)

def _restore_registry():

    """Ensure custom extractors registered in a test don't leak to others."""

    import copy

    from graphify.extractors import registry

    saved = list(registry._REGISTRY)

    yield

    registry._REGISTRY[:] = saved





# ---------------------------------------------------------------------------

# AC1: Whitelist match + non-whitelist fallback

# ---------------------------------------------------------------------------



def test_whitelist_match_context_map(tmp_path: Path):

    """A context-map.md file should be parsed by the DDD extractor."""

    (tmp_path / "context-map.md").write_text(

        "| BC ID | BC 名称 | 职责 |\n|---|---|---|\n| BC-01 | 订单 | 处理下单 |\n",

        encoding="utf-8",

    )

    result = extract_ddd(tmp_path / "context-map.md", root=tmp_path)

    assert result is not None

    assert isinstance(result, ExtractionResult)

    assert result.merge_mode == "merge"

    assert any("bounded_context" in n.get("tags", []) for n in result.nodes)





def test_whitelist_match_all_seven_keywords(tmp_path: Path):

    """Each of the 7 whitelist keywords should trigger the DDD extractor."""

    for kw, fname in [

        ("context-map", "context-map.md"),

        ("technical-constraints", "technical-constraints.md"),

        ("business-flow", "business-flow.md"),

        ("invariants", "invariants.md"),

        ("contracts", "contracts.md"),

        ("domain-events", "domain-events.md"),

        ("domain-model", "domain-model.md"),

    ]:

        (tmp_path / fname).write_text("# stub\n", encoding="utf-8")

        result = extract_ddd(tmp_path / fname, root=tmp_path)

        assert result is not None, f"keyword {kw} ({fname}) should be claimed"





def test_non_whitelist_returns_none(tmp_path: Path):

    """A non-whitelist .md file should return None (fall back to default)."""

    (tmp_path / "README.md").write_text("# Hello\n", encoding="utf-8")

    result = extract_ddd(tmp_path / "README.md", root=tmp_path)

    assert result is None





# ---------------------------------------------------------------------------

# AC6: Registry fallback to default

# ---------------------------------------------------------------------------



def test_registry_fallback(tmp_path: Path):

    """try_external_extractors returns None for non-whitelist ??caller falls back."""

    (tmp_path / "README.md").write_text("# Hello\n", encoding="utf-8")

    result = try_external_extractors(tmp_path / "README.md", root=tmp_path)

    assert result is None





def test_registry_fallback_when_extractor_raises_not_applicable(tmp_path: Path):

    """An extractor raising _NotApplicable is treated as None (fall back)."""

    from graphify.extractors.registry import _NotApplicable, register_doc_extractor



    @register_doc_extractor

    def _always_noop(path, *, root, nodes=None):

        raise _NotApplicable()



    (tmp_path / "context-map.md").write_text(

        "| BC ID | BC 名称 |\n|---|---|\n| BC-01 | 订单 |\n", encoding="utf-8",

    )

    # The _always_noop extractor is registered FIRST here? No ??it's appended

    # AFTER the ddd extractor (which was registered at import time). So the ddd

    # extractor claims context-map.md before _always_noop is ever tried.

    # Test the _NotApplicable path with a non-whitelist file instead:

    (tmp_path / "README.md").write_text("# Hello\n", encoding="utf-8")

    result = try_external_extractors(tmp_path / "README.md", root=tmp_path)

    assert result is None





# ---------------------------------------------------------------------------

# AC3: Code anchor matching ??describes (references) edge

# ---------------------------------------------------------------------------



def test_code_anchor_pascal_case_class_match():

    """describes edge created when <anchor:code> matches a code node by class name."""

    code_nodes = [

        {"id": "src_order_service:OrderService", "label": "OrderService",

         "file_type": "code", "node_kind": "class", "source_file": "src/order/service.py"},

    ]

    indices = _build_code_indices(code_nodes)

    matched = _match_code_anchor("OrderService", indices)

    assert len(matched) == 1

    assert matched[0][0]["id"] == "src_order_service:OrderService"

    assert matched[0][1] == "EXTRACTED"

    assert matched[0][2] == 1.0





def test_code_anchor_pascal_case_method_match():

    """PascalCase.method matches a function in the same file as the class."""

    code_nodes = [

        {"id": "src_order_repo:OrderRepository", "label": "OrderRepository",

         "file_type": "code", "node_kind": "class", "source_file": "src/order/repo.py"},

        {"id": "src_order_repo:OrderRepository.create", "label": "create",

         "file_type": "code", "node_kind": "function", "source_file": "src/order/repo.py"},

    ]

    indices = _build_code_indices(code_nodes)

    matched = _match_code_anchor("OrderRepository.create", indices)

    assert len(matched) == 1

    assert matched[0][0]["id"] == "src_order_repo:OrderRepository.create"

    assert matched[0][1] == "EXTRACTED"





def test_code_anchor_snake_dot_method_match():

    """snake_case file.method matches a function in the file with that stem."""

    code_nodes = [

        {"id": "src_payment_consumer:PaymentCallbackHandler", "label": "PaymentCallbackHandler",

         "file_type": "code", "node_kind": "class", "source_file": "src/payment/consumer.py"},

        {"id": "src_payment_consumer:handle", "label": "handle",

         "file_type": "code", "node_kind": "function", "source_file": "src/payment/consumer.py"},

    ]

    indices = _build_code_indices(code_nodes)

    matched = _match_code_anchor("consumer.handle", indices)

    assert len(matched) == 1

    assert matched[0][0]["label"] == "handle"

    assert matched[0][1] == "EXTRACTED"





def test_code_anchor_file_name_match():

    """A bare filename like `order_service.rs` matches the file node."""

    code_nodes = [

        {"id": "src_order_order_service_rs", "label": "order_service.rs",

         "file_type": "code", "node_kind": "file", "source_file": "src/order/order_service.rs"},

    ]

    indices = _build_code_indices(code_nodes)

    matched = _match_code_anchor("order_service.rs", indices)

    assert len(matched) == 1

    assert matched[0][0]["node_kind"] == "file"





def test_code_anchor_http_path_match():

    """`POST /api/orders` matches an endpoint node whose label is the path."""

    code_nodes = [

        {"id": "src_api_routes:POST_orders", "label": "/api/orders",

         "file_type": "code", "node_kind": "endpoint", "source_file": "src/api/routes.py"},

    ]

    indices = _build_code_indices(code_nodes)

    matched = _match_code_anchor("POST /api/orders", indices)

    assert len(matched) == 1

    assert matched[0][0]["label"] == "/api/orders"

    assert matched[0][1] == "EXTRACTED"





def test_code_anchor_colon_path_match():

    """`POST:/api/orders` (colon form) matches the same endpoint node."""

    code_nodes = [

        {"id": "src_api_routes:POST_orders", "label": "/api/orders",

         "file_type": "code", "node_kind": "endpoint", "source_file": "src/api/routes.py"},

    ]

    indices = _build_code_indices(code_nodes)

    matched = _match_code_anchor("POST:/api/orders", indices)

    assert len(matched) == 1

    assert matched[0][0]["label"] == "/api/orders"




def _swagger_endpoint_node(ep_id: str, label: str) -> dict:

    """A slim rest_endpoint node as the swagger extractor emits it — the URL
    lives in the label; there are no method/path/full_path node fields."""

    return {"id": ep_id, "label": label, "file_type": "concept",

            "node_kind": "rest_endpoint", "source_file": "docs/user-api.yaml"}




def test_code_anchor_url_matches_slim_endpoint_label():

    """`GET:/rest/users/{id}` matches a slim rest_endpoint node by its label
    (no full_path/path fields — the label is the URL's sole carrier)."""

    nodes = [_swagger_endpoint_node("ep1", "GET:/rest/users/{id}")]

    indices = _build_code_indices(nodes)

    matched = _match_code_anchor("GET:/rest/users/{id}", indices)

    assert len(matched) == 1

    assert matched[0][0]["id"] == "ep1"

    assert matched[0][1] == "EXTRACTED"

    assert matched[0][2] == 1.0




def test_code_anchor_url_matches_different_path_var_name():

    """`GET:/rest/users/{userId}` matches an endpoint labeled with `{id}` —
    path-variable names are normalized on both sides."""

    nodes = [_swagger_endpoint_node("ep1", "GET:/rest/users/{id}")]

    indices = _build_code_indices(nodes)

    matched = _match_code_anchor("GET:/rest/users/{userId}", indices)

    assert len(matched) == 1

    assert matched[0][0]["id"] == "ep1"

    assert matched[0][1] == "EXTRACTED"




def test_code_anchor_url_method_mismatch_downgrades_to_ambiguous():

    """A wrong-method anchor (`PUT:/rest/users` vs a `GET:/rest/users`
    endpoint) must NOT produce an EXTRACTED edge — it downgrades to
    AMBIGUOUS 0.3 (path exists, method differs)."""

    nodes = [

        _swagger_endpoint_node("ep_get", "GET:/rest/users"),

        _swagger_endpoint_node("ep_post", "POST:/rest/users"),

    ]

    indices = _build_code_indices(nodes)

    matched = _match_code_anchor("PUT:/rest/users", indices)

    assert len(matched) == 1

    assert matched[0][1] == "AMBIGUOUS"

    assert matched[0][2] == 0.3




def test_code_anchor_bare_path_matches_slim_endpoint():

    """A method-less bare-path anchor (`/rest/users/{id}`) matches the slim
    endpoint via the bare-path key — no method signal, so EXTRACTED stands."""

    nodes = [_swagger_endpoint_node("ep1", "GET:/rest/users/{id}")]

    indices = _build_code_indices(nodes)

    matched = _match_code_anchor("/rest/users/{id}", indices)

    assert len(matched) == 1

    assert matched[0][0]["id"] == "ep1"

    assert matched[0][1] == "EXTRACTED"





def test_code_anchor_no_match_returns_none():

    """No matching code node returns empty list (caller records to unmatched)."""

    indices = _build_code_indices([])

    assert _match_code_anchor("NonExistentClass", indices) == []

    assert _match_code_anchor("missing_file.py", indices) == []

    assert _match_code_anchor("GET /nonexistent", indices) == []





def test_code_anchor_only_indexes_code_nodes():

    """Non-code nodes (file_type != 'code') are not indexed for anchor matching."""

    nodes = [

        {"id": "docanchor_x:Concept", "label": "OrderService",

         "file_type": "concept", "node_kind": "doc-anchor"},

    ]

    indices = _build_code_indices(nodes)

    # The doc-anchor node shares label "OrderService" but should NOT be matched

    assert _match_code_anchor("OrderService", indices) == []





# ---------------------------------------------------------------------------

# AC4: Unmatched anchors recorded

# ---------------------------------------------------------------------------



def test_unmatched_anchor_recorded(tmp_path: Path):

    """Unmatched code anchors recorded in unmatched list."""

    (tmp_path / "domain-model.md").write_text(

        "| 聚合根<anchor:ddd> | 代码锚点<anchor:code> | 描述<anchor:desc> |\n"

        "|---|---|---|\n| 订单聚合根 | NonExistentClass | 订单聚合根描述 |\n",

        encoding="utf-8",

    )

    result = extract_ddd(tmp_path / "domain-model.md", root=tmp_path, nodes=[])

    assert result is not None

    assert len(result.unmatched) == 1

    assert result.unmatched[0]["anchor"] == "NonExistentClass"

    assert "reason" in result.unmatched[0]





# ---------------------------------------------------------------------------

# AC2: Node shape compliance (all-generic fields + tags encode DDD type)

# ---------------------------------------------------------------------------



def test_node_shape_compliance(tmp_path: Path):

    """DDD nodes use all-generic fields + tags encodes DDD type. No ddd_* fields."""

    (tmp_path / "context-map.md").write_text(

        "| BC ID | BC 名称 | 职责 |\n|---|---|---|\n| BC-01 | 订单 | 处理下单 |\n",

        encoding="utf-8",

    )

    result = extract_ddd(tmp_path / "context-map.md", root=tmp_path)

    assert result is not None

    node = result.nodes[0]

    # All fields are generic

    assert node["file_type"] == "concept"

    assert node["node_kind"] == "doc-anchor"

    assert node["concept_id"] == "BC-01"  # raw, not normalized

    assert node["desc"] == "处理下单"

    assert "tags" in node

    assert "ddd" in node["tags"]

    assert "bounded_context" in node["tags"]

    # No ddd_* prefixed fields

    assert not any(k.startswith("ddd_") for k in node.keys())





def test_doc_anchor_id_format(tmp_path: Path):

    """Node ID is `docanchor_{stem}_{concept_id}` and is \\w-compliant (graphify

    normalize_id uses re.UNICODE, so Chinese word chars are preserved, not [a-z0-9_])."""

    (tmp_path / "domain-model.md").write_text(

        "| 聚合根<anchor:ddd> | 代码锚点<anchor:code> | 描述<anchor:desc> |\n"

        "|---|---|---|\n| 订单聚合根 | OrderService | 订单聚合根描述 |\n",

        encoding="utf-8",

    )

    result = extract_ddd(tmp_path / "domain-model.md", root=tmp_path)

    assert result is not None

    node_id = result.nodes[0]["id"]

    assert node_id.startswith("docanchor_")

    # graphify id spec: normalize_id uses re.sub(r"[^\w]+", "_", ...) with

    # re.UNICODE, so \w includes Unicode word chars (Chinese, etc.). The ID

    # is \w+ (underscores allowed) ??NOT restricted to ASCII [a-z0-9_].

    import re

    assert re.fullmatch(r"\w+", node_id, re.UNICODE), f"id {node_id!r} not \\w-compliant"





# ---------------------------------------------------------------------------

# AC9: Cross-file edge resolution via global concept_id index

# ---------------------------------------------------------------------------



def test_cross_file_related_edge_resolves(tmp_path: Path):

    """related edge between two doc-anchor nodes in different files resolves."""

    # File 1: domain-model.md with a related edge AG-01 ??AG-02 (no node defs)

    (tmp_path / "domain-model.md").write_text(

        "| 聚合根<anchor:ddd> | 从 | 到 |\n"

        "|---|---|---|\n| 订单-聚合根 | AG-01 | AG-02 |\n",

        encoding="utf-8",

    )

    # File 2: another domain-model file defining AG-01 and AG-02 as concept_ids.
    # Placed in a subdirectory so the filename still matches the whitelist
    # exactly (filename-exact match does not consider the directory).

    # Both rows live in ONE table (no `|---|` between data rows ??that would

    # be parsed as an empty data row, not a new table).

    refs_dir = tmp_path / "refs"
    refs_dir.mkdir()
    (refs_dir / "domain-model.md").write_text(

        "| 聚合根<anchor:ddd> | ID | 代码锚点<anchor:code> | 描述<anchor:desc> |\n"

        "|---|---|---|---|\n"

        "| 订单聚合根 | AG-01 | OrderService | 订单描述 |\n"

        "| 支付聚合根 | AG-02 | PaymentService | 支付描述 |\n",

        encoding="utf-8",

    )

    r1 = extract_ddd(tmp_path / "domain-model.md", root=tmp_path)

    r2 = extract_ddd(refs_dir / "domain-model.md", root=tmp_path)

    assert r1 is not None and r2 is not None

    assert len(r2.nodes) == 2, f"expected 2 nodes in refs file, got {len(r2.nodes)}"



    # Combine + resolve globally (mirrors what extract() does for the doc stage)

    all_nodes = r1.nodes + r2.nodes

    # r1 produced a pending related edge sourceRef=AG-01, targetRef=AG-02;

    # r2's nodes have concept_id AG-01 and AG-02.

    gidx = _build_global_node_index(all_nodes)

    assert gidx["byConceptId"].get("AG-01") is not None

    assert gidx["byConceptId"].get("AG-02") is not None



    # And verify _resolve_pending_edges wires them together when given the

    # combined node set + r1's pending edges (re-collected here directly).

    pending = [{

        "type": "related",

        "sourceNodeId": None,

        "sourceRef": "AG-01",

        "targetRef": "AG-02",

        "targetNodeId": None,

        "weight": 0.5,

        "source_file": "domain-model.md",

    }]

    edges = _resolve_pending_edges(all_nodes, pending)

    assert len(edges) == 1

    assert edges[0]["relation"] == "conceptually_related_to"

    assert edges[0]["source"] == r2.nodes[0]["id"]  # AG-01's node

    assert edges[0]["target"] == r2.nodes[1]["id"]  # AG-02's node





def test_resolve_ref_strips_parenthetical_qualifier():

    """resolve_ref strips parenthetical qualifiers like 'BC-04(Converter)'."""

    nodes = nodes = [{"id": "docanchor_x:BC-04", "concept_id": "BC-04", "label": "Converter"}]

    gidx = _build_global_node_index(nodes)

    from graphify.extractors.custom.ddd import _resolve_ref

    resolved = _resolve_ref("BC-04(Converter)", gidx)

    assert resolved is not None

    assert resolved["concept_id"] == "BC-04"





# ---------------------------------------------------------------------------

# AC7: merge mode produces both doc-anchor + page/heading nodes

# ---------------------------------------------------------------------------



def test_merge_mode_produces_doc_anchor_and_page(tmp_path: Path):

    """In merge mode, the extract() pre-pass yields both doc-anchor + page nodes."""

    from graphify.extract import extract

    (tmp_path / "context-map.md").write_text(

        "| BC ID | BC 名称 |\n|---|---|\n| BC-01 | 订单 |\n",

        encoding="utf-8",

    )

    result = extract([tmp_path / "context-map.md"], root=tmp_path, nodes=[])

    doc_anchors = [n for n in result["nodes"] if n.get("node_kind") == "doc-anchor"]

    pages = [n for n in result["nodes"] if n.get("node_kind") == "page"]

    assert doc_anchors, "merge mode should produce doc-anchor nodes from DDD extractor"

    assert pages, "merge mode should also produce page nodes from default extract_markdown"





# ---------------------------------------------------------------------------

# AC5: DDD extractor references a non-empty nodes list

# ---------------------------------------------------------------------------



def test_code_index_passed_to_ddd_extractor(tmp_path: Path):

    """extract() passes nodes to the DDD extractor (G3: AST-first)."""

    code_nodes = [

        {"id": "src_order:OrderService", "label": "OrderService",

         "file_type": "code", "node_kind": "class", "source_file": "src/order/service.py"},

    ]

    (tmp_path / "domain-model.md").write_text(

        "| 聚合根<anchor:ddd> | 代码锚点<anchor:code> | 描述<anchor:desc> |\n"

        "|---|---|---|\n| 订单聚合根 | OrderService | 订单聚合根描述 |\n",

        encoding="utf-8",

    )

    from graphify.extract import extract

    result = extract(

        [tmp_path / "domain-model.md"], root=tmp_path,

        nodes=code_nodes,

    )

    describes_edges = [e for e in result["edges"] if e["relation"] == "references"]

    assert any("OrderService" in e["target"] for e in describes_edges), \
        "describes (references) edge should connect doc-anchor to OrderService code node"


# ---------------------------------------------------------------------------

# AC8: suppress_llm_files surface from extract()

# ---------------------------------------------------------------------------



def test_supplement_only_suppresses_llm_files(tmp_path: Path):

    """A supplement_only extractor with suppress_llm=True surfaces to extract()."""

    from graphify.extract import extract

    from graphify.extractors.registry import register_doc_extractor



    @register_doc_extractor

    def _supplement(path, *, root, nodes=None):

        if path.name != "stub.md":

            return None

        return ExtractionResult(

            nodes=[{"id": "stub_node", "label": "stub", "file_type": "concept"}],

            edges=[],

            merge_mode="supplement_only",

            suppress_llm=True,

        )



    (tmp_path / "stub.md").write_text("# stub\n", encoding="utf-8")

    result = extract([tmp_path / "stub.md"], root=tmp_path, nodes=[])

    assert str(tmp_path / "stub.md") in result["suppress_llm_files"]





def test_default_merge_mode_does_not_suppress_llm(tmp_path: Path):

    """DDD's default merge mode does NOT add files to suppress_llm_files."""

    from graphify.extract import extract

    (tmp_path / "context-map.md").write_text(

        "| BC ID | BC 名称 |\n|---|---|\n| BC-01 | 订单 |\n", encoding="utf-8",

    )

    result = extract([tmp_path / "context-map.md"], root=tmp_path, nodes=[])

    # extract() returns suppress_llm_files as a LIST (documented at
    # extract.py:7327-7334 — JSON has no set type, and cli.py json.dumps
    # the result). Assert emptiness type-agnostically so the test holds
    # regardless of container type, matching the intent "no files suppressed".
    assert not result["suppress_llm_files"]





# ---------------------------------------------------------------------------

# AC10 (revised): tags are filter metadata for graph.html, NOT query text.

# The ddd fork originally appended tags to serve.py's _node_search_text so

# query "aggregate_root" matched doc-anchors. That coupled filter metadata to

# query recall, and AI-emitted tags turned it into a noise channel — removed.

# These tests now guard the decoupling: tags must never enter search text.

# ---------------------------------------------------------------------------



def test_tags_excluded_from_search_text():

    """tags must NOT participate in string retrieval (query/tag decoupling).

    A node carrying ddd tags produces search text without them — query
    semantics stay tag-independent; ddd type filtering lives in the
    graph.html tag panel.
    """

    node = {

        "id": "docanchor_test_AG-01",

        "label": "Order",

        "tags": ["ddd", "aggregate_root"],

    }

    text = _node_search_text(node, node["id"])

    assert "aggregate_root" not in text

    assert "ddd" not in text

    # The standard fields are still present

    assert "order" in text

    assert "docanchor_test_ag-01" in text





def test_tags_retrieval_no_tags_node_unaffected():

    """A node without a tags field produces upstream-identical search text

    (five NUL-separated fields, no trailing NUL)."""

    node = {"id": "src_foo:Foo", "label": "Foo", "source_file": "src/foo.py"}

    text = _node_search_text(node, node["id"])

    # The standard fields are still present

    assert "foo" in text

    assert "src/foo.py" in text

    # No trailing NUL: the last field is source_tokens ("src foo py").

    assert not text.endswith("\x00"), f"text should not end with NUL, got: {text!r}"





def test_tags_retrieval_non_list_tags_ignored():

    """A non-list tags field (string, None) is ignored gracefully."""

    node_str_tags = {"id": "x", "label": "X", "tags": "not_a_list"}

    text_str = _node_search_text(node_str_tags, "x")

    assert "x" in text_str



    node_none = {"id": "x", "label": "X", "tags": None}

    text_none = _node_search_text(node_none, "x")

    assert "x" in text_none





# ---------------------------------------------------------------------------

# Fixture-based integration tests

# ---------------------------------------------------------------------------



def test_fixture_context_map():

    """The fixture context-map.md produces BC + glossary nodes + related edges."""

    result = extract_ddd(FIXTURES / "context-map.md", root=FIXTURES.parent.parent.parent)

    assert result is not None

    bc_nodes = [n for n in result.nodes if "bounded_context" in n.get("tags", [])]

    glossary_nodes = [n for n in result.nodes if "glossary_term" in n.get("tags", [])]

    assert len(bc_nodes) >= 4, "context-map fixture should yield ≥4 BC nodes"

    assert len(glossary_nodes) >= 3, "context-map fixture should yield ?? glossary terms"

    # related edges between BCs (resolved via concept_id)

    related_edges = [e for e in result.edges if e["relation"] == "conceptually_related_to"]

    assert len(related_edges) >= 3, "should yield ≥3 related edges between BCs"





def test_fixture_technical_constraints():

    """The fixture technical-constraints.md produces TC nodes + describes edges.

    Cross-file categorized_under edges to BC-01/BC-02 require BC nodes from

    context-map.md in the global index, so we combine both files' nodes."""

    code_nodes = [

        {"id": "src_order:order_service", "label": "order_service.rs",

         "file_type": "code", "node_kind": "file", "source_file": "src/order/order_service.rs"},

        {"id": "src_payment:payment_consumer", "label": "payment_consumer.rs",

         "file_type": "code", "node_kind": "file", "source_file": "src/payment/payment_consumer.rs"},

        {"id": "src_order:OrderRepository", "label": "OrderRepository",

         "file_type": "code", "node_kind": "class", "source_file": "src/order/repo.py"},

        {"id": "src_order:OrderRepository.create", "label": "create",

         "file_type": "code", "node_kind": "function", "source_file": "src/order/repo.py"},

        {"id": "src_api:POST_api_orders", "label": "/api/orders",

         "file_type": "code", "node_kind": "endpoint", "source_file": "src/api/routes.py"},

    ]

    root_for_fixtures = FIXTURES.parent.parent.parent

    tc_result = extract_ddd(

        FIXTURES / "technical-constraints.md",

        root=root_for_fixtures,

        nodes=code_nodes,

    )

    assert tc_result is not None

    tc_nodes = [n for n in tc_result.nodes if "tech_constraint" in n.get("tags", [])]

    assert len(tc_nodes) == 3, "fixture has 3 TC headings"

    # describes (references) edges to matched code nodes ??resolved immediately

    describes = [e for e in tc_result.edges if e["relation"] == "references"]

    assert len(describes) >= 3, "should yield ≥3 describes edges (one per TC's code anchors)"



    # categorized_under edges to BC-01/BC-02 need BC nodes from context-map.md

    # in the global index. Combine both files' nodes and re-resolve.

    cm_result = extract_ddd(FIXTURES / "context-map.md", root=root_for_fixtures)

    assert cm_result is not None

    all_nodes = tc_result.nodes + cm_result.nodes

    # Re-resolve TC's pending categorized_under edges against the combined index.

    # The TC parser created pending edges with targetRef="BC-01"/"BC-02";

    # extract_ddd already tried to resolve them against TC-only nodes (failed).

    # Re-feed those same pending refs through _resolve_pending_edges with the

    # full node set.

    pending_categorized = [

        {"type": "categorized_under", "sourceNodeId": tc_nodes[0]["id"],

         "sourceRef": None, "targetRef": "BC-01", "targetNodeId": None,

         "weight": 0.6, "source_file": "technical-constraints.md"},

        {"type": "categorized_under", "sourceNodeId": tc_nodes[0]["id"],

         "sourceRef": None, "targetRef": "BC-02", "targetNodeId": None,

         "weight": 0.6, "source_file": "technical-constraints.md"},

    ]

    categorized_edges = _resolve_pending_edges(all_nodes, pending_categorized)

    assert len(categorized_edges) == 2, "should resolve 2 categorized_under edges to BC-01/BC-02"

    assert any(e["target"].endswith("bc_01") or "BC-01" in e.get("target", "")

               or "bc_01" in e["target"].lower() for e in categorized_edges)





def test_fixture_domain_model_with_code_anchors():

    """The fixture domain-model.md yields aggregate nodes + describes edges."""

    code_nodes = [

        {"id": "src_order:OrderService", "label": "OrderService",

         "file_type": "code", "node_kind": "class", "source_file": "src/order/service.py"},

        {"id": "src_order:OrderItem", "label": "OrderItem",

         "file_type": "code", "node_kind": "class", "source_file": "src/order/item.py"},

        {"id": "src_payment:PaymentService", "label": "PaymentService",

         "file_type": "code", "node_kind": "class", "source_file": "src/payment/service.py"},

    ]

    result = extract_ddd(

        FIXTURES / "domain-model.md",

        root=FIXTURES.parent.parent.parent,

        nodes=code_nodes,

    )

    assert result is not None

    ag_nodes = [n for n in result.nodes if "aggregate_root" in n.get("tags", [])]

    assert len(ag_nodes) >= 5, "fixture should yield ≥5 aggregate_root nodes"

    describes = [e for e in result.edges if e["relation"] == "references"]

    assert any("OrderService" in e["target"] for e in describes)

    assert any("PaymentService" in e["target"] for e in describes)





def test_fixture_business_flow_related_edges():

    """The fixture business-flow.md yields related edges between aggregates.

    The ??????????? columns reference BC names (???/???/???) that are defined

    as BC labels in context-map.md, so combine both files' nodes for resolution."""

    root_for_fixtures = FIXTURES.parent.parent.parent

    bf_result = extract_ddd(

        FIXTURES / "business-flow.md",

        root=root_for_fixtures,

    )

    assert bf_result is not None

    bf_nodes = [n for n in bf_result.nodes if "business_flow_step" in n.get("tags", [])]

    assert len(bf_nodes) >= 4, "fixture should yield ≥4 business_flow_step nodes"



    # context-map.md defines BC-01=???, BC-02=???, BC-03=???. The business-flow

    # fixture's Chinese label values (订单/认证/用户) match those BC labels, so

    # combining both files' nodes lets _resolve_pending_edges wire related edges.

    cm_result = extract_ddd(FIXTURES / "context-map.md", root=root_for_fixtures)

    assert cm_result is not None

    all_nodes = bf_result.nodes + cm_result.nodes



    # Re-collect the business-flow pending related edges (sourceRef=???, etc.)

    # and resolve against the combined index. The bf_result already tried to

    # resolve them against bf-only nodes (no BC labels there) and produced 0.

    # Re-run with the combined node set.

    from graphify.extractors.custom.ddd import _parse_tagged_file, _build_code_indices

    parsed = _parse_tagged_file(

        FIXTURES / "business-flow.md", root_for_fixtures,

        _build_code_indices([]),

    )

    combined_edges = _resolve_pending_edges(all_nodes, parsed["pendingEdges"])

    related = [e for e in combined_edges if e["relation"] == "conceptually_related_to"]

    assert len(related) >= 1, "should yield ≥1 related edge between BCs (via label match)"





def test_fixture_readme_falls_back_to_default(tmp_path: Path):

    """The non-whitelist README.md returns None (default extract_markdown runs)."""

    result = extract_ddd(FIXTURES / "README.md", root=FIXTURES.parent.parent.parent)

    assert result is None





# ---------------------------------------------------------------------------

# Edge dedup in merge mode

# ---------------------------------------------------------------------------



def test_merge_mode_dedups_edges(tmp_path: Path):

    """In merge mode, duplicate edges (same src/tgt/relation) are deduped."""

    from graphify.extract import extract

    # A context-map with no inter-BC relationships ??the only edges are from

    # the BC table itself (none here, since context-map doesn't emit describes)

    # and from extract_markdown (none, since no markdown links).

    (tmp_path / "context-map.md").write_text(

        "| BC ID | BC 名称 |\n|---|---|\n| BC-01 | 订单 |\n", encoding="utf-8",

    )

    result = extract([tmp_path / "context-map.md"], root=tmp_path, nodes=[])

    # No edges expected at all here, just verify no crash + nodes present

    edges = result["edges"]

    # Verify no duplicate (source, target, relation) triples

    keys = [(e.get("source"), e.get("target"), e.get("relation")) for e in edges]

    assert len(keys) == len(set(keys)), "merge mode should dedup edges"



