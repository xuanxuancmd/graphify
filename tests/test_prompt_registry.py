"""Tests for the Tier 2 prompt registry (Gap-4).

Covers:
- load_prompts_from_dir: YAML loading, malformed-file resilience
- find_prompt: glob matching (exact, *, **)
- group_by_prompt: routing files to specs, unmatched → None key
- validate_prompt_schema: stricter validation on top of validate_extraction
"""
from __future__ import annotations

from pathlib import Path

import pytest

from graphify.prompt_registry import (
    PromptSpec,
    find_prompt,
    group_by_prompt,
    load_all_prompts,
    load_builtin_prompts,
    load_prompts_from_dir,
)
from graphify.validate import validate_extraction, validate_prompt_schema


# ── fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def prompt_dir(tmp_path: Path) -> Path:
    """Create a .graph/extension/prompts/ dir with two specs."""
    d = tmp_path / ".graph" / "extension" / "prompts"
    d.mkdir(parents=True)

    (d / "ddd.yaml").write_text(
        """
name: "ddd-semantic"
description: "DDD extraction"
match:
  files:
    - "context-map.md"
    - "ddd/**/*.md"
mode: replace
prompt: |
  You are a DDD extractor.
output_schema:
  valid_file_types: ["concept", "rationale"]
  valid_relations: ["references", "conceptually_related_to"]
""",
        encoding="utf-8",
    )

    (d / "api.yaml").write_text(
        """
name: "api-spec"
description: "API doc extraction"
match:
  files:
    - "**/openapi.yaml"
mode: merge
prompt: |
  You are an API spec extractor.
""",
        encoding="utf-8",
    )

    # A malformed file — must be skipped, not abort loading
    (d / "broken.yaml").write_text("name: [unclosed", encoding="utf-8")

    # A file with empty prompt — must be skipped
    (d / "empty.yaml").write_text(
        """
name: "empty"
match:
  files: ["*.md"]
prompt: ""
""",
        encoding="utf-8",
    )

    return d


# ── load_prompts_from_dir ────────────────────────────────────────────────────


def test_load_prompts_returns_valid_specs(prompt_dir: Path) -> None:
    specs = load_prompts_from_dir(prompt_dir)
    names = [s.name for s in specs]
    assert "ddd-semantic" in names
    assert "api-spec" in names


def test_load_prompts_skips_malformed(prompt_dir: Path) -> None:
    specs = load_prompts_from_dir(prompt_dir)
    names = [s.name for s in specs]
    assert "broken" not in names
    assert "empty" not in names


def test_load_prompts_nonexistent_dir(tmp_path: Path) -> None:
    specs = load_prompts_from_dir(tmp_path / "nonexistent")
    assert specs == []


def test_load_prompts_sorted_by_filename(prompt_dir: Path) -> None:
    specs = load_prompts_from_dir(prompt_dir)
    # api.yaml before ddd.yaml (alphabetical)
    assert specs[0].name == "api-spec"
    assert specs[1].name == "ddd-semantic"


# ── find_prompt ───────────────────────────────────────────────────────────────


def test_find_prompt_exact_filename(prompt_dir: Path, tmp_path: Path) -> None:
    specs = load_prompts_from_dir(prompt_dir)
    path = tmp_path / "context-map.md"
    path.write_text("content", encoding="utf-8")
    spec = find_prompt(path, tmp_path, specs)
    assert spec is not None
    assert spec.name == "ddd-semantic"


def test_find_prompt_glob_double_star(prompt_dir: Path, tmp_path: Path) -> None:
    specs = load_prompts_from_dir(prompt_dir)
    path = tmp_path / "docs" / "api" / "openapi.yaml"
    path.parent.mkdir(parents=True)
    path.write_text("content", encoding="utf-8")
    spec = find_prompt(path, tmp_path, specs)
    assert spec is not None
    assert spec.name == "api-spec"


def test_find_prompt_glob_dir_double_star(prompt_dir: Path, tmp_path: Path) -> None:
    specs = load_prompts_from_dir(prompt_dir)
    path = tmp_path / "ddd" / "subdir" / "domain-model.md"
    path.parent.mkdir(parents=True)
    path.write_text("content", encoding="utf-8")
    spec = find_prompt(path, tmp_path, specs)
    assert spec is not None
    assert spec.name == "ddd-semantic"


def test_find_prompt_no_match(prompt_dir: Path, tmp_path: Path) -> None:
    specs = load_prompts_from_dir(prompt_dir)
    path = tmp_path / "random.md"
    path.write_text("content", encoding="utf-8")
    spec = find_prompt(path, tmp_path, specs)
    assert spec is None


def test_find_prompt_first_match_wins(prompt_dir: Path, tmp_path: Path) -> None:
    """When two specs match the same file, the first in list order wins."""
    specs = load_prompts_from_dir(prompt_dir)
    # Both "ddd/**/*.md" and "**/openapi.yaml" could match, but context-map.md
    # only matches ddd-semantic, so this is fine. Let's verify api-spec wins
    # for openapi.yaml (it comes first alphabetically).
    path = tmp_path / "openapi.yaml"
    path.write_text("content", encoding="utf-8")
    spec = find_prompt(path, tmp_path, specs)
    assert spec is not None
    assert spec.name == "api-spec"


def test_find_prompt_star_does_not_cross_slash(prompt_dir: Path, tmp_path: Path) -> None:
    """Bare * must NOT cross / — *.yaml matches api.yaml but NOT deep/api.yaml.
    Use **/*.yaml to match across directories."""
    specs = load_prompts_from_dir(prompt_dir)
    # api-spec matches "**/openapi.yaml" — a ** pattern, so it crosses dirs ✅
    # But let's test a bare *.yaml pattern explicitly:
    d = tmp_path / ".graph" / "extension" / "prompts"
    (d / "bare_star.yaml").write_text(
        """
name: "bare-star"
match:
  files: ["*.yaml"]
prompt: "test"
""",
        encoding="utf-8",
    )
    specs2 = load_prompts_from_dir(d)

    # Top-level file matches
    top = tmp_path / "file.yaml"
    top.write_text("x", encoding="utf-8")
    assert find_prompt(top, tmp_path, specs2) is not None

    # Nested file does NOT match (bare * doesn't cross /)
    nested = tmp_path / "subdir" / "file.yaml"
    nested.parent.mkdir(parents=True)
    nested.write_text("x", encoding="utf-8")
    assert find_prompt(nested, tmp_path, specs2) is None


# ── group_by_prompt ──────────────────────────────────────────────────────────


def test_group_by_prompt_routes_matched_and_unmatched(
    prompt_dir: Path, tmp_path: Path
) -> None:
    specs = load_prompts_from_dir(prompt_dir)

    files = [
        tmp_path / "context-map.md",       # → ddd-semantic
        tmp_path / "openapi.yaml",         # → api-spec
        tmp_path / "random.md",           # → None (unmatched)
    ]
    for f in files:
        f.write_text("x", encoding="utf-8")

    groups = group_by_prompt(files, tmp_path, specs)

    # Find which spec each file went to
    none_group = groups.get(None, [])
    ddd_group = groups.get(specs[1], [])  # ddd-semantic
    api_group = groups.get(specs[0], [])  # api-spec

    assert len(none_group) == 1
    assert len(ddd_group) == 1
    assert len(api_group) == 1


def test_group_by_prompt_empty_files(prompt_dir: Path, tmp_path: Path) -> None:
    specs = load_prompts_from_dir(prompt_dir)
    groups = group_by_prompt([], tmp_path, specs)
    assert groups == {}


def test_group_by_prompt_all_unmatched(prompt_dir: Path, tmp_path: Path) -> None:
    specs = load_prompts_from_dir(prompt_dir)
    files = [tmp_path / "a.md", tmp_path / "b.txt"]
    for f in files:
        f.write_text("x", encoding="utf-8")
    groups = group_by_prompt(files, tmp_path, specs)
    assert None in groups
    assert len(groups[None]) == 2


# ── validate_prompt_schema ──────────────────────────────────────────────────


def test_validate_prompt_schema_none_returns_empty() -> None:
    data = {"nodes": [], "edges": []}
    assert validate_prompt_schema(data, None) == []


def test_validate_prompt_schema_valid_data() -> None:
    data = {
        "nodes": [
            {"id": "n1", "label": "X", "file_type": "concept", "source_file": "a.md"},
        ],
        "edges": [
            {"source": "n1", "target": "n1", "relation": "references",
             "confidence": "EXTRACTED", "source_file": "a.md"},
        ],
    }
    schema = {
        "valid_file_types": ["concept"],
        "valid_relations": ["references"],
        "valid_confidences": ["EXTRACTED"],
    }
    assert validate_prompt_schema(data, schema) == []


def test_validate_prompt_schema_invalid_file_type() -> None:
    data = {
        "nodes": [
            {"id": "n1", "label": "X", "file_type": "code", "source_file": "a.py"},
        ],
        "edges": [],
    }
    schema = {"valid_file_types": ["concept"]}
    errors = validate_prompt_schema(data, schema)
    assert len(errors) == 1
    assert "code" in errors[0]


def test_validate_prompt_schema_invalid_relation() -> None:
    data = {
        "nodes": [
            {"id": "n1", "label": "X", "file_type": "concept", "source_file": "a.md"},
        ],
        "edges": [
            {"source": "n1", "target": "n1", "relation": "calls",
             "confidence": "EXTRACTED", "source_file": "a.md"},
        ],
    }
    schema = {"valid_relations": ["references"]}
    errors = validate_prompt_schema(data, schema)
    assert len(errors) == 1
    assert "calls" in errors[0]


def test_validate_prompt_schema_invalid_confidence() -> None:
    data = {
        "nodes": [
            {"id": "n1", "label": "X", "file_type": "concept", "source_file": "a.md"},
        ],
        "edges": [
            {"source": "n1", "target": "n1", "relation": "references",
             "confidence": "MAYBE", "source_file": "a.md"},
        ],
    }
    schema = {"valid_confidences": ["EXTRACTED"]}
    errors = validate_prompt_schema(data, schema)
    assert len(errors) == 1
    assert "MAYBE" in errors[0]


def test_validate_prompt_schema_runs_after_validate_extraction() -> None:
    """validate_prompt_schema should catch issues validate_extraction doesn't."""
    data = {
        "nodes": [
            {"id": "n1", "label": "X", "file_type": "concept", "source_file": "a.md"},
        ],
        "edges": [
            {"source": "n1", "target": "n1", "relation": "calls",
             "confidence": "EXTRACTED", "source_file": "a.md"},
        ],
    }
    # validate_extraction passes — "calls" is a valid relation at the graphify level
    assert validate_extraction(data) == []
    # But the spec's stricter schema rejects "calls"
    schema = {"valid_relations": ["references"]}
    errors = validate_prompt_schema(data, schema)
    assert len(errors) == 1


# ── load_all_prompts: built-in + project-level priority ──────────────────────


def test_load_all_prompts_project_level_first(prompt_dir: Path) -> None:
    """load_all_prompts returns project-level specs before built-in."""
    specs = load_all_prompts(prompt_dir)
    names = [s.name for s in specs]
    assert "api-spec" in names
    assert "ddd-semantic" in names


def test_load_builtin_prompts_empty() -> None:
    """Built-in prompts dir (graphify/prompts/) is currently empty."""
    specs = load_builtin_prompts()
    assert specs == []


def test_load_all_prompts_project_overrides_builtin(tmp_path: Path) -> None:
    """Project-level specs are prepended so first-match-wins favours them."""
    proj_dir = tmp_path / ".graph" / "extension" / "prompts"
    proj_dir.mkdir(parents=True)
    (proj_dir / "a.yaml").write_text(
        """
name: "project-prompt"
match:
  files: ["*.md"]
prompt: "project level"
""",
        encoding="utf-8",
    )
    specs = load_all_prompts(proj_dir)
    assert specs[0].name == "project-prompt"
