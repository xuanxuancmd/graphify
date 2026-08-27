# DO NOT import from graphify.extract here — direction is extract.py → extractors/ only.
"""External extractor registry — opt-in extension point for .md doc parsing.

External extractors registered here are tried BEFORE the default extract_markdown.
An extractor returns None to signal "not my file, fall back to default".

This module is opt-in: if no extractor is registered (or the import in
__init__.py is removed), graphify behaves exactly as upstream.

Design:

- Registered extractors are tried in registration order. The first non-None
  result wins; if all return None, the caller falls back to the default
  markdown extractor.
- An extractor returns an :class:`ExtractionResult` dataclass that carries the
  produced nodes/edges plus a declarative ``merge_mode`` and ``suppress_llm``
  flag, so :func:`graphify.extract.extract` can decide whether to also run the
  default ``extract_markdown`` and/or skip LLM Tier 2 for that file.
- Extractors run in the MAIN process (not the subprocess pool) because they may
  need the ``nodes`` (already-extracted AST + config nodes) for anchor matching;
  pickling that across subprocesses is too expensive. Doc extraction is
  I/O-light (no tree-sitter), so the main process is plenty.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Protocol


class DocExtractor(Protocol):
    def __call__(
        self, path: Path, *, root: Path, nodes: list[dict] | None = None
    ) -> "ExtractionResult | None":
        """Return ExtractionResult or None to fall back to default."""
        ...


@dataclass
class ExtractionResult:
    """声明式返回：外部解析器产出的节点/边 + 合并策略。

    merge_mode:
        "merge"          — 外部 + 默认 extract_markdown 合并（保留 page/heading 节点）
        "replace"        — 外部替代默认 markdown（跳过 extract_markdown），LLM Tier 2 仍跑（除非 suppress_llm）
        "supplement_only" — 只用外部结果，跳过默认 markdown + 跳过 LLM Tier 2

    suppress_llm:
        True = 不对该文件跑 LLM Tier 2（对 replace/supplement_only 生效；merge 模式下 LLM 总是跑）

    pending_edges:
        原始未解析的边（sourceRef/targetRef 形式），供 extract() 做跨文件
        全局二次解析。每个文件独立解析时，引用其他文件 concept_id/name
        的边无法解析；extract() 收集所有文件的 pending_edges + doc-anchor
        节点后统一重解析。已在本文件内解析的边放在 ``edges`` 里，不重复。
    """

    nodes: list[dict]
    edges: list[dict]
    hyperedges: list[dict] = field(default_factory=list)
    merge_mode: str = "merge"
    suppress_llm: bool = False
    unmatched: list[dict] = field(default_factory=list)
    pending_edges: list[dict] = field(default_factory=list)


_REGISTRY: list[Callable[..., "ExtractionResult | None"]] = []

#: Extensions declared by registered extractors via ``register_doc_extractor``.
#: A doc file with one of these extensions is offered to
#: ``try_external_extractors`` even when no built-in ``_get_extractor`` exists
#: for it (e.g. ``.yaml`` for swagger). ``_rebuild_code`` (watch.py) uses this
#: to decide which doc files to include in a hook/watch rebuild so that Tier1
#: custom extractors fire on commit — without it, a ``.yaml`` change is invisible
#: to the post-commit hook (no built-in extractor, so the file never enters
#: ``code_files`` / ``doc_targets``, so ``try_external_extractors`` never sees it).
_REGISTRY_EXTENSIONS: dict[str, frozenset[str]] = {}


def register_doc_extractor(
    fn: Callable[..., "ExtractionResult | None"],
    *,
    priority: str = "append",
    extensions: frozenset[str] | set[str] | None = None,
) -> Callable[..., "ExtractionResult | None"]:
    """Decorator to register an external doc extractor.

    Registered extractors are tried in registration order. The first non-None
    result wins; if all return None, the caller falls back to the default
    markdown extractor.

    priority:
        "append"  — append to tail (built-in default; tried last)
        "prepend" — insert at head (project-level; tried first, overrides
                    built-in same-name extractors)

    extensions:
        File extensions (lowercase, WITH the leading dot, e.g. ``{".yaml", ".yml"}``)
        this extractor claims. When ``None`` (the default), the extractor is
        tried for every file ``try_external_extractors`` is offered — same as
        before this parameter existed. Declaring extensions lets
        :func:`external_extractor_extensions` report the union, so
        ``_rebuild_code`` (watch.py) can include doc files with these
        extensions in a hook/watch rebuild even when no built-in
        ``_get_extractor`` handles them. Without this, a ``.yaml`` swagger spec
        is invisible to the post-commit hook (graphify classifies ``.yaml`` as
        a document, but no built-in extractor claims it, so the file never
        enters ``code_files`` / ``doc_targets`` and
        ``try_external_extractors`` never runs on it).
    """
    if fn not in _REGISTRY:
        if priority == "prepend":
            _REGISTRY.insert(0, fn)
        else:
            _REGISTRY.append(fn)
        if extensions:
            _REGISTRY_EXTENSIONS[getattr(fn, "__name__", repr(fn))] = frozenset(extensions)
    return fn


def external_extractor_extensions() -> frozenset[str]:
    """Union of file extensions declared by all registered extractors.

    Used by ``_rebuild_code`` (watch.py) to widen the doc-file set included in a
    hook/watch rebuild: a doc file whose extension is in this set is pulled into
    ``doc_targets`` even when no built-in ``_get_extractor`` handles it, so
    ``try_external_extractors`` (which runs inside ``extract()`` when
    ``nodes`` is passed) gets a chance to claim it.
    """
    result: set[str] = set()
    for exts in _REGISTRY_EXTENSIONS.values():
        result.update(exts)
    return frozenset(result)


def try_external_extractors(
    path: Path, *, root: Path, nodes: list[dict] | None = None
) -> "ExtractionResult | None":
    """Try registered extractors in order; return first non-None result, or None."""
    for fn in _REGISTRY:
        try:
            result = fn(path, root=root, nodes=nodes)
        except _NotApplicable:
            result = None
        if result is not None:
            return result
    return None


class _NotApplicable(Exception):
    """Extractor signals "not my file" by raising this or returning None."""
    pass


def clear_registry() -> None:
    """Test helper: clear all registered extractors."""
    _REGISTRY.clear()
