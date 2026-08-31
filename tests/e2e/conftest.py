"""conftest.py for tests/e2e/ — ensures graph.json is built before tests run.

This module runs the graphify CLI once at session start to generate
``.graph/graph.json`` on the user-management fixture project. The
extraction uses ``--allow-partial`` with a fake API key so that:

  - Stage 1 (code AST) runs normally (no API key needed)
  - Stage 2 (DDD doc extraction) runs normally (no API key needed — the
    DDD extractor is an AST/regex parser, not an LLM call)
  - LLM Tier 2 (semantic extraction) fails (no real API key), but
    ``--allow-partial`` lets the pipeline write the AST + DDD nodes to
    graph.json instead of exiting with an error

The resulting graph.json contains code AST nodes + DDD doc-anchor nodes +
default markdown page/heading nodes, but NOT LLM semantic concept nodes.
That's sufficient for verifying the DDD extractor integration.

Set ``GRAPHIFY_E2E_FORCE=1`` to force a rebuild (deletes existing
.graph/ and the stale root-level ddd-unmatched.json before
re-extracting). Use this after implementing extractor changes so the
E2E tests run against the fresh graph, not a stale cached one.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent / "resources" / "user-management"
GRAPH_JSON = PROJECT_ROOT / ".graph" / "graph.json"


def _run_extraction() -> None:
    """Run graphify extract on the fixture project."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent.parent.parent)
    env["OPENAI_API_KEY"] = "sk-fake-key-for-e2e-test"
    # tests/conftest.py sets GRAPHIFY_OUT=.graph for upstream tests.
    # Override to .graph so the output matches GRAPH_JSON below.
    env["GRAPHIFY_OUT"] = ".graph"
    cmd = [
        sys.executable, "-m", "graphify", "extract",
        str(PROJECT_ROOT),
        "--backend", "openai",
        "--allow-partial",
        "--no-cluster",
        "--no-viz",
    ]
    subprocess.run(cmd, env=env, capture_output=True, timeout=300)


@pytest.fixture(scope="session", autouse=True)
def ensure_graph_json():
    """Build graph.json once per test session if it doesn't exist.

    Tests in test_user_management_e2e.py read graph.json, not extract()
    directly. This fixture ensures the CLI-generated graph is available
    before any test runs. If graph.json already exists (e.g. from a prior
    manual run), the extraction is skipped to save time — unless
    GRAPHIFY_E2E_FORCE=1 is set, which deletes the old output and rebuilds.
    """
    force = os.environ.get("GRAPHIFY_E2E_FORCE", "") == "1"
    if GRAPH_JSON.exists() and not force:
        print("[e2e] graph.json already exists, skipping extraction")
        yield
        return
    # Clean up old output + stale root-level ddd-unmatched.json (.mjs legacy)
    out_dir = PROJECT_ROOT / ".graph"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    stale = PROJECT_ROOT / "ddd-unmatched.json"
    if stale.exists():
        stale.unlink()
    print("\n[e2e] Building graph.json for user-management project...")
    _run_extraction()
    if not GRAPH_JSON.exists():
        pytest.fail(
            "Failed to build graph.json — check that graphify extract works "
            "with --allow-partial and a fake API key"
        )
    print(f"[e2e] graph.json built: {GRAPH_JSON.stat().st_size} bytes")
    yield
