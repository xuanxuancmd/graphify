"""Swagger / OpenAPI YAML extractor.

Parses swagger 2.0 / openapi 3.x YAML interface docs into ``rest_endpoint``
nodes plus ``references`` edges linking each endpoint to its controller class
and handler function in the already-extracted code AST (via ``nodes``).

Registered via :mod:`graphify.extractors.registry`; tried BEFORE
``extract_markdown`` for ``.yaml``/``.yml`` files. Returns ``None`` for
non-swagger yaml (docker-compose, CI configs, k8s manifests, ...) so those
fall back to the default markdown extractor.

Design mirrors :mod:`graphify.extractors.custom.ddd`:

- ``nodes`` shape: ``list[dict]`` of AST node dicts (built in
  ``cli.py`` stage 3 — doc extraction reuses stage 1's AST nodes +
  graph.json persisted code nodes).
- ``_build_code_indices``: nameIndex (label -> nodes), fileIndex
  (basename -> nodes) — same as DDD. Also returns ``main_language``: the
  backend main language detected by counting code nodes per
  ``source_file`` extension (see ``_detect_main_language``).
- ``_match_controller``: ``tags[0]`` -> class node via nameIndex. Java
  codegen fallback: when no class node matches the bare tag and
  ``main_language == "java"``, retry with an ``Impl`` suffix
  (swagger-codegen / openapi-generator emit ``<Name>Impl`` classes for
  Java).
- ``_match_handler``: ``operationId`` -> function node, preferring the one
  co-located with the matched controller's ``source_file``
  (PascalCase.method pattern from DDD).
- Edge relation: ``references`` (same as DDD's describes -> references).
- No shadow nodes: unmatched ``tags``/``operationId`` are recorded in
  ``unmatched`` for the GRAPH_REPORT, like DDD — never synthesized as nodes.
- ``suppress_llm=True``: Tier 1 only, zero LLM cost, fully deterministic.
  Swagger structure is closed-form; no prose semantics to enrich.

Swagger 2.0 vs OpenAPI 3.x field differences handled:

  ============  ======================  ===============================
  field         Swagger 2.0             OpenAPI 3.x
  ============  ======================  ===============================
  version key   ``swagger: "2.0"``      ``openapi: "3.0.x"``
  base path     ``basePath: /rest``     ``servers[0].url`` path part
  request body  ``parameters[in:body]`` ``requestBody``
  response      ``responses[code]``     ``responses[code]``
  mime types    ``produces``/``consumes`` ``content.<mime>``
  ============  ======================  ===============================
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

from graphify.extractors.base import _file_stem, _make_id
from graphify.extractors.registry import ExtractionResult, register_doc_extractor

_LOG = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: HTTP methods we extract as endpoints (lowercase, as they appear in yaml keys).
HTTP_METHODS: frozenset[str] = frozenset({
    "get", "post", "put", "delete", "patch", "head", "options",
})

#: File extensions this extractor claims.
SWAGGER_EXTENSIONS: frozenset[str] = frozenset({".yaml", ".yml"})

# ---------------------------------------------------------------------------
# Code index helpers — ported verbatim from ddd.py
# (graphify's language extractors set _callable_class / _callable markers
# instead of node_kind on TS/JS; we accept both signals so matching works
# across all 40+ language extractors.)
# ---------------------------------------------------------------------------


def _is_class_node(n: dict) -> bool:
    """True if node represents a class declaration (node_kind or _callable_class)."""
    if n.get("node_kind") == "class":
        return True
    return bool(n.get("_callable_class"))


def _is_function_node(n: dict) -> bool:
    """True if node represents a function/method declaration."""
    if n.get("node_kind") in ("function", "method_definition", "function_definition"):
        return True
    return bool(n.get("_callable")) and not n.get("_callable_class")


def _basename_without_ext(file_path: str) -> str:
    from os.path import basename, splitext
    return splitext(basename(file_path))[0]


def _normalize_label(label: str) -> str:
    """Normalize a code node label for name-index lookup.

    graphify's TS/JS extractor emits method labels as ``.methodName()`` —
    a leading dot marks class membership, a trailing ``()`` marks callability.
    Swagger ``operationId`` is the bare name (``handleRegister``), so a naive
    ``nameIndex[operationId]`` lookup misses every TS method. Strip the
    leading dot and trailing parens so ``.handleRegister()`` -> ``handleRegister``
    and matches the operationId.

    Class labels (``UserService``) have no dot/parens and pass through
    unchanged, so controller matching is unaffected.
    """
    s = label.strip()
    if s.startswith("."):
        s = s[1:]
    if s.endswith("()"):
        s = s[:-2]
    return s


def _detect_main_language(code_nodes: list[dict]) -> str:
    """Detect the backend main language by counting code nodes per language.

    Walks every ``file_type == "code"`` node, bins by ``source_file``
    extension (``.java`` -> ``"java"``, ``.ts`` -> ``"ts"``, ...), and
    returns the language with the most nodes (plurality). Returns ``""``
    when no code nodes are present or none have a recognisable extension.

    This is a heuristic for mixed-language repos. A project may contain
    Java backend code, TypeScript frontend, and Python/Shell build scripts
    simultaneously — but only the backend language matters for swagger
    controller matching. Build/tooling languages (Shell, Python for
    scripts) typically have far fewer AST nodes than application code, so
    they won't dominate the count. In a frontend-heavy repo where TS nodes
    outnumber Java nodes, ``main_language`` will be ``"ts"`` and the Impl
    fallback correctly stays off.

    Used by ``_match_controller`` to gate the Java codegen ``Impl`` suffix
    fallback — only fires when ``main_language == "java"``.
    """
    lang_counts: dict[str, int] = {}
    for node in code_nodes:
        if not node or node.get("file_type") != "code":
            continue
        source_file = node.get("source_file", "")
        if not source_file or "." not in source_file:
            continue
        ext = source_file.rsplit(".", 1)[-1].lower()
        if ext:
            lang_counts[ext] = lang_counts.get(ext, 0) + 1
    if not lang_counts:
        return ""
    return max(lang_counts, key=lang_counts.get)


def _build_code_indices(code_nodes: list[dict]) -> dict[str, dict]:
    """Build nameIndex / fileIndex from AST-extracted code nodes.

    Indexes only ``file_type == "code"`` nodes (the AST output). The label
    index is keyed on BOTH the raw label (so a swagger tag of ``UserService``
    matches a class node whose label is ``UserService``) AND the normalized
    label (so an operationId of ``handleRegister`` matches a TS method node
    whose label is ``.handleRegister()``). Normalization is idempotent for
    labels that are already bare (``UserService`` -> ``UserService``), so
    class nodes end up indexed once under their canonical name.

    Also returns ``main_language``: the backend main language detected by
    counting code nodes per ``source_file`` extension (see
    :func:`_detect_main_language`). Used by ``_match_controller`` to gate
    the Java-codegen ``Impl`` suffix fallback.
    """
    name_index: dict[str, list[dict]] = {}
    file_index: dict[str, list[dict]] = {}

    for node in code_nodes:
        if not node or not node.get("id"):
            continue
        if node.get("file_type") != "code":
            continue
        source_file = node.get("source_file")
        if source_file:
            key = _basename_without_ext(source_file)
            if key:
                file_index.setdefault(key, []).append(node)
        label = node.get("label")
        if label:
            # Index under both raw and normalized labels so callers can look
            # up by either form. Normalized is the primary key for function
            # matching (operationId is bare); raw is kept for exact-tag matches
            # on classes (label is already bare for class nodes, so the two
            # keys collapse and we index once).
            name_index.setdefault(label, []).append(node)
            norm = _normalize_label(label)
            if norm != label:
                name_index.setdefault(norm, []).append(node)

    return {
        "nameIndex": name_index,
        "fileIndex": file_index,
        "main_language": _detect_main_language(code_nodes),
    }


# ---------------------------------------------------------------------------
# Code matching — controller (tags) and handler (operationId)
# ---------------------------------------------------------------------------

def _match_controller(
    tag_name: str, indices: dict
) -> list[tuple[dict, str, float]]:
    """Match a swagger ``tags`` entry to a controller class in the code index.

    Returns ``[(node, confidence, score)]``:
      - unique class match -> ``[(..., "EXTRACTED", 1.0)]``
      - multiple class matches -> all, ``("AMBIGUOUS", 0.3)``
      - no class match but same-name non-class nodes -> all, ``("AMBIGUOUS", 0.3)``
      - nothing -> ``[]``

    Java codegen fallback: swagger-codegen / openapi-generator for Java emit
    implementation classes as ``<swaggerName>Impl`` (e.g. swagger tag
    ``UserController`` -> Java class ``UserControllerImpl``). When the direct
    ``tag_name`` lookup finds no class node AND the corpus's main backend
    language is Java (``indices["main_language"] == "java"``), retry the
    lookup with an ``Impl`` suffix. The fallback is gated on the main
    language so it never fires for TypeScript / Python backends, avoiding
    spurious ``XxxImpl`` matches in non-Java stacks.
    """
    if not tag_name:
        return []
    candidates = indices["nameIndex"].get(tag_name, [])
    class_nodes = [n for n in candidates if _is_class_node(n)]

    # Java codegen fallback: <swaggerName>Impl (swagger-codegen / openapi-generator).
    # Only fires when no class node matched the bare tag AND the corpus's main
    # backend language is Java — see docstring for rationale.
    if not class_nodes and indices.get("main_language") == "java":
        impl_candidates = indices["nameIndex"].get(tag_name + "Impl", [])
        impl_class_nodes = [n for n in impl_candidates if _is_class_node(n)]
        if impl_class_nodes:
            class_nodes = impl_class_nodes

    matched = class_nodes if class_nodes else candidates
    if not matched:
        return []
    if len(matched) == 1:
        return [(matched[0], "EXTRACTED", 1.0)]
    return [(n, "AMBIGUOUS", 0.3) for n in matched]


def _match_handler(
    operation_id: str,
    controller_matches: list[tuple[dict, str, float]],
    indices: dict,
) -> list[tuple[dict, str, float]]:
    """Match a swagger ``operationId`` to a handler function in the code index.

    Prefers functions co-located with a matched controller's ``source_file``
    (PascalCase.method pattern). Falls back to any same-name function.
    """
    if not operation_id:
        return []
    candidates = indices["nameIndex"].get(operation_id, [])
    if not candidates:
        return []
    fn_candidates = [n for n in candidates if _is_function_node(n)]
    if not fn_candidates:
        return []

    # Prefer functions in the same source_file as a matched controller.
    controller_files = {
        n.get("source_file")
        for n, _, _ in controller_matches
        if n.get("source_file")
    }
    if controller_files:
        same_file = [n for n in fn_candidates if n.get("source_file") in controller_files]
        if same_file:
            fn_candidates = same_file

    if len(fn_candidates) == 1:
        return [(fn_candidates[0], "EXTRACTED", 1.0)]
    return [(n, "AMBIGUOUS", 0.3) for n in fn_candidates]


# ---------------------------------------------------------------------------
# YAML parsing — safe_load for data + compose for line numbers
# ---------------------------------------------------------------------------

def _is_swagger_spec(data: Any) -> bool:
    """Heuristic: is this parsed yaml a swagger/openapi spec?

    Accepts:
      - ``swagger: "2.0"`` key present, OR
      - ``openapi: "3.x"`` key present, OR
      - ``paths`` dict with at least one ``/``-prefixed key containing an
        HTTP-method sub-key (lenient match for specs missing the version key).
    """
    if not isinstance(data, dict):
        return False
    if "swagger" in data or "openapi" in data:
        return True
    paths = data.get("paths")
    if not isinstance(paths, dict) or not paths:
        return False
    for path_key, path_val in paths.items():
        if not isinstance(path_key, str) or not path_key.startswith("/"):
            continue
        if not isinstance(path_val, dict):
            continue
        if any(m in path_val for m in HTTP_METHODS):
            return True
    return False


def _compose_line_map(content: str) -> dict[str, int]:
    """Walk the composed yaml Node tree to build a ``"paths.<path>.<method>"``
    -> 1-based line-number map for accurate ``source_location``.

    Falls back to ``{}`` if compose fails (data-only parsing still works).
    """
    line_map: dict[str, int] = {}
    try:
        root = yaml.compose(content)
    except yaml.YAMLError:
        return line_map
    if not isinstance(root, yaml.MappingNode):
        return line_map

    for key_node, val_node in root.value:
        if not (isinstance(key_node, yaml.ScalarNode) and key_node.value == "paths"):
            continue
        if not isinstance(val_node, yaml.MappingNode):
            continue
        for path_key, path_val in val_node.value:
            if not (isinstance(path_key, yaml.ScalarNode) and isinstance(path_val, yaml.MappingNode)):
                continue
            path_str = path_key.value
            for method_key, method_val in path_val.value:
                if not isinstance(method_key, yaml.ScalarNode):
                    continue
                if method_key.value in HTTP_METHODS:
                    # start_mark.line is 0-based; graphify uses 1-based "L<n>".
                    line_map[f"paths.{path_str}.{method_key.value}"] = method_key.start_mark.line + 1
    return line_map


def _extract_base_path(spec: dict, version: str) -> str:
    """Extract the base path prefix.

    Swagger 2.0: ``basePath: /rest``.
    OpenAPI 3.x:  ``servers[0].url`` -> path component (host stripped).
    """
    if version.startswith("2"):
        bp = spec.get("basePath", "")
        return bp if isinstance(bp, str) else ""
    # 3.x
    servers = spec.get("servers")
    if isinstance(servers, list) and servers:
        url = servers[0].get("url", "") if isinstance(servers[0], dict) else ""
        if not isinstance(url, str) or not url:
            return ""
        if "://" in url:
            parsed = urlparse(url)
            return parsed.path or ""
        return url if url.startswith("/") else ""
    return ""


def _detect_version(spec: dict) -> str:
    """Return ``"2.x"`` or ``"3.x"`` (major version string), or ``""`` if unknown."""
    if "swagger" in spec:
        return "2.x"
    if "openapi" in spec:
        return "3.x"
    return ""


def _extract_examples(operation: dict) -> list[str]:
    """Pull ``x-examples`` from the operation (custom swagger extension).

    Stored as raw strings for the endpoint node's ``examples`` field — not
    parsed into sub-nodes (keeps the graph lean).
    """
    examples: list[str] = []
    raw = operation.get("x-examples")
    if isinstance(raw, str):
        examples.append(raw)
    elif isinstance(raw, list):
        examples.extend(str(x) for x in raw if x)
    # also check per-response x-examples
    responses = operation.get("responses")
    if isinstance(responses, dict):
        for resp in responses.values():
            if not isinstance(resp, dict):
                continue
            r_ex = resp.get("x-examples")
            if isinstance(r_ex, str):
                examples.append(r_ex)
            elif isinstance(r_ex, list):
                examples.extend(str(x) for x in r_ex if x)
    return examples


# ---------------------------------------------------------------------------
# Node + Edge builders
# ---------------------------------------------------------------------------

def _make_doc_node(*, doc_path: str, stem: str) -> dict:
    """Build the per-file swagger document node (generic fields only)."""
    return {
        "id": _make_id("swagger_doc", stem),
        "label": Path(doc_path).name,
        "file_type": "document",
        "source_file": doc_path,
        "source_location": None,
        "node_kind": "swagger_doc",
        "tags": ["swagger"],
    }


def _make_endpoint_node(
    *,
    doc_path: str,
    stem: str,
    method: str,
    path: str,
    base_path: str,
    operation: dict,
    line_num: int,
) -> dict:
    """Build one REST endpoint node from a ``paths.<path>.<method>`` block.

    ``label`` follows the ``METHOD:/full/path`` convention — the URL exactly
    as written in the yaml, path variables keeping their original names
    (``GET:/rest/users/{id}``) — so the URL is recoverable from the label
    alone and token-based retrieval (``graphify query`` / ``path`` /
    ``explain``) sees the same tokens a user would type.

    ``desc`` is description + x-examples (summary is intentionally excluded —
    redundant with description) so the semantic tier embeds the endpoint's
    business language and ``graphify query`` / ``explain`` return the full
    human-readable context.

    All fields are generic — no swagger-specific fields. Controller/handler
    associations live in ``references`` edges (built by :func:`extract_swagger`);
    request/response structure stays in the yaml itself, reachable via
    ``source_file`` + ``source_location``.
    """
    full_path = (base_path or "") + path
    method_upper = method.upper()
    description = operation.get("description", "") or ""
    examples = _extract_examples(operation)

    # desc = description + examples (no summary — redundant with description).
    parts: list[str] = []
    if description:
        parts.append(description)
    if examples:
        parts.extend(examples)
    desc = "\n\n".join(parts)

    # ID: swagger_ep_<stem>_<method>_<normalized full_path>
    norm_path = full_path.lstrip("/").replace("/", "_").replace("{", "").replace("}", "")
    endpoint_id = _make_id("swagger_ep", stem, method_upper.lower(), norm_path) if norm_path \
        else _make_id("swagger_ep", stem, method_upper.lower(), "root")

    return {
        "id": endpoint_id,
        "label": f"{method_upper}:{full_path}",
        "file_type": "concept",
        "source_file": doc_path,
        "source_location": f"L{line_num}" if line_num else None,
        "node_kind": "rest_endpoint",
        "desc": desc,
        "tags": ["url"],
    }


def _make_edge(
    *,
    source: str,
    target: str,
    relation: str,
    confidence: str = "EXTRACTED",
    confidence_score: float = 1.0,
    source_file: str,
    line_num: int = 0,
    weight: float = 0.8,
) -> dict:
    return {
        "source": source,
        "target": target,
        "relation": relation,
        "confidence": confidence,
        "confidence_score": confidence_score,
        "source_file": source_file,
        "source_location": f"L{line_num}" if line_num else None,
        "weight": weight,
    }


# ---------------------------------------------------------------------------
# Main extractor
# ---------------------------------------------------------------------------

def extract_swagger(
    path: Path, *, root: Path, nodes: list[dict] | None = None
) -> ExtractionResult | None:
    """Extract REST endpoint nodes + references edges from a swagger/openapi yaml.

    Returns ``None`` (fall back to default ``extract_markdown``) when the file
    is not a swagger/openapi spec.
    """
    if path.suffix.lower() not in SWAGGER_EXTENSIONS:
        return None

    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        _LOG.warning("swagger extractor: cannot read %s: %s", path, exc)
        return None

    try:
        spec = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        _LOG.debug("swagger extractor: yaml parse error in %s: %s", path, exc)
        return None  # let default markdown extractor try

    if not _is_swagger_spec(spec):
        return None

    if not isinstance(spec, dict):
        return None

    version = _detect_version(spec) or "2.x"  # default to 2.x field access for path-only specs
    base_path = _extract_base_path(spec, version)
    line_map = _compose_line_map(content)

    # Build code indices for controller/handler matching (AST-first, G3).
    # ``nodes`` may include both fresh (this run's Stage 1/2) and persisted
    # (graph.json存量) code/config nodes — extract() merges them before calling.
    code_nodes = nodes if nodes else []
    indices = _build_code_indices(code_nodes)

    doc_path = path.resolve().relative_to(root.resolve()).as_posix()
    stem = _file_stem(Path(doc_path))

    doc_node = _make_doc_node(doc_path=doc_path, stem=stem)
    nodes: list[dict] = [doc_node]
    edges: list[dict] = []
    unmatched: list[dict] = []

    paths = spec.get("paths")
    if not isinstance(paths, dict):
        return ExtractionResult(
            nodes=nodes, edges=edges, hyperedges=[],
            merge_mode="replace", suppress_llm=True,
            unmatched=unmatched, pending_edges=[],
        )

    for path_str, path_val in paths.items():
        if not isinstance(path_str, str) or not isinstance(path_val, dict):
            continue
        for method, operation in path_val.items():
            if method not in HTTP_METHODS:
                continue
            if not isinstance(operation, dict):
                continue

            line_num = line_map.get(f"paths.{path_str}.{method}", 0)
            ep_node = _make_endpoint_node(
                doc_path=doc_path, stem=stem, method=method, path=path_str,
                base_path=base_path, operation=operation, line_num=line_num,
            )
            nodes.append(ep_node)

            # doc -> contains -> endpoint
            edges.append(_make_edge(
                source=doc_node["id"], target=ep_node["id"], relation="contains",
                confidence="EXTRACTED", confidence_score=1.0,
                source_file=doc_path, line_num=line_num, weight=0.9,
            ))
            # endpoint -> defined_in -> doc (reverse, for path queries)
            edges.append(_make_edge(
                source=ep_node["id"], target=doc_node["id"], relation="defined_in",
                confidence="EXTRACTED", confidence_score=1.0,
                source_file=doc_path, line_num=line_num, weight=0.5,
            ))

            # --- Code association: tags -> controller class ---
            # The references edge carries the controller/handler relationship
            # explicitly — the endpoint node itself keeps no swagger-specific
            # fields (URL lives in the label, semantics in desc).
            raw_tags = operation.get("tags", []) or []
            if not isinstance(raw_tags, list):
                raw_tags = []
            controller_matches: list[tuple[dict, str, float]] = []
            if raw_tags:
                # Use the first tag (Spring/Swagger convention: tags[0] = controller class)
                primary_tag = str(raw_tags[0])
                controller_matches = _match_controller(primary_tag, indices)
                if controller_matches:
                    for matched_node, conf, score in controller_matches:
                        edges.append(_make_edge(
                            source=ep_node["id"], target=matched_node["id"],
                            relation="references", confidence=conf,
                            confidence_score=score, source_file=doc_path,
                            line_num=line_num,
                            weight=0.8 if conf == "EXTRACTED" else 0.3,
                        ))
                else:
                    unmatched.append({
                        "source": "swagger",
                        "docPath": doc_path,
                        "endpointId": ep_node["id"],
                        "endpointLabel": ep_node["label"],
                        "anchor": primary_tag,
                        "anchorKind": "controller_tag",
                        "reason": "no matching class node in code index",
                    })

            # --- Code association: operationId -> handler function ---
            operation_id = operation.get("operationId", "") or ""
            if operation_id:
                handler_matches = _match_handler(operation_id, controller_matches, indices)
                if handler_matches:
                    for matched_node, conf, score in handler_matches:
                        edges.append(_make_edge(
                            source=ep_node["id"], target=matched_node["id"],
                            relation="references", confidence=conf,
                            confidence_score=score, source_file=doc_path,
                            line_num=line_num,
                            weight=0.8 if conf == "EXTRACTED" else 0.3,
                        ))
                else:
                    unmatched.append({
                        "source": "swagger",
                        "docPath": doc_path,
                        "endpointId": ep_node["id"],
                        "endpointLabel": ep_node["label"],
                        "anchor": operation_id,
                        "anchorKind": "operation_id",
                        "reason": "no matching function node in code index",
                    })

    return ExtractionResult(
        nodes=nodes,
        edges=edges,
        hyperedges=[],
        merge_mode="replace",        # swagger is structured; default markdown adds noise
        suppress_llm=True,           # Tier 1 only — zero LLM cost, fully deterministic
        unmatched=unmatched,
        pending_edges=[],            # all edges resolved in-file (no cross-file concept refs)
    )


# Declare extensions so ``_rebuild_code`` (watch.py) includes ``.yaml``/``.yml``
# doc files in post-commit hook rebuilds. Without this, graphify classifies
# ``.yaml`` as a document but no built-in ``_get_extractor`` claims it, so the
# file never enters ``code_files``/``doc_targets`` and ``try_external_extractors``
# never sees it — the swagger spec would be invisible to ``git commit``-triggered
# rebuilds and require a manual ``/graphify --update`` instead.
register_doc_extractor(extract_swagger, extensions={".yaml", ".yml"})
