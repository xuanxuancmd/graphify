# DO NOT import from graphify.extract here — direction is extract.py → extractors/ only.
"""Tier 2 prompt registry — YAML-declared custom LLM extraction prompts.

Loads ``.graph/extension/prompts/*.yaml`` declarations, routes semantic files
to matching prompts via ``match.files`` globs, and groups files by prompt spec
so each group forms one LLM chunk with its custom system prompt.

Design (see docs/extending-extractors/spec.md §3):

- Users write **zero Python** — only YAML files declaring ``match.files`` globs
  + a custom ``prompt`` (system message instruction part).
- File content is still read and wrapped in ``<untrusted_source>`` by
  ``llm.py:_read_files()`` — the custom prompt only replaces the system
  message, exactly the role ``_EXTRACTION_SYSTEM`` plays today.
- ``mode: replace`` (default) uses only the custom prompt; ``mode: merge`` runs
  the custom prompt then the default prompt, doubling LLM cost but letting a
  domain-specific prompt complement the general-purpose one.
- Tier 1 ``suppress_llm=True`` is the master switch — it skips Tier 2 entirely,
  taking priority over any matching prompt spec.
"""
from __future__ import annotations

import fnmatch
import logging
from dataclasses import dataclass, field
from pathlib import Path

_LOG = logging.getLogger(__name__)


@dataclass(eq=False)
class PromptSpec:
    """A YAML-declared custom Tier 2 extraction prompt."""

    name: str
    description: str = ""
    match: dict = field(default_factory=dict)  # {"files": ["glob1", "glob2", ...]}
    mode: str = "replace"  # "replace" | "merge"
    prompt: str = ""  # system prompt (instruction part only; file content is injected by _read_files)
    output_schema: dict | None = None  # optional stricter validation

    def __hash__(self) -> int:  # noqa: D401 — needed for dict keys in group_by_prompt
        return hash(self.name)


def load_prompts_from_dir(prompt_dir: Path) -> list["PromptSpec"]:
    """Scan ``*.yaml`` in *prompt_dir* and return a list of PromptSpec.

    A malformed YAML file is logged and skipped — one bad file does not abort
    startup. Files are sorted by name so the first-match-wins ordering is
    deterministic across runs.
    """
    if not prompt_dir.is_dir():
        return []

    try:
        import yaml
    except ImportError:
        _LOG.warning(
            "prompt_registry: PyYAML not installed — custom prompts in %s ignored",
            prompt_dir,
        )
        return []

    specs: list[PromptSpec] = []
    for yaml_path in sorted(prompt_dir.glob("*.yaml")):
        try:
            raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        except Exception as exc:
            _LOG.warning("prompt_registry: failed to load %s: %s", yaml_path, exc)
            continue
        if not isinstance(raw, dict):
            _LOG.warning("prompt_registry: %s is not a YAML mapping, skipping", yaml_path)
            continue
        try:
            spec = PromptSpec(
                name=raw.get("name", yaml_path.stem),
                description=raw.get("description", ""),
                match=raw.get("match", {}) or {},
                mode=raw.get("mode", "replace"),
                prompt=raw.get("prompt", ""),
                output_schema=raw.get("output_schema"),
            )
        except Exception as exc:
            _LOG.warning("prompt_registry: %s has invalid structure: %s", yaml_path, exc)
            continue
        if not spec.prompt.strip():
            _LOG.warning("prompt_registry: %s has empty prompt, skipping", yaml_path)
            continue
        if spec.mode not in ("replace", "merge"):
            _LOG.warning(
                "prompt_registry: %s has invalid mode %r, defaulting to 'replace'",
                yaml_path,
                spec.mode,
            )
            spec.mode = "replace"
        files_list = spec.match.get("files", []) if isinstance(spec.match, dict) else []
        if not files_list:
            _LOG.warning(
                "prompt_registry: %s has no match.files globs, skipping", yaml_path
            )
            continue
        specs.append(spec)
    return specs


def load_builtin_prompts() -> list["PromptSpec"]:
    """Scan the built-in ``graphify/prompts/*.yaml`` directory.

    These ship with the graphify package — DDD semantic extraction, API spec
    extraction, etc. Users override them by placing a same-named or matching
    spec in the project-level ``.graph/extension/prompts/`` directory, which
    takes priority via :func:`load_all_prompts`.
    """
    _builtin_dir = Path(__file__).parent / "prompts"
    return load_prompts_from_dir(_builtin_dir)


def load_all_prompts(project_dir: Path | None = None) -> list["PromptSpec"]:
    """Load built-in + project-level prompts, project-level first (priority).

    Mirrors the Tier 1 pattern: ``graphify/extractors/custom/`` (built-in) +
    ``.graph/extension/extractors/`` (project-level, prepend). Here:
    ``graphify/prompts/`` (built-in) + ``.graph/extension/prompts/``
    (project-level, prepended so first-match-wins favours the project spec).

    If *project_dir* is None, defaults to ``Path.cwd() / ".graph" / "extension"
    / "prompts"``.
    """
    if project_dir is None:
        project_dir = Path.cwd() / ".graph" / "extension" / "prompts"
    builtin = load_builtin_prompts()
    project = load_prompts_from_dir(project_dir)
    # Project-level first (first-match-wins → project overrides built-in)
    return project + builtin


def find_prompt(
    path: Path, root: Path, specs: list["PromptSpec"]
) -> "PromptSpec | None":
    """Return the first PromptSpec whose ``match.files`` glob matches *path*.

    *path* is resolved relative to *root* and matched as a posix path string.
    Specs are tried in list order (sorted by filename on load) — the first
    match wins.
    """
    try:
        rel = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        rel = path.as_posix()

    for spec in specs:
        files = spec.match.get("files", []) if isinstance(spec.match, dict) else []
        for pattern in files:
            if _glob_match(rel, pattern):
                return spec
    return None


def group_by_prompt(
    files: list[Path], root: Path, specs: list["PromptSpec"]
) -> dict["PromptSpec | None", list[Path]]:
    """Group semantic files by matching PromptSpec.

    Returns a dict mapping each PromptSpec (or ``None`` for unmatched files)
    to the list of files that match it. Unmatched files go under the ``None``
    key and use the default ``_EXTRACTION_SYSTEM`` prompt.
    """
    groups: dict["PromptSpec | None", list[Path]] = {}
    for f in files:
        spec = find_prompt(f, root, specs)
        groups.setdefault(spec, []).append(f)
    return groups


# ── glob matching ────────────────────────────────────────────────────────────


def _glob_match(rel_path: str, pattern: str) -> bool:
    """Match a relative posix path against a glob pattern.

    Supports ``**`` (cross-directory) and standard ``fnmatch`` wildcards.
    For non-``**`` patterns, ``*`` does NOT cross ``/`` (path separators) —
    each path segment is matched independently, so ``*.yaml`` matches
    ``api.yaml`` but NOT ``deep/nested/api.yaml``. Use ``**/*.yaml`` to
    match across directories.
    """
    if "**" not in pattern:
        # Segment-wise match: * does not cross /
        pat_parts = pattern.split("/")
        path_parts = rel_path.split("/")
        if len(pat_parts) != len(path_parts):
            return False
        return all(
            fnmatch.fnmatchcase(pp, qp) for pp, qp in zip(path_parts, pat_parts)
        )

    pat_parts = pattern.split("/")
    path_parts = rel_path.split("/")
    return _match_globstar(pat_parts, path_parts, 0, 0)


def _match_globstar(
    pat_parts: list[str], path_parts: list[str], pi: int, si: int
) -> bool:
    """Recursive ``**`` matcher: ``**`` matches zero or more path segments."""
    if pi >= len(pat_parts):
        return si >= len(path_parts)
    if pat_parts[pi] == "**":
        for skip in range(si, len(path_parts) + 1):
            if _match_globstar(pat_parts, path_parts, pi + 1, skip):
                return True
        return False
    if si >= len(path_parts):
        return False
    if fnmatch.fnmatchcase(path_parts[si], pat_parts[pi]):
        return _match_globstar(pat_parts, path_parts, pi + 1, si + 1)
    return False
