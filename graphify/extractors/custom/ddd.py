"""DDD documentation extractor.

Parses DDD-style markdown docs (context-map / technical-constraints /
business-flow / invariants / contracts / domain-events / domain-model)
into doc-anchor nodes + describes/related/categorized_under/cites edges.

Reference implementation: Understand-Anything/understand-anything-plugin/
skills/understand-ddd/parse-ddd-tables.mjs (ported to Python line-by-line).

Registered via graphify.extractors.registry; tried BEFORE extract_markdown
for .md files. Returns None for non-whitelist files (fall back to default).

Node modeling: all fields are generic (no ddd_* prefixed fields). DDD type
info is encoded into the generic 'tags' list field as:
    ["ddd", "<ddd_type>"]
so that graphify's string retrieval can match DDD types via tags.
"""
from __future__ import annotations

import re
from pathlib import Path

from graphify.extractors.base import _file_stem, _make_id
from graphify.extractors.registry import ExtractionResult, register_doc_extractor

# ---------------------------------------------------------------------------
# Constants (ported from parse-ddd-tables.mjs)
# ---------------------------------------------------------------------------

DDD_DOC_KEYWORDS: tuple[str, ...] = (
    "context-map",
    "technical-constraints",
    "business-flow",
    "invariants",
    "contracts",
    "domain-events",
    "domain-model",
)

HEADER_TAG_REGEX = re.compile(r"^(.+?)<anchor:(\w+)>$")
TABLE_SEP_REGEX = re.compile(r"^:?-+:?$")
FENCE_REGEX = re.compile(r"^(```+|~~~+)")

FROM_COLUMNS = ["从", "源聚合", "源BC"]
TO_COLUMNS = ["到", "目标聚合", "目标BC"]
AGGREGATE_REF_COLUMNS = ["归属聚合", "操作的聚合"]
BC_REF_COLUMNS = ["对端 BC"]

TC_HEADING_REGEX = re.compile(r"^###\s+(TC-\d+)\s*[:：]\s*(.+)$")
TC_CODE_ANCHOR_PREFIX = "**代码锚点**"
TC_SCOPE_PREFIX = "**适用范围**"
TC_REASON_PREFIX = "**选型理由"

MULTI_REF_SPLIT_REGEX = re.compile(r"[/]")
ANCHOR_SPLIT_REGEX = re.compile(r"[·→]")

# Code anchor formats (ported from ddd-code-matcher.mjs)
FILE_EXTENSIONS: frozenset[str] = frozenset({
    "rs", "ts", "tsx", "jsx", "js", "mjs", "py", "pyi", "go", "java", "rb",
    "c", "cpp", "h", "hpp", "toml", "yaml", "yml", "json", "md",
})
FILE_NAME_REGEX = re.compile(r"^[\w/\\-]+\.\w{1,5}$")
SNAKE_DOT_METHOD_REGEX = re.compile(r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$")
PASCAL_DOT_METHOD_REGEX = re.compile(r"^([A-Z][a-zA-Z0-9]+)\.([a-zA-Z_][a-zA-Z0-9_]*)$")
PASCAL_CASE_REGEX = re.compile(r"^[A-Z][a-zA-Z0-9]+$")
HTTP_URL_REGEX = re.compile(r"^(GET|POST|PUT|DELETE|PATCH)\s+\/.+$", re.IGNORECASE)
HTTP_COLON_URL_REGEX = re.compile(r"^(GET|POST|PUT|DELETE|PATCH):\/(.+)$", re.IGNORECASE)
PATH_URL_REGEX = re.compile(r"^\/.+")


# ---------------------------------------------------------------------------
# Code anchor matching (ported from ddd-code-matcher.mjs)
# ---------------------------------------------------------------------------

_PATH_VAR_RE = re.compile(r"\{[^}]+\}")


def _normalize_path_vars(p: str) -> str:
    """Normalize path variables: ``/rest/users/{userId}`` → ``/rest/users/{}``.

    DDD docs may use ``{id}`` while the swagger endpoint's ``full_path`` carries
    ``{userId}``. Without normalization these never match. This rewrites every
    ``{...}`` segment to ``{}`` so path-variable anchors match regardless of the
    variable name.
    """
    return _PATH_VAR_RE.sub("{}", p)


def _basename_without_ext(file_path: str) -> str:
    from os.path import basename, splitext
    base = basename(file_path)
    return splitext(base)[0]


def _is_class_node(n: dict) -> bool:
    """Check if a node represents a class declaration.

    graphify's TS/JS AST extractor does not set ``node_kind`` on code nodes
    (only the markdown extractor sets it for ``page``/``heading``). Instead,
    callable classes carry the ``_callable_class`` marker. We accept either
    signal so the DDD matcher works across all graphify language extractors.
    """
    if n.get("node_kind") == "class":
        return True
    return bool(n.get("_callable_class"))


def _is_function_node(n: dict) -> bool:
    """Check if a node represents a function/method declaration.

    Like ``_is_class_node``, falls back to graphify's ``_callable`` marker
    when ``node_kind`` is absent (TS/JS extractor produces only callable
    markers, not ``node_kind``).
    """
    if n.get("node_kind") in ("function", "method_definition", "function_definition"):
        return True
    return bool(n.get("_callable")) and not n.get("_callable_class")


def _is_file_node(n: dict) -> bool:
    """Check if a node represents a file-level node.

    A file node is the per-file node whose label is the filename. When
    ``node_kind`` is absent, we infer it from the label matching the
    basename of ``source_file``.
    """
    if n.get("node_kind") == "file":
        return True
    label = n.get("label", "")
    sf = n.get("source_file", "")
    if label and sf:
        from os.path import basename
        return label == basename(sf) or label == sf
    return False


def _build_code_indices(graph_nodes: list[dict]) -> dict[str, dict]:
    """Build fileIndex / nameIndex / endpointIndex from existing AST nodes.

    Indexes nodes with file_type=="code" (AST-extracted) for class/function/file
    matching. Also indexes ``rest_endpoint`` nodes (file_type=="concept",
    node_kind=="rest_endpoint") into endpointIndex by their **path** (not label),
    so URL anchors like ``POST:/rest/auth/register`` match regardless of the
    HTTP method prefix in the label.
    """
    file_index: dict[str, list[dict]] = {}
    name_index: dict[str, list[dict]] = {}
    endpoint_index: dict[str, dict] = {}

    for node in graph_nodes:
        if not node or not node.get("id"):
            continue

        # Code nodes: class/function/file matching
        if node.get("file_type") == "code":
            source_file = node.get("source_file")
            if source_file:
                key = _basename_without_ext(source_file)
                if key:
                    file_index.setdefault(key, []).append(node)
            label = node.get("label")
            if label:
                name_index.setdefault(label, []).append(node)
                # Also index a normalized label (strip leading "." and
                # trailing "()") so "findByEmail" matches ".findByEmail()".
                norm = label.lstrip(".").rstrip("()")
                if norm and norm != label:
                    name_index.setdefault(norm, []).append(node)
            # Code nodes whose label is a bare path (e.g. "/api/orders")
            # are also endpoints (node_kind="endpoint" from AST extractors).
            if label and label.startswith("/"):
                endpoint_index[label] = node
                norm = label.rstrip("/")
                if norm and norm != label:
                    endpoint_index[norm] = node

        # Endpoint nodes (swagger rest_endpoint): index by path, not label.
        # The label is "POST:/rest/auth/register" — a URL anchor only
        # carries the path "/rest/auth/register", so indexing by label
        # would never match. Also index a path-variable-normalized form so
        # "{id}" and "{userId}" match each other.
        if node.get("node_kind") == "rest_endpoint":
            for path_key in ("full_path", "path"):
                p = node.get(path_key)
                if p:
                    endpoint_index[p] = node
                    endpoint_index[_normalize_path_vars(p)] = node
                    norm = p.rstrip("/")
                    if norm and norm != p:
                        endpoint_index[norm] = node
                        endpoint_index[_normalize_path_vars(norm)] = node

    return {"fileIndex": file_index, "nameIndex": name_index, "endpointIndex": endpoint_index}


def _match_code_anchor(anchor: str, indices: dict) -> list[tuple[dict, str, float]]:
    """Match a code anchor string against graph indices.

    Returns a list of ``(node, confidence, score)`` tuples — ALL matching
    candidates, not just the first. This lets the caller build an edge to
    every matching node when the anchor is ambiguous (e.g. two classes with
    the same name).

    - Unique match → ``[(..., "EXTRACTED", 1.0)]``
    - Multiple matches → all candidates with ``("AMBIGUOUS", 0.3)``
    - No match → ``[]``

    Anchor formats (priority order):

    0. File name with extension (``register_plugin.rs``) — fileIndex by basename
    1. snake_case ``file.method`` (``mirror_source_task.poll``) — fileIndex → function
    2. PascalCase.method (``OrderService.create``) — nameIndex class → same-file function
    3. PascalCase SimpleName (``OrderService``) — nameIndex by label
    3.5 Qualified name (``com.example.OrderService`` / ``module.OrderService``) —
        split last segment → nameIndex, disambiguate by source_file path hints
    4-6. URL formats (``POST /path`` / ``POST:/path`` / ``/path``) — endpointIndex

    When graphify's language extractors don't set ``node_kind`` (e.g. the
    TS/JS extractor), falls back to ``_callable_class`` / ``_callable``
    markers. When a PascalCase.method anchor can't find a method node (many
    extractors don't emit method-level nodes), falls back to the class node
    as a partial match with AMBIGUOUS confidence.
    """
    # 0. File name with known extension
    if FILE_NAME_REGEX.match(anchor):
        ext = anchor.rsplit(".", 1)[-1]
        if ext in FILE_EXTENSIONS:
            base = _basename_without_ext(anchor)
            candidates = indices["fileIndex"].get(base, [])
            file_nodes = [n for n in candidates if _is_file_node(n)]
            matched = file_nodes if file_nodes else candidates
            if len(matched) == 1:
                return [(matched[0], "EXTRACTED", 1.0)]
            elif len(matched) > 1:
                return [(n, "AMBIGUOUS", 0.3) for n in matched]

    # 1. snake_case file.method
    if SNAKE_DOT_METHOD_REGEX.match(anchor):
        dot_idx = anchor.index(".")
        file_hint = anchor[:dot_idx]
        method_name = anchor[dot_idx + 1:]
        candidates = indices["fileIndex"].get(file_hint, [])
        # Exact function matches first
        fn_matches = [n for n in candidates
                      if _is_function_node(n) and n.get("label") == method_name]
        if fn_matches:
            if len(fn_matches) == 1:
                return [(fn_matches[0], "EXTRACTED", 1.0)]
            return [(n, "AMBIGUOUS", 0.3) for n in fn_matches]
        # Fallback: file nodes themselves (method not emitted by extractor)
        file_nodes = [n for n in candidates if _is_file_node(n)]
        fb = file_nodes if file_nodes else (candidates[:1] if candidates else [])
        if len(fb) == 1:
            return [(fb[0], "EXTRACTED", 1.0)]
        elif len(fb) > 1:
            return [(n, "AMBIGUOUS", 0.3) for n in fb]

    # 2. PascalCase.method
    m = PASCAL_DOT_METHOD_REGEX.match(anchor)
    if m:
        class_name, method_name = m.group(1), m.group(2)
        class_candidates = indices["nameIndex"].get(class_name, [])
        class_nodes = [n for n in class_candidates if _is_class_node(n)]
        if not class_nodes:
            # Fallback: same-name non-class nodes
            class_nodes = class_candidates[:]
        if not class_nodes:
            return []
        results: list[tuple[dict, str, float]] = []
        for cls in class_nodes:
            fn_candidates = indices["nameIndex"].get(method_name, [])
            fns = [n for n in fn_candidates
                   if _is_function_node(n)
                   and n.get("source_file") == cls.get("source_file")]
            if fns:
                for fn in fns:
                    results.append((fn, "EXTRACTED", 1.0))
            else:
                # Fallback: class node (partial match)
                results.append((cls, "AMBIGUOUS", 0.3))
        # Dedup by node id (same node may match multiple classes)
        seen_ids: set[str] = set()
        deduped: list[tuple[dict, str, float]] = []
        for node, conf, score in results:
            if node["id"] not in seen_ids:
                seen_ids.add(node["id"])
                deduped.append((node, conf, score))
        if len(deduped) == 1:
            return [(deduped[0][0], "EXTRACTED", 1.0)]
        elif len(deduped) > 1:
            return [(n, "AMBIGUOUS", 0.3) for n, _, _ in deduped]
        return []

    # 3. PascalCase class name (SimpleName)
    if PASCAL_CASE_REGEX.match(anchor):
        candidates = indices["nameIndex"].get(anchor, [])
        class_candidates = [n for n in candidates if _is_class_node(n)]
        matched = class_candidates if class_candidates else candidates
        if len(matched) == 1:
            return [(matched[0], "EXTRACTED", 1.0)]
        elif len(matched) > 1:
            return [(n, "AMBIGUOUS", 0.3) for n in matched]
        return []

    # 3.5 Qualified name or partial path: com.example.OrderService / module.OrderService
    #    (has "." but not snake_case.method or PascalCase.method format)
    if "." in anchor and not SNAKE_DOT_METHOD_REGEX.match(anchor) \
       and not PASCAL_DOT_METHOD_REGEX.match(anchor) \
       and not FILE_NAME_REGEX.match(anchor):
        parts = anchor.split(".")
        simple_name = parts[-1]
        path_hints = parts[:-1]
        candidates = indices["nameIndex"].get(simple_name, [])
        if not candidates:
            return []
        if not path_hints:
            # Just "module.Name" with single path segment — treat like SimpleName
            if len(candidates) == 1:
                return [(candidates[0], "EXTRACTED", 1.0)]
            return [(n, "AMBIGUOUS", 0.3) for n in candidates]
        path_str = "/".join(p.lower() for p in path_hints)
        matched_exact: list[dict] = []
        matched_ambiguous: list[dict] = []
        for n in candidates:
            sf = (n.get("source_file") or "").lower().replace("\\", "/")
            if path_str in sf:
                matched_exact.append(n)
            else:
                matched_ambiguous.append(n)
        if matched_exact:
            if len(matched_exact) == 1:
                return [(matched_exact[0], "EXTRACTED", 1.0)]
            return [(n, "AMBIGUOUS", 0.3) for n in matched_exact]
        if matched_ambiguous:
            return [(n, "AMBIGUOUS", 0.3) for n in matched_ambiguous]
        return []

    # 4. URL — HTTP method + space + path
    if HTTP_URL_REGEX.match(anchor):
        space_idx = anchor.index(" ")
        path = anchor[space_idx + 1:].strip()
        _endpoint = indices["endpointIndex"].get(path)
        if not _endpoint:
            _endpoint = indices["endpointIndex"].get(_normalize_path_vars(path))
        if _endpoint:
            return [(_endpoint, "EXTRACTED", 1.0)]
        # Prefix match: anchor /rest matches endpoint /rest/users/{id}
        norm = path.rstrip("/") if len(path) > 1 else path
        prefix_matches = [(n, "AMBIGUOUS", 0.3)
                          for ep, n in indices["endpointIndex"].items()
                          if ep.startswith(norm)]
        return prefix_matches

    # 5. URL — HTTP method + colon + path
    m = HTTP_COLON_URL_REGEX.match(anchor)
    if m:
        raw_path = "/" + m.group(2)
        norm = raw_path.rstrip("/") if len(raw_path) > 1 else raw_path
        _endpoint = indices["endpointIndex"].get(norm)
        if not _endpoint:
            _endpoint = indices["endpointIndex"].get(_normalize_path_vars(norm))
        if _endpoint:
            return [(_endpoint, "EXTRACTED", 1.0)]
        # Also try exact raw (with trailing slash)
        _endpoint = indices["endpointIndex"].get(raw_path)
        if not _endpoint:
            _endpoint = indices["endpointIndex"].get(_normalize_path_vars(raw_path))
        if _endpoint:
            return [(_endpoint, "EXTRACTED", 1.0)]
        prefix_matches = [(n, "AMBIGUOUS", 0.3)
                          for ep, n in indices["endpointIndex"].items()
                          if ep.startswith(norm)]
        return prefix_matches

    # 6. bare path
    if PATH_URL_REGEX.match(anchor):
        norm = anchor.rstrip("/") if len(anchor) > 1 else anchor
        _endpoint = indices["endpointIndex"].get(norm)
        if not _endpoint:
            _endpoint = indices["endpointIndex"].get(_normalize_path_vars(norm))
        if _endpoint:
            return [(_endpoint, "EXTRACTED", 1.0)]
        _endpoint = indices["endpointIndex"].get(anchor)
        if not _endpoint:
            _endpoint = indices["endpointIndex"].get(_normalize_path_vars(anchor))
        if _endpoint:
            return [(_endpoint, "EXTRACTED", 1.0)]
        prefix_matches = [(n, "AMBIGUOUS", 0.3)
                          for ep, n in indices["endpointIndex"].items()
                          if ep.startswith(norm)]
        return prefix_matches

    return []


# ---------------------------------------------------------------------------
# Fence-aware line scanner (ported from parse-ddd-tables.mjs:105-128)
# ---------------------------------------------------------------------------

def _scan_lines_with_fence(content: str) -> list[dict]:
    lines = content.split("\n")
    result = []
    in_fence = False
    fence_marker = None
    for i, line in enumerate(lines):
        fence_match = FENCE_REGEX.match(line)
        if fence_match:
            if not in_fence:
                in_fence = True
                fence_marker = fence_match.group(1)[0]
            elif fence_marker and line.startswith(fence_marker):
                in_fence = False
                fence_marker = None
            result.append({"lineNum": i + 1, "line": line, "inFence": True})
            continue
        result.append({"lineNum": i + 1, "line": line, "inFence": in_fence})
    return result


# ---------------------------------------------------------------------------
# Table parsing (ported from parse-ddd-tables.mjs:77-99)
# ---------------------------------------------------------------------------

def _parse_table_block(table_lines: list[str]) -> dict | None:
    if len(table_lines) < 2:
        return None

    def parse_row(line: str) -> list[str]:
        inner = line.strip()
        if inner.startswith("|"):
            inner = inner[1:]
        if inner.endswith("|"):
            inner = inner[:-1]
        return [c.strip() for c in inner.split("|")]

    headers = parse_row(table_lines[0])
    sep = parse_row(table_lines[1])
    if not all(TABLE_SEP_REGEX.match(c) for c in sep):
        return None
    return {"headers": headers, "rows": [parse_row(l) for l in table_lines[2:]]}


def _parse_header_tags(headers: list[str]) -> dict[str, dict] | None:
    tags: dict[str, dict] = {}
    for i, h in enumerate(headers):
        m = HEADER_TAG_REGEX.match(h)
        if m:
            tags[m.group(2)] = {"colIndex": i, "dddType": m.group(1).strip()}
    return tags if tags else None


def _split_anchors(cell_value: str) -> list[str]:
    """Split a cell value into individual anchor strings. Handles · and → separators."""
    if not cell_value:
        return []
    return [
        s.strip().strip("`").strip()
        for s in ANCHOR_SPLIT_REGEX.split(cell_value)
        if s.strip()
    ]


def _clean_anchor(anchor_str: str) -> str:
    r"""Normalize a raw anchor string for matching.

    1. Strip trailing qualifiers after whitespace: ``trait (#[async_trait])``
    2. Strip surrounding quotes/backticks: backtick-UserRepo-backtick -> UserRepo
    3. Strip surrounding backslashes: backslash-Logger-backslash -> Logger
    4. Strip surrounding single/double quotes: "key" -> key
    """
    s = re.sub(r"\s+.*$", "", anchor_str).strip()
    # Strip surrounding backslashes, backticks, single/double quotes
    s = s.strip("\\`'\"")
    return s


# ---------------------------------------------------------------------------
# Node + Edge builders (graphify-compatible shapes, all generic fields)
# ---------------------------------------------------------------------------

def _make_doc_anchor_id(doc_path: str, concept_id: str) -> str:
    """ID format: docanchor_{stem}_{conceptId}. Uses make_id for [a-z0-9_] compliance."""
    stem = _file_stem(Path(doc_path))
    return _make_id("docanchor", stem, concept_id)


def _infer_ddd_type(ddd_type_raw: str) -> str:
    """Infer machine-readable ddd_type from the <anchor:ddd> column name."""
    raw = ddd_type_raw.lower()
    if "聚合根" in raw or "aggregate" in raw:
        return "aggregate_root"
    if "领域事件" in raw or "event" in raw:
        return "domain_event"
    if "不变式" in raw or "invariant" in raw:
        return "invariant"
    if "限界上下文" in raw or "bounded context" in raw or raw.strip() == "bc":
        return "bounded_context"
    if "值对象" in raw or "value" in raw:
        return "value_object"
    if "领域服务" in raw:
        return "domain_service"
    if "契约" in raw or "contract" in raw:
        return "contract"
    if "流程" in raw or "flow" in raw:
        return "business_flow_step"
    if "术语" in raw or "glossary" in raw:
        return "glossary_term"
    if "约束" in raw or "constraint" in raw or raw.strip().startswith("tc"):
        return "tech_constraint"
    return "concept"


def _make_node(
    *, doc_path: str, concept_id: str, name: str,
    ddd_type: str, desc: str = "", line_num: int = 0,
) -> dict:
    """Build a doc-anchor node with all-generic fields.

    DDD type info is encoded into the generic 'tags' list field:
        ["ddd", "<ddd_type>"]
    so no ddd_* prefixed fields are needed on the node.
    """
    return {
        "id": _make_doc_anchor_id(doc_path, concept_id),
        "label": name,
        "file_type": "concept",
        "source_file": doc_path,
        "source_location": f"L{line_num}" if line_num else None,
        "node_kind": "doc-anchor",
        "desc": desc,
        "concept_id": concept_id,
        # Generic tags list — DDD type info encoded here for retrieval
        "tags": ["ddd", ddd_type],
    }


def _make_edge(
    *, source: str, target: str, relation: str,
    confidence: str = "EXTRACTED", confidence_score: float = 1.0,
    source_file: str, line_num: int = 0, weight: float = 0.5,
) -> dict:
    return {
        "source": source, "target": target, "relation": relation,
        "confidence": confidence, "confidence_score": confidence_score,
        "source_file": source_file,
        "source_location": f"L{line_num}" if line_num else None,
        "weight": weight,
    }


# ---------------------------------------------------------------------------
# R3: Tagged-table parser (ported from parse-ddd-tables.mjs:177-337)
# ---------------------------------------------------------------------------

def _parse_tagged_file(
    abs_path: Path, project_root: Path, indices: dict,
) -> dict:
    """Parse a single .md file for tagged DDD tables.

    Collects nodes + pending edges + unmatched anchors.
    Does NOT resolve internal edges — that happens in _resolve_pending_edges
    with the global index.
    """
    doc_path = abs_path.resolve().relative_to(project_root.resolve()).as_posix()
    content = abs_path.read_text(encoding="utf-8", errors="replace")
    scanned = _scan_lines_with_fence(content)

    nodes: list[dict] = []
    pending_edges: list[dict] = []
    unmatched: list[dict] = []

    i = 0
    while i < len(scanned):
        if scanned[i]["inFence"] or not scanned[i]["line"].strip().startswith("|"):
            i += 1
            continue
        block_start = i
        while i < len(scanned) and not scanned[i]["inFence"] and scanned[i]["line"].strip().startswith("|"):
            i += 1
        block_lines = [s["line"] for s in scanned[block_start:i]]

        parsed = _parse_table_block(block_lines)
        if not parsed:
            continue

        header_tags = _parse_header_tags(parsed["headers"])
        if not header_tags:
            continue  # No anchor tags — skip

        ddd_col = header_tags.get("ddd")
        if not ddd_col:
            continue

        desc_col = header_tags.get("desc")
        code_col = header_tags.get("code")
        ddd_type_raw = ddd_col["dddType"]
        ddd_type = _infer_ddd_type(ddd_type_raw)

        # Detect internal-edge columns using relaxed synonyms
        id_col_idx = next((idx for idx, h in enumerate(parsed["headers"]) if h.strip() == "ID"), -1)
        from_col_idx = next((idx for idx, h in enumerate(parsed["headers"]) if h.strip() in FROM_COLUMNS), -1)
        to_col_idx = next((idx for idx, h in enumerate(parsed["headers"]) if h.strip() in TO_COLUMNS), -1)
        agg_ref_col_idx = next((idx for idx, h in enumerate(parsed["headers"]) if h.strip() in AGGREGATE_REF_COLUMNS), -1)
        bc_ref_col_idx = next((idx for idx, h in enumerate(parsed["headers"]) if h.strip() in BC_REF_COLUMNS), -1)

        for row in parsed["rows"]:
            ddd_value = (row[ddd_col["colIndex"]] if ddd_col["colIndex"] < len(row) else "").strip()
            if not ddd_value:
                continue

            desc_value = (row[desc_col["colIndex"]] if desc_col and desc_col["colIndex"] < len(row) else "").strip()
            code_value = (row[code_col["colIndex"]] if code_col and code_col["colIndex"] < len(row) else "").strip()

            # concept_id: prefer ID column, else name
            concept_id = (
                row[id_col_idx].strip()
                if id_col_idx >= 0 and id_col_idx < len(row) and row[id_col_idx].strip()
                else ddd_value
            )

            node = _make_node(
                doc_path=doc_path, concept_id=concept_id, name=ddd_value,
                ddd_type=ddd_type,
                desc=desc_value, line_num=scanned[block_start]["lineNum"],
            )
            nodes.append(node)

            # --- Code anchors → describes edges (resolved immediately) ---
            if code_value:
                for anchor_str in _split_anchors(code_value):
                    # Strip trailing qualifiers like "trait (#[async_trait])"
                    # and surrounding quotes/backticks/backslashes
                    clean_anchor = _clean_anchor(anchor_str)
                    if not clean_anchor:
                        continue
                    candidates = _match_code_anchor(clean_anchor, indices)
                    if candidates:
                        for matched, conf, score in candidates:
                            pending_edges.append({
                                "type": "describes",
                                "sourceNodeId": node["id"],
                                "targetNodeId": matched["id"],
                                "confidence": conf,
                                "confidence_score": score,
                                "weight": 0.8 if conf == "EXTRACTED" else 0.3,
                                "source_file": doc_path,
                            })
                    else:
                        unmatched.append({
                            "source": "ddd",
                            "docPath": doc_path,
                            "conceptId": concept_id,
                            "anchor": clean_anchor,
                            "reason": "no matching code node",
                        })

            # --- from/to columns → related edges ---
            if from_col_idx >= 0 and to_col_idx >= 0:
                from_val = (row[from_col_idx] if from_col_idx < len(row) else "").strip()
                to_val = (row[to_col_idx] if to_col_idx < len(row) else "").strip()
                if from_val and to_val:
                    for fr in MULTI_REF_SPLIT_REGEX.split(from_val):
                        for tr in MULTI_REF_SPLIT_REGEX.split(to_val):
                            fr, tr = fr.strip(), tr.strip()
                            if fr and tr:
                                pending_edges.append({
                                    "type": "related",
                                    "sourceNodeId": None,
                                    "sourceRef": fr,
                                    "targetRef": tr,
                                    "targetNodeId": None,
                                    "weight": 0.5,
                                    "source_file": doc_path,
                                })

            # --- 归属聚合/操作的聚合 → categorized_under edges ---
            if agg_ref_col_idx >= 0:
                agg_val = (row[agg_ref_col_idx] if agg_ref_col_idx < len(row) else "").strip()
                if agg_val:
                    for ref in MULTI_REF_SPLIT_REGEX.split(agg_val):
                        ref = ref.strip()
                        if ref:
                            pending_edges.append({
                                "type": "categorized_under",
                                "sourceNodeId": node["id"],
                                "sourceRef": None,
                                "targetRef": ref,
                                "targetNodeId": None,
                                "weight": 0.6,
                                "source_file": doc_path,
                            })

            # --- 对端 BC → cites edges ---
            if bc_ref_col_idx >= 0:
                bc_val = (row[bc_ref_col_idx] if bc_ref_col_idx < len(row) else "").strip()
                if bc_val and bc_val != "外部":
                    pending_edges.append({
                        "type": "cites",
                        "sourceNodeId": node["id"],
                        "sourceRef": None,
                        "targetRef": bc_val,
                        "targetNodeId": None,
                        "weight": 0.7,
                        "source_file": doc_path,
                    })

    return {"nodes": nodes, "pendingEdges": pending_edges, "unmatched": unmatched}


# ---------------------------------------------------------------------------
# R6: context-map.md handler (ported from parse-ddd-tables.mjs:353-452)
# ---------------------------------------------------------------------------

def _parse_context_map(abs_path: Path, project_root: Path) -> dict:
    """Parse context-map.md which has no <anchor:...> tags.

    Extracts:
      - BC nodes from the "限界上下文" table (headers: BC ID, BC 名称, ...)
      - related edges from the "业务关系" table (headers: 从, 到, ...)
      - glossary nodes from the "统一语言" table (headers: 术语, 定义, ...)
    """
    doc_path = abs_path.resolve().relative_to(project_root.resolve()).as_posix()
    content = abs_path.read_text(encoding="utf-8", errors="replace")
    scanned = _scan_lines_with_fence(content)

    nodes: list[dict] = []
    pending_edges: list[dict] = []

    i = 0
    while i < len(scanned):
        if scanned[i]["inFence"] or not scanned[i]["line"].strip().startswith("|"):
            i += 1
            continue
        block_start = i
        while i < len(scanned) and not scanned[i]["inFence"] and scanned[i]["line"].strip().startswith("|"):
            i += 1
        block_lines = [s["line"] for s in scanned[block_start:i]]

        parsed = _parse_table_block(block_lines)
        if not parsed:
            continue

        headers = [h.strip() for h in parsed["headers"]]

        # --- BC table: headers include "BC ID" and "BC 名称" ---
        if "BC ID" in headers and "BC 名称" in headers:
            id_idx = headers.index("BC ID")
            name_idx = headers.index("BC 名称")
            desc_idx = next((idx for idx, h in enumerate(headers) if h.startswith("职责")), -1)

            for row in parsed["rows"]:
                bc_id = (row[id_idx] if id_idx < len(row) else "").strip()
                bc_name = (row[name_idx] if name_idx < len(row) else "").strip()
                if not bc_id or not bc_name:
                    continue
                nodes.append(_make_node(
                    doc_path=doc_path, concept_id=bc_id, name=bc_name,
                    ddd_type="bounded_context",
                    desc=(row[desc_idx] if desc_idx >= 0 and desc_idx < len(row) else "").strip(),
                    line_num=scanned[block_start]["lineNum"],
                ))
            continue

        # --- BC relationship table: headers include "从" and "到" ---
        if any(h in FROM_COLUMNS for h in headers) and any(h in TO_COLUMNS for h in headers):
            from_idx = next(idx for idx, h in enumerate(headers) if h in FROM_COLUMNS)
            to_idx = next(idx for idx, h in enumerate(headers) if h in TO_COLUMNS)

            for row in parsed["rows"]:
                from_val = (row[from_idx] if from_idx < len(row) else "").strip()
                to_val = (row[to_idx] if to_idx < len(row) else "").strip()
                if not from_val or not to_val or from_val == "外部" or to_val == "外部":
                    continue
                pending_edges.append({
                    "type": "related",
                    "sourceNodeId": None,
                    "sourceRef": from_val,
                    "targetRef": to_val,
                    "targetNodeId": None,
                    "weight": 0.5,
                    "source_file": doc_path,
                })
            continue

        # --- Glossary table: headers include "术语" and "定义" ---
        if "术语" in headers and "定义" in headers:
            term_idx = headers.index("术语")
            def_idx = headers.index("定义")

            for row in parsed["rows"]:
                term = (row[term_idx] if term_idx < len(row) else "").strip()
                if not term:
                    continue
                nodes.append(_make_node(
                    doc_path=doc_path, concept_id=term, name=term,
                    ddd_type="glossary_term",
                    desc=(row[def_idx] if def_idx >= 0 and def_idx < len(row) else "").strip(),
                    line_num=scanned[block_start]["lineNum"],
                ))
            continue

    return {"nodes": nodes, "pendingEdges": pending_edges}


# ---------------------------------------------------------------------------
# R7: technical-constraints.md handler (ported from parse-ddd-tables.mjs:464-569)
# ---------------------------------------------------------------------------

def _parse_technical_constraints(
    abs_path: Path, project_root: Path, indices: dict,
) -> dict:
    """Parse technical-constraints.md which uses `### TC-xxx:` headings and
    `**代码锚点**:` / `**适用范围**:` paragraph prefixes instead of tables.
    """
    doc_path = abs_path.resolve().relative_to(project_root.resolve()).as_posix()
    content = abs_path.read_text(encoding="utf-8", errors="replace")
    lines = content.split("\n")

    nodes: list[dict] = []
    pending_edges: list[dict] = []
    unmatched: list[dict] = []

    current_node: dict | None = None

    for i, line in enumerate(lines):
        trimmed = line.strip()
        # Strip leading `- ` (list item prefix) for paragraph-prefix checks
        stripped = re.sub(r"^-\s+", "", trimmed)

        # --- TC heading: `### TC-001: Title` ---
        tc_match = TC_HEADING_REGEX.match(trimmed)
        if tc_match:
            tc_id = tc_match.group(1)
            tc_title = tc_match.group(2).strip()
            current_node = _make_node(
                doc_path=doc_path, concept_id=tc_id, name=tc_title,
                ddd_type="tech_constraint",
                desc="", line_num=i + 1,
            )
            nodes.append(current_node)
            continue

        if not current_node:
            continue

        # --- **代码锚点**: `file.rs` · `other.rs` ---
        if stripped.startswith(TC_CODE_ANCHOR_PREFIX):
            anchor_str = re.sub(r"^[:：]\s*", "", stripped[len(TC_CODE_ANCHOR_PREFIX):]).strip()
            if anchor_str:
                for anchor in _split_anchors(anchor_str):
                    # Strip trailing qualifiers and surrounding quotes/backticks/backslashes
                    clean_anchor = _clean_anchor(anchor)
                    if not clean_anchor:
                        continue
                    candidates = _match_code_anchor(clean_anchor, indices)
                    if candidates:
                        for matched, conf, score in candidates:
                            pending_edges.append({
                                "type": "describes",
                                "sourceNodeId": current_node["id"],
                                "targetNodeId": matched["id"],
                                "confidence": conf,
                                "confidence_score": score,
                                "weight": 0.8 if conf == "EXTRACTED" else 0.3,
                                "source_file": doc_path,
                            })
                    else:
                        unmatched.append({
                            "source": "ddd",
                            "docPath": doc_path,
                            "conceptId": current_node["concept_id"],
                            "anchor": clean_anchor,
                            "reason": "no matching code node",
                        })

        # --- **适用范围**: BC-01 / 全局 ---
        if stripped.startswith(TC_SCOPE_PREFIX):
            scope_val = re.sub(r"^[:：]\s*", "", stripped[len(TC_SCOPE_PREFIX):]).strip()
            if scope_val and scope_val != "全局":
                for ref in re.split(r"[,，]", scope_val):
                    ref = ref.strip()
                    if ref and ref.startswith("BC-"):
                        pending_edges.append({
                            "type": "categorized_under",
                            "sourceNodeId": current_node["id"],
                            "sourceRef": None,
                            "targetRef": ref,
                            "targetNodeId": None,
                            "weight": 0.6,
                            "source_file": doc_path,
                        })

        # --- **选型理由（Why）**: → use as desc ---
        if stripped.startswith(TC_REASON_PREFIX):
            reason = re.sub(r"^\*\*选型理由[^*]*\*\*[:：]?\s*", "", stripped).strip()
            if reason and current_node:
                current_node["desc"] = reason

    return {"nodes": nodes, "pendingEdges": pending_edges, "unmatched": unmatched}


# ---------------------------------------------------------------------------
# Global edge resolver (ported from parse-ddd-tables.mjs:579-665)
# ---------------------------------------------------------------------------

def _build_global_node_index(all_nodes: list[dict]) -> dict:
    """Build concept_id → node and name → node index from ALL collected nodes.

    Uses the raw 'concept_id' node field (not the normalized id) to avoid
    the make_id normalization issue (paths/ids get lowercased + separators
    collapsed to _, breaking split-based recovery).
    """
    by_concept_id: dict[str, dict] = {}
    by_name: dict[str, dict] = {}

    for node in all_nodes:
        if not node.get("id", "").startswith("docanchor_"):
            continue
        concept_id = node.get("concept_id", "")
        if concept_id and concept_id not in by_concept_id:
            by_concept_id[concept_id] = node
        name = node.get("label", "")
        if name and name not in by_name:
            by_name[name] = node

    return {"byConceptId": by_concept_id, "byName": by_name}


def _resolve_ref(ref: str, global_index: dict) -> dict | None:
    """Resolve a reference (concept_id or name) to a node using the global index.

    Strips parenthetical qualifiers: "BC-04(Converter)" → "BC-04".
    Matches raw values (no normalization) — concept_id is stored raw on nodes.
    """
    if not ref:
        return None
    clean_ref = re.sub(r"\(.*\)", "", ref).strip()
    return global_index["byConceptId"].get(clean_ref) or global_index["byName"].get(clean_ref)


def _resolve_pending_edges(all_nodes: list[dict], pending_edges: list[dict]) -> list[dict]:
    """Resolve all pending edges using the global node index.

    - describes edges: already have targetNodeId, just materialize
    - related/categorized_under/cites: resolve sourceRef/targetRef via global index
    """
    global_index = _build_global_node_index(all_nodes)
    node_by_id = {n["id"]: n for n in all_nodes}
    edges: list[dict] = []
    seen: set[str] = set()

    relation_map = {
        "describes": "references",
        "related": "conceptually_related_to",
        "categorized_under": "conceptually_related_to",
        "cites": "cites",
    }

    for pe in pending_edges:
        source_node = None
        target_node = None

        if pe["type"] == "describes":
            # Already resolved — sourceNodeId + targetNodeId known
            source_node = node_by_id.get(pe["sourceNodeId"])
            target_node = {"id": pe["targetNodeId"]} if pe.get("targetNodeId") else None
        else:
            # Resolve via global index
            if pe.get("sourceNodeId"):
                source_node = node_by_id.get(pe["sourceNodeId"])
            elif pe.get("sourceRef"):
                source_node = _resolve_ref(pe["sourceRef"], global_index)

            if pe.get("targetNodeId"):
                target_node = {"id": pe["targetNodeId"]}
            elif pe.get("targetRef"):
                target_node = _resolve_ref(pe["targetRef"], global_index)

        if source_node and target_node:
            key = f"{source_node['id']}|{target_node['id']}|{pe['type']}"
            if key not in seen:
                seen.add(key)
                edges.append(_make_edge(
                    source=source_node["id"],
                    target=target_node["id"],
                    relation=relation_map.get(pe["type"], "references"),
                    confidence=pe.get("confidence", "EXTRACTED"),
                    confidence_score=pe.get("confidence_score", 1.0),
                    source_file=pe.get("source_file", ""),
                    weight=pe.get("weight", 0.5),
                ))

    return edges


# ---------------------------------------------------------------------------
# Public entry — returns ExtractionResult
# ---------------------------------------------------------------------------

def extract_ddd(
    path: Path, *, root: Path, nodes: list[dict] | None = None
) -> ExtractionResult | None:
    """Extract DDD concepts from a whitelist .md file. Returns None for non-whitelist.

    Whitelist match is filename-exact: ``path.name.lower()`` must equal
    ``f"{kw}.md"`` for some keyword in ``DDD_DOC_KEYWORDS``. Directory names
    never participate in the match, so a file under ``api/contracts/`` is not
    pulled in merely because the path contains ``contracts``.
    """
    filename = path.name.lower()
    if filename not in {f"{kw}.md" for kw in DDD_DOC_KEYWORDS}:
        return None

    # Build code indices from the nodes passed in by extract() (AST-first, G3).
    # ``nodes`` may include both fresh (this run's Stage 1/2) and persisted
    # (graph.json存量) code/config nodes — extract() is responsible for merging
    # them before calling external extractors, so ddd sees the full picture and
    # does NOT read graph.json itself.
    code_nodes = nodes if nodes else []
    indices = _build_code_indices(code_nodes)

    filename = path.name
    all_nodes: list[dict] = []
    pending_edges: list[dict] = []
    unmatched: list[dict] = []

    if filename == "context-map.md":
        result = _parse_context_map(path, root)
        all_nodes.extend(result["nodes"])
        pending_edges.extend(result["pendingEdges"])
    elif filename == "technical-constraints.md":
        result = _parse_technical_constraints(path, root, indices)
        all_nodes.extend(result["nodes"])
        pending_edges.extend(result["pendingEdges"])
        unmatched.extend(result["unmatched"])
    else:
        # Tagged-table parser for business-flow / invariants / contracts /
        # domain-events / domain-model
        result = _parse_tagged_file(path, root, indices)
        all_nodes.extend(result["nodes"])
        pending_edges.extend(result["pendingEdges"])
        unmatched.extend(result["unmatched"])

    edges = _resolve_pending_edges(all_nodes, pending_edges)

    # DDD 推荐 merge 模式：doc-anchor + page/heading 互补，LLM Tier 2 仍跑（通用 prompt）
    # pending_edges 原样返回供 extract() 做跨文件全局二次解析（spec §4.4）：
    # 单文件内已解析的边放在 edges 里；引用其他文件 concept_id/name 的边
    # 在本文件内无法解析，留给 extract() 收集所有文件节点后统一重解析。
    return ExtractionResult(
        nodes=all_nodes,
        edges=edges,
        hyperedges=[],
        merge_mode="merge",        # DDD：外部 + 默认 markdown 合并
        suppress_llm=False,        # LLM Tier 2 仍跑（通用 prompt 抓散文语义）
        unmatched=unmatched,
        pending_edges=pending_edges,
    )


register_doc_extractor(extract_ddd)
