"""Tests that the post-commit hook path (_rebuild_code) now picks up .yaml
swagger specs and runs the custom extractor on them.

Before the fix, _rebuild_code's doc-file collection (watch.py:1219-1225)
only included doc files with a built-in _get_extractor. .yaml had no built-in
extractor, so it was never in code_files/doc_targets, and
try_external_extractors (which runs inside extract() when code_index is passed)
never saw it — the swagger spec was invisible to git-commit-triggered rebuilds.

After the fix, _rebuild_code also includes doc files whose extensions are
declared by registered custom extractors (via external_extractor_extensions()),
so .yaml swagger specs enter doc_targets and the two-stage pipeline (which
already passes code_index in stage 2) fires extract_swagger on commit.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Registry extensions unit test
# ---------------------------------------------------------------------------

class TestExternalExtractorExtensions:
    def test_yaml_extensions_declared(self) -> None:
        """swagger extractor declares .yaml/.yml so _rebuild_code includes them."""
        from graphify.extractors.registry import external_extractor_extensions
        exts = external_extractor_extensions()
        assert ".yaml" in exts
        assert ".yml" in exts

    def test_returns_frozenset(self) -> None:
        from graphify.extractors.registry import external_extractor_extensions
        assert isinstance(external_extractor_extensions(), frozenset)


# ---------------------------------------------------------------------------
# Integration test: _rebuild_code processes .yaml swagger on the hook path
# ---------------------------------------------------------------------------

SWAGGER_YAML = """\
swagger: "2.0"
info:
  title: Hook Test API
  version: "1.0"
basePath: /rest
paths:
  /hooktest/v1/items:
    get:
      summary: List items
      description: Returns all items
      tags:
        - ItemController
      operationId: listItems
      responses:
        200:
          description: A list of items
          schema:
            type: array
"""

CONTROLLER_TS = """\
export class ItemController {
  listItems(): void {
    console.log("listing items");
  }
}
"""


class TestRebuildCodeProcessesSwaggerYaml:
    """Verify _rebuild_code (the post-commit hook entry point) now includes
    .yaml swagger specs in the rebuild scope."""

    @pytest.fixture
    def project(self, tmp_path: Path) -> Path:
        """Create a minimal project: src/ItemController.ts + docs/api.yaml."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "ItemController.ts").write_text(CONTROLLER_TS, encoding="utf-8")

        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "api.yaml").write_text(SWAGGER_YAML, encoding="utf-8")

        return tmp_path

    def test_yaml_enters_code_files(self, project: Path) -> None:
        """The key gap fix: .yaml doc files now enter code_files in _rebuild_code.

        We verify by running _rebuild_code and checking the output graph.json
        contains swagger endpoint nodes — which can only happen if the yaml
        file was in doc_targets and try_external_extractors ran on it.
        """
        from graphify.watch import _rebuild_code

        graph_out = project / ".graph"
        graph_json = graph_out / "graph.json"

        # Simulate a commit that touched both the code and the yaml
        changed = [
            project / "src" / "ItemController.ts",
            project / "docs" / "api.yaml",
        ]

        ok = _rebuild_code(
            project,
            changed_paths=changed,
            no_cluster=True,      # skip clustering for speed
            acquire_lock=False,   # no flock on Windows
        )
        assert ok, "_rebuild_code should succeed"

        # Read the output graph
        assert graph_json.exists(), "graph.json should be written"
        graph = json.loads(graph_json.read_text(encoding="utf-8"))
        nodes = graph.get("nodes", [])
        edges = graph.get("links", graph.get("edges", []))

        # 1. swagger_doc node exists
        doc_nodes = [n for n in nodes if n.get("node_kind") == "swagger_doc"]
        assert len(doc_nodes) == 1, f"expected 1 swagger_doc node, got {len(doc_nodes)}"

        # 2. rest_endpoint node exists (URL lives in the label; no method/
        #    full_path/operation_id/swagger_tags fields on the slim node)
        eps = [n for n in nodes if n.get("node_kind") == "rest_endpoint"]
        assert len(eps) == 1, f"expected 1 rest_endpoint, got {len(eps)}"
        assert eps[0]["label"] == "GET:/rest/hooktest/v1/items"
        assert eps[0]["tags"] == ["url"]

        # 3. The TS code node (ItemController class) is in the graph
        code_labels = [n.get("label") for n in nodes if n.get("file_type") == "code"]
        assert "ItemController" in code_labels

        # 4. references edge: endpoint -> ItemController class (code association)
        refs = [e for e in edges if e.get("relation") == "references"]
        ep_id = eps[0]["id"]
        ref_targets = [e["target"] for e in refs if e["source"] == ep_id]
        assert len(ref_targets) >= 1, (
            "expected endpoint to have references edges to code nodes"
        )

        # 5. contains edge: swagger_doc -> endpoint
        contains = [
            e for e in edges
            if e.get("relation") == "contains"
            and e["source"] == doc_nodes[0]["id"]
            and e["target"] == ep_id
        ]
        assert len(contains) == 1

    def test_yaml_only_change_triggers_extractor(self, project: Path) -> None:
        """When only the .yaml changes (no code), the extractor still fires.

        code_index will be empty (no code AST nodes from stage 1), so
        references edges won't be created — but the swagger endpoint nodes
        MUST still appear, proving the yaml entered doc_targets.
        """
        from graphify.watch import _rebuild_code

        # First rebuild to establish the graph (code + yaml)
        _rebuild_code(
            project,
            changed_paths=[
                project / "src" / "ItemController.ts",
                project / "docs" / "api.yaml",
            ],
            no_cluster=True,
            acquire_lock=False,
        )

        # Now change ONLY the yaml (add a second endpoint)
        updated_yaml = SWAGGER_YAML + """\
    post:
      summary: Create item
      tags:
        - ItemController
      operationId: createItem
      responses:
        201:
          description: Created
"""
        (project / "docs" / "api.yaml").write_text(updated_yaml, encoding="utf-8")

        # Rebuild with only the yaml as changed
        ok = _rebuild_code(
            project,
            changed_paths=[project / "docs" / "api.yaml"],
            no_cluster=True,
            acquire_lock=False,
        )
        assert ok

        graph = json.loads(
            (project / ".graph" / "graph.json").read_text(encoding="utf-8")
        )
        eps = [n for n in graph.get("nodes", []) if n.get("node_kind") == "rest_endpoint"]
        # Should now have 2 endpoints (GET + POST)
        assert len(eps) == 2, (
            f"expected 2 endpoints after yaml-only change, got {len(eps)}: "
            f"{[e['label'] for e in eps]}"
        )
        methods = {e["label"].split(":", 1)[0] for e in eps}
        assert methods == {"GET", "POST"}

    def test_non_swagger_yaml_not_in_code_files(self, project: Path) -> None:
        """A non-swagger .yaml (docker-compose) should NOT enter code_files
        and should NOT produce swagger nodes."""
        from graphify.watch import _rebuild_code

        # Add a docker-compose.yaml (non-swagger)
        (project / "docker-compose.yaml").write_text(
            "version: '3.8'\nservices:\n  web:\n    image: nginx\n",
            encoding="utf-8",
        )

        changed = [
            project / "src" / "ItemController.ts",
            project / "docs" / "api.yaml",
            project / "docker-compose.yaml",
        ]
        ok = _rebuild_code(
            project,
            changed_paths=changed,
            no_cluster=True,
            acquire_lock=False,
        )
        assert ok

        graph = json.loads(
            (project / ".graph" / "graph.json").read_text(encoding="utf-8")
        )
        # Only the swagger yaml should produce swagger_doc/rest_endpoint nodes
        doc_nodes = [n for n in graph.get("nodes", []) if n.get("node_kind") == "swagger_doc"]
        assert len(doc_nodes) == 1, "only the swagger yaml should produce swagger_doc nodes"
        # The docker-compose.yaml should not have created any swagger nodes
        eps = [n for n in graph.get("nodes", []) if n.get("node_kind") == "rest_endpoint"]
        # 1 endpoint from api.yaml, 0 from docker-compose.yaml
        assert all("hooktest" in e.get("label", "") for e in eps)
