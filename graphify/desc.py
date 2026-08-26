"""Node desc field extraction for hybrid semantic search.

Extracts docstrings/comments as per-node ``desc`` fields, used as the sole
embedding text source. Decoupled from extract.py — called by engine.py's
``_extract_generic`` walk and markdown.py's ``extract_markdown``.

Supported languages (others leave desc empty, fallback to label at embed time):
- Python: module/function/class docstring (first string in body)
- JS/TS: JSDoc comment (/** ... */) immediately before declaration
- C/C++/Go/Rust/Java/C#/Swift: block comment immediately before declaration
"""
from __future__ import annotations

_DESC_MAX_CHARS = 512  # cap desc length (embedding models use ~512 tokens)


def _clean_desc(raw: str) -> str:
    """Strip comment markers, dedent, collapse whitespace, cap length.

    Returns ``""`` for empty input. Leading ``#``, ``//``, ``/*``, ``*/``,
    ``*`` and ``--`` prefixes are stripped line-by-line so a multi-line
    block comment flattens to one line of prose. A leading marker is
    stripped RECURSIVELY so ``/**`` collapses: ``/*`` peels first, leaving
    ``*`` which the next pass peels — without the loop a JSDoc opener
    would leak a stray ``*`` into the first line of prose. A trailing
    ``*/`` on a single-line block comment is also stripped so
    ``/* text */`` flattens to ``text``.
    """
    if not raw:
        return ""
    lines: list[str] = []
    for line in raw.splitlines():
        stripped = line.strip()
        # Repeatedly strip leading comment markers (so "/**" -> "*" -> "")
        # so a JSDoc opener does not leak a stray '*' into the prose.
        changed = True
        while changed:
            changed = False
            for prefix in ("#", "//", "/*", "*/", "*", "--"):
                if stripped.startswith(prefix):
                    stripped = stripped[len(prefix):].strip()
                    changed = True
                    break
        # Strip trailing block-comment close (single-line `/* text */` case).
        # Multi-line JSDoc lines end without `*/` so this is a no-op there.
        if stripped.endswith("*/"):
            stripped = stripped[:-2].strip()
        if stripped:
            lines.append(stripped)
    desc = " ".join(lines).strip()
    return desc[:_DESC_MAX_CHARS]


def _node_text(node, source: bytes) -> str:
    """Bytes-slice the source span of a tree-sitter node."""
    return source[node.start_byte:node.end_byte].decode("utf-8", errors="replace")


def _strip_quotes(s: str) -> str:
    """Strip Python string quotes/triple-quotes."""
    s = s.strip()
    for q in ('"""', "'''", '"', "'"):
        if s.startswith(q) and s.endswith(q) and len(s) >= 2 * len(q):
            return s[len(q):-len(q)]
    return s


def _extract_python_docstring(node, source: bytes) -> str:
    """Python: first statement in block body is a string literal (docstring).

    Handles module, function, and class docstrings. For a function/class the
    body is the named ``body`` field; for a module (the root ``module`` node)
    tree-sitter Python exposes no ``body`` field — statements are direct
    children, so we check the first child directly.
    """
    body = node.child_by_field_name("body")
    if body is None:
        # Module-level: tree-sitter Python modules have no 'body' field.
        # Statements are direct children of the module node, so the first
        # child is the docstring when it's an expression_statement(string).
        if node.type == "module" and node.children:
            first = node.children[0]
            if first.type == "expression_statement":
                for sub in first.children:
                    if sub.type == "string":
                        raw = _node_text(sub, source)
                        return _clean_desc(_strip_quotes(raw))
        return ""
    if len(body.children) == 0:
        return ""
    first = body.children[0]
    # docstring is expression_statement containing a string
    if first.type == "expression_statement":
        for sub in first.children:
            if sub.type == "string":
                raw = _node_text(sub, source)
                return _clean_desc(_strip_quotes(raw))
    return ""


def _extract_jsdoc(node, source: bytes) -> str:
    """JS/TS: JSDoc comment /** ... */ immediately before the declaration."""
    prev = node.prev_sibling
    if prev is not None and prev.type == "comment":
        raw = _node_text(prev, source)
        if raw.startswith("/**"):
            return _clean_desc(raw)
    return ""


def _extract_preceding_comment(node, source: bytes) -> str:
    """C/Go/Rust/Java/C#/Swift: block comment immediately before declaration.

    Only block comments (``/* ... */``) are considered — line comments
    trailing code on the previous line are skipped to avoid pulling in
    incidental remarks.
    """
    prev = node.prev_sibling
    if prev is not None and prev.type in ("comment", "block_comment"):
        raw = _node_text(prev, source)
        # Only block comments (/* ... */), not line comments trailing code
        if raw.startswith("/*"):
            return _clean_desc(raw)
    return ""


# Map tree-sitter module names to a desc-extraction strategy. The keys are
# the ``config.ts_module`` strings produced by LanguageConfig (e.g.
# ``tree_sitter_python``); the values are short language tags used here.
_TS_MODULE_TO_LANG: dict[str, str] = {
    "tree_sitter_python": "python",
    "tree_sitter_javascript": "javascript",
    "tree_sitter_typescript": "typescript",
    "tree_sitter_c": "c",
    "tree_sitter_cpp": "cpp",
    "tree_sitter_go": "go",
    "tree_sitter_rust": "rust",
    "tree_sitter_java": "java",
    "tree_sitter_c_sharp": "c_sharp",
    "tree_sitter_swift": "swift",
}


def _language_from_ts_module(ts_module: str) -> str:
    """Translate ``config.ts_module`` to the desc-extraction language tag.

    Returns ``""`` for unsupported languages so ``_extract_node_desc`` short
    circuits and the node's desc falls back to its label at embed time.
    """
    return _TS_MODULE_TO_LANG.get(ts_module, "")


def _extract_node_desc(node, source: bytes, language: str) -> str:
    """Extract desc from an AST node. Returns ``""`` if no docstring/comment.

    Called by engine.py walk() when creating function/class/file nodes.
    ``language`` is the short tag from ``_language_from_ts_module`` — pass
    ``""`` to short-circuit (the node will fall back to its label at embed
    time).
    """
    if not language:
        return ""
    if language == "python":
        return _extract_python_docstring(node, source)
    if language in ("javascript", "typescript"):
        return _extract_jsdoc(node, source)
    if language in ("c", "cpp", "go", "rust", "java", "c_sharp", "swift"):
        return _extract_preceding_comment(node, source)
    return ""
