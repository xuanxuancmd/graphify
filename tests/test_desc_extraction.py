"""Tests for node desc field extraction (graphify/desc.py).

Covers the four docstring/comment conventions desc.py understands:
Python docstrings, JS/TS JSDoc, C-family preceding block comments, and
the "no docstring" fallback. Each test parses a small snippet with
tree-sitter (the same parser engine.py uses) and asserts the extracted
desc matches the expected prose.
"""
from __future__ import annotations

import pytest

from graphify.desc import (
    _DESC_MAX_CHARS,
    _clean_desc,
    _extract_node_desc,
    _language_from_ts_module,
    _strip_quotes,
)


# ---------------------------------------------------------------------------
# _clean_desc
# ---------------------------------------------------------------------------


class TestCleanDesc:
    def test_strips_hash_comment(self) -> None:
        assert _clean_desc("# Validate user credentials") == "Validate user credentials"

    def test_strips_double_slash_comment(self) -> None:
        assert _clean_desc("// Manages auth sessions") == "Manages auth sessions"

    def test_strips_block_comment_markers(self) -> None:
        assert _clean_desc("/* Block comment */") == "Block comment"

    def test_strips_jsdoc_markers(self) -> None:
        # JSDoc /** ... */ with leading * on each line
        raw = "/**\n * Manages authentication sessions\n * and token refresh.\n */"
        cleaned = _clean_desc(raw)
        assert "Manages authentication sessions" in cleaned
        assert "and token refresh" in cleaned
        # No comment markers remain
        assert "*" not in cleaned
        assert "/*" not in cleaned
        assert "*/" not in cleaned

    def test_multiline_collapses_to_single_line(self) -> None:
        raw = "# line one\n# line two\n# line three"
        assert _clean_desc(raw) == "line one line two line three"

    def test_empty_input_returns_empty(self) -> None:
        assert _clean_desc("") == ""
        assert _clean_desc(None) == ""  # type: ignore[arg-type]

    def test_only_whitespace_returns_empty(self) -> None:
        assert _clean_desc("   \n   \n  ") == ""

    def test_caps_at_512_chars(self) -> None:
        long = "x" * 600
        result = _clean_desc(long)
        assert len(result) == _DESC_MAX_CHARS

    def test_strips_dash_dash_comment(self) -> None:
        assert _clean_desc("-- Lua style comment") == "Lua style comment"


# ---------------------------------------------------------------------------
# _strip_quotes
# ---------------------------------------------------------------------------


class TestStripQuotes:
    def test_triple_double_quotes(self) -> None:
        assert _strip_quotes('"""docstring"""') == "docstring"

    def test_triple_single_quotes(self) -> None:
        assert _strip_quotes("'''docstring'''") == "docstring"

    def test_single_quotes(self) -> None:
        assert _strip_quotes("'docstring'") == "docstring"

    def test_double_quotes(self) -> None:
        assert _strip_quotes('"docstring"') == "docstring"

    def test_no_quotes(self) -> None:
        assert _strip_quotes("no quotes here") == "no quotes here"

    def test_unclosed_quote_returns_input(self) -> None:
        # Mismatched quotes — too short to peel both ends, returns as-is
        assert _strip_quotes('"unclosed') == '"unclosed'


# ---------------------------------------------------------------------------
# _language_from_ts_module
# ---------------------------------------------------------------------------


class TestLanguageFromTsModule:
    def test_python(self) -> None:
        assert _language_from_ts_module("tree_sitter_python") == "python"

    def test_javascript(self) -> None:
        assert _language_from_ts_module("tree_sitter_javascript") == "javascript"

    def test_typescript(self) -> None:
        assert _language_from_ts_module("tree_sitter_typescript") == "typescript"

    def test_c_family(self) -> None:
        assert _language_from_ts_module("tree_sitter_c") == "c"
        assert _language_from_ts_module("tree_sitter_cpp") == "cpp"
        assert _language_from_ts_module("tree_sitter_go") == "go"
        assert _language_from_ts_module("tree_sitter_rust") == "rust"
        assert _language_from_ts_module("tree_sitter_java") == "java"
        assert _language_from_ts_module("tree_sitter_c_sharp") == "c_sharp"
        assert _language_from_ts_module("tree_sitter_swift") == "swift"

    def test_unsupported_returns_empty(self) -> None:
        assert _language_from_ts_module("tree_sitter_ruby") == ""
        assert _language_from_ts_module("tree_sitter_php") == ""
        assert _language_from_ts_module("nonexistent_module") == ""


# ---------------------------------------------------------------------------
# _extract_node_desc — language-specific integration tests
# ---------------------------------------------------------------------------


def _parse_source(source: bytes, ts_module: str):
    """Parse source bytes with the given tree-sitter module; return root node.

    Skips the test if the tree-sitter module isn't installed (some are
    optional extras). Mirrors what engine.py does in _extract_generic.
    """
    pytest.importorskip(ts_module)
    import importlib
    from tree_sitter import Language, Parser

    mod = importlib.import_module(ts_module)
    lang_fn = getattr(mod, "language", None)
    assert lang_fn is not None, f"{ts_module} has no language()"
    language = Language(lang_fn())
    parser = Parser(language)
    tree = parser.parse(source)
    return tree.root_node


class TestExtractPythonDocstring:
    def test_function_docstring(self) -> None:
        source = b'''
def verify_password(password: str) -> bool:
    """Validate user credentials against the stored hash."""
    return True
'''
        root = _parse_source(source, "tree_sitter_python")
        # root is 'module'; first child is the function_definition
        func_node = root.children[0]
        # Wait — leading blank line means children[0] might be None or empty
        # Find the first non-empty child
        func_node = next(c for c in root.children if c.type == "function_definition")
        desc = _extract_node_desc(func_node, source, "python")
        assert desc == "Validate user credentials against the stored hash."

    def test_class_docstring(self) -> None:
        source = b'''
class AuthService:
    """Manages authentication sessions and token refresh."""
    pass
'''
        root = _parse_source(source, "tree_sitter_python")
        class_node = next(c for c in root.children if c.type == "class_definition")
        desc = _extract_node_desc(class_node, source, "python")
        assert desc == "Manages authentication sessions and token refresh."

    def test_module_docstring(self) -> None:
        source = b'"""Authentication service module."""\n\ndef foo():\n    pass\n'
        root = _parse_source(source, "tree_sitter_python")
        # Module-level: pass the root (module node) directly
        desc = _extract_node_desc(root, source, "python")
        assert desc == "Authentication service module."

    def test_no_docstring_returns_empty(self) -> None:
        source = b"def no_docs():\n    return 42\n"
        root = _parse_source(source, "tree_sitter_python")
        func_node = next(c for c in root.children if c.type == "function_definition")
        assert _extract_node_desc(func_node, source, "python") == ""


class TestExtractJsdoc:
    def test_jsdoc_before_function(self) -> None:
        source = b'''/**
 * Manages authentication sessions.
 * @param {string} token - JWT token
 */
function AuthService(token) {
    this.token = token;
}
'''
        root = _parse_source(source, "tree_sitter_javascript")
        func_node = next(
            c for c in root.children
            if c.type in ("function_declaration", "export_statement")
        )
        # If wrapped in export_statement, descend
        if func_node.type == "export_statement":
            func_node = next(
                c for c in func_node.children
                if c.type == "function_declaration"
            )
        desc = _extract_node_desc(func_node, source, "javascript")
        assert "Manages authentication sessions" in desc
        assert "JWT token" in desc

    def test_no_jsdoc_returns_empty(self) -> None:
        source = b"function foo() { return 1; }\n"
        root = _parse_source(source, "tree_sitter_javascript")
        func_node = next(c for c in root.children if c.type == "function_declaration")
        assert _extract_node_desc(func_node, source, "javascript") == ""


class TestExtractPrecedingComment:
    def test_c_block_comment_before_function(self) -> None:
        source = b'''/* Validate user credentials against the stored hash. */
int verify_password(const char *password) {
    return 0;
}
'''
        root = _parse_source(source, "tree_sitter_c")
        func_node = next(
            c for c in root.children
            if c.type in ("function_definition", "declaration")
        )
        desc = _extract_node_desc(func_node, source, "c")
        assert desc == "Validate user credentials against the stored hash."

    def test_no_preceding_comment_returns_empty(self) -> None:
        source = b"int foo(void) { return 0; }\n"
        root = _parse_source(source, "tree_sitter_c")
        func_node = next(
            c for c in root.children
            if c.type in ("function_definition", "declaration")
        )
        assert _extract_node_desc(func_node, source, "c") == ""


class TestUnsupportedLanguage:
    def test_unsupported_returns_empty(self) -> None:
        # _extract_node_desc with "" language short-circuits
        assert _extract_node_desc(None, b"", "") == ""
        assert _extract_node_desc(None, b"", "ruby") == ""
        assert _extract_node_desc(None, b"", "php") == ""
