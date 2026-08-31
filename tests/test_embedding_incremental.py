"""Tests for the incremental embedding update logic.

Verifies:
1. _git_diff_changed_node_ids correctly finds changed node_ids with --unified=30
2. _extract_embed_text_from_git_version retrieves old desc from git history
3. generate_embeddings_incremental only re-embeds nodes whose desc/rationale changed
4. community-only changes do NOT trigger re-embed
5. new/deleted nodes are handled correctly
6. fallback to full rebuild when no git history / corrupt sidecar
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest

from graphify.embeddings import (
    _node_embed_text,
    _git_diff_changed_node_ids,
    _extract_embed_text_from_git_version,
    generate_embeddings_for_graph,
    generate_embeddings_incremental,
    _sidecar_paths,
    _write_sidecar_meta,
)


# ---------------------------------------------------------------------------
# Helpers: create a fake git repo with graph.json
# ---------------------------------------------------------------------------

def _make_graph_json(nodes: list[dict]) -> dict:
    """Build a minimal graph.json structure."""
    return {
        "nodes": nodes,
        "links": [],
        "hyperedges": [],
        "built_at_commit": "",
    }


def _node(id: str, desc: str = "", rationale: str = "", community: int = 0, label: str = "") -> dict:
    n = {"id": id, "label": label or id, "file_type": "code", "source_file": f"src/{id}.py", "community": community}
    if desc:
        n["desc"] = desc
    if rationale:
        n["rationale"] = rationale
    return n


def _init_git_repo(repo_dir: Path) -> str:
    """Init a git repo, return the initial commit hash."""
    subprocess.run(["git", "init"], cwd=str(repo_dir), capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=str(repo_dir), capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=str(repo_dir), capture_output=True, check=True)
    subprocess.run(["git", "add", "-A"], cwd=str(repo_dir), capture_output=True, check=True)
    r = subprocess.run(["git", "commit", "-m", "init"], cwd=str(repo_dir), capture_output=True, text=True, check=True)
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(repo_dir), capture_output=True, text=True, check=True).stdout.strip()


def _commit(repo_dir: Path, msg: str = "update") -> str:
    subprocess.run(["git", "add", "-A"], cwd=str(repo_dir), capture_output=True, check=True)
    r = subprocess.run(["git", "commit", "-m", msg], cwd=str(repo_dir), capture_output=True, text=True)
    # Allow empty commits too
    if r.returncode != 0:
        subprocess.run(["git", "commit", "--allow-empty", "-m", msg], cwd=str(repo_dir), capture_output=True, check=True)
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(repo_dir), capture_output=True, text=True, check=True).stdout.strip()


def _make_sidecar(graph_dir: Path, node_ids: list[str], model: str = "test-model", dim: int = 4, graph_commit: str = ""):
    """Create a fake embedding sidecar with random vectors."""
    paths = _sidecar_paths(graph_dir, model)
    paths["npy"].parent.mkdir(parents=True, exist_ok=True)
    n = len(node_ids)
    if n > 0:
        matrix = np.random.rand(n, dim).astype(np.float32)
    else:
        matrix = np.zeros((0, dim), dtype=np.float32)
    np.save(paths["npy"], matrix)
    paths["index"].write_text(json.dumps({
        "node_ids": node_ids,
        "model": model,
        "dim": dim,
    }), encoding="utf-8")
    _write_sidecar_meta(paths, graph_dir / "graph.json", {"built_at_commit": graph_commit},
                        node_ids, model, "test-backend", dim)
    return paths


# ---------------------------------------------------------------------------
# Test 1: _node_embed_text behavior (desc → rationale → empty)
# ---------------------------------------------------------------------------

class TestNodeEmbedText:
    def test_desc_priority(self):
        assert _node_embed_text({"desc": "doc", "rationale": "why", "label": "fn"}) == "doc"

    def test_rationale_fallback(self):
        assert _node_embed_text({"desc": "", "rationale": "why", "label": "fn"}) == "why"

    def test_empty_when_neither(self):
        assert _node_embed_text({"label": "fn"}) == ""

    def test_rationale_truncation(self):
        long_r = "x" * 600
        assert len(_node_embed_text({"rationale": long_r})) == 512


# ---------------------------------------------------------------------------
# Test 2: _git_diff_changed_node_ids with --unified=30
# ---------------------------------------------------------------------------

class TestGitDiffChangedNodeIds:
    def test_desc_change_is_detected(self, tmp_path):
        """The core bug fix: desc change must be detected even though the
        changed line doesn't contain 'id' — the --unified=30 context
        includes the id line."""
        repo_dir = tmp_path / "repo"
        graph_dir = repo_dir / ".graph"
        graph_dir.mkdir(parents=True)
        graph_path = graph_dir / "graph.json"

        # Commit 1: two nodes, each with a desc
        data = _make_graph_json([
            _node("A", desc="old desc A", community=1),
            _node("B", desc="old desc B", community=2),
        ])
        graph_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        old_commit = _init_git_repo(repo_dir)

        # Commit 2: change only A's desc (B unchanged)
        data2 = _make_graph_json([
            _node("A", desc="NEW desc A", community=1),
            _node("B", desc="old desc B", community=2),
        ])
        graph_path.write_text(json.dumps(data2, indent=2), encoding="utf-8")
        new_commit = _commit(repo_dir)

        changed = _git_diff_changed_node_ids(graph_path, old_commit)
        assert changed is not None, "git diff should succeed"
        assert "A" in changed, "node A desc changed → must be in changed set"
        # B might also appear in context, that's fine — the caller does precise comparison

    def test_community_only_change_may_appear_but_desc_same(self, tmp_path):
        """When only community changes, the node may appear in the diff, but
        _extract_embed_text_from_git_version should return the same desc →
        the caller skips it."""
        repo_dir = tmp_path / "repo"
        graph_dir = repo_dir / ".graph"
        graph_dir.mkdir(parents=True)
        graph_path = graph_dir / "graph.json"

        data = _make_graph_json([
            _node("A", desc="same desc", community=1),
        ])
        graph_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        old_commit = _init_git_repo(repo_dir)

        data2 = _make_graph_json([
            _node("A", desc="same desc", community=2),
        ])
        graph_path.write_text(json.dumps(data2, indent=2), encoding="utf-8")
        _commit(repo_dir)

        changed = _git_diff_changed_node_ids(graph_path, old_commit)
        assert changed is not None
        # The node may appear (community changed → JSON line changed),
        # but the old embed text should match the new one:
        old_text = _extract_embed_text_from_git_version(graph_path, old_commit, "A")
        assert old_text == "same desc", "old desc should be 'same desc'"

    def test_no_changes_returns_empty(self, tmp_path):
        repo_dir = tmp_path / "repo"
        graph_dir = repo_dir / ".graph"
        graph_dir.mkdir(parents=True)
        graph_path = graph_dir / "graph.json"

        data = _make_graph_json([_node("A", desc="desc")])
        graph_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        old_commit = _init_git_repo(repo_dir)
        # No new commit — HEAD == old_commit
        changed = _git_diff_changed_node_ids(graph_path, old_commit)
        assert changed == set()

    def test_empty_old_commit_returns_none(self, tmp_path):
        """When old_commit is empty, should return None (no basis to diff)."""
        graph_path = tmp_path / ".graph" / "graph.json"
        assert _git_diff_changed_node_ids(graph_path, "") is None

    def test_not_a_git_repo_returns_none(self, tmp_path):
        """When the path is not in a git repo, should return None."""
        graph_path = tmp_path / ".graph" / "graph.json"
        graph_path.parent.mkdir(parents=True)
        assert _git_diff_changed_node_ids(graph_path, "abc123") is None


# ---------------------------------------------------------------------------
# Test 3: _extract_embed_text_from_git_version
# ---------------------------------------------------------------------------

class TestExtractEmbedTextFromGit:
    def test_retrieves_old_desc(self, tmp_path):
        repo_dir = tmp_path / "repo"
        graph_dir = repo_dir / ".graph"
        graph_dir.mkdir(parents=True)
        graph_path = graph_dir / "graph.json"

        data = _make_graph_json([_node("A", desc="original desc")])
        graph_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        old_commit = _init_git_repo(repo_dir)

        # Change to a new desc and commit
        data2 = _make_graph_json([_node("A", desc="new desc")])
        graph_path.write_text(json.dumps(data2, indent=2), encoding="utf-8")
        _commit(repo_dir)

        old_text = _extract_embed_text_from_git_version(graph_path, old_commit, "A")
        assert old_text == "original desc"

    def test_retrieves_rationale_when_no_desc(self, tmp_path):
        repo_dir = tmp_path / "repo"
        graph_dir = repo_dir / ".graph"
        graph_dir.mkdir(parents=True)
        graph_path = graph_dir / "graph.json"

        data = _make_graph_json([_node("A", rationale="old rationale")])
        graph_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        old_commit = _init_git_repo(repo_dir)

        data2 = _make_graph_json([_node("A", rationale="new rationale")])
        graph_path.write_text(json.dumps(data2, indent=2), encoding="utf-8")
        _commit(repo_dir)

        old_text = _extract_embed_text_from_git_version(graph_path, old_commit, "A")
        assert old_text == "old rationale"

    def test_nonexistent_node_returns_empty(self, tmp_path):
        repo_dir = tmp_path / "repo"
        graph_dir = repo_dir / ".graph"
        graph_dir.mkdir(parents=True)
        graph_path = graph_dir / "graph.json"

        data = _make_graph_json([_node("A", desc="desc")])
        graph_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        old_commit = _init_git_repo(repo_dir)

        text = _extract_embed_text_from_git_version(graph_path, old_commit, "nonexistent")
        assert text == ""

    def test_invalid_commit_returns_empty(self, tmp_path):
        repo_dir = tmp_path / "repo"
        graph_dir = repo_dir / ".graph"
        graph_dir.mkdir(parents=True)
        graph_path = graph_dir / "graph.json"

        data = _make_graph_json([_node("A", desc="desc")])
        graph_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        _init_git_repo(repo_dir)

        text = _extract_embed_text_from_git_version(graph_path, "0000000000000000000000000000000000000000", "A")
        assert text == ""


# ---------------------------------------------------------------------------
# Test 4: generate_embeddings_incremental integration
# ---------------------------------------------------------------------------

class TestGenerateEmbeddingsIncremental:
    """Integration tests using a mock embedding backend."""

    @pytest.fixture
    def git_repo_with_graph(self, tmp_path):
        """Create a git repo with a graph.json and an initial embedding sidecar."""
        repo_dir = tmp_path / "repo"
        graph_dir = repo_dir / ".graph"
        graph_dir.mkdir(parents=True)
        graph_path = graph_dir / "graph.json"

        nodes = [
            _node("A", desc="desc A", community=1),
            _node("B", desc="desc B", community=2),
            _node("C", desc="desc C", community=3),
        ]
        data = _make_graph_json(nodes)
        graph_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        commit = _init_git_repo(repo_dir)

        # Create initial sidecar
        _make_sidecar(graph_dir, ["A", "B", "C"], model="test-model", dim=4, graph_commit=commit)

        # Write graphifyrc to configure the backend
        (graph_dir / "graphifyrc").write_text(
            "embed_backend=sentence-transformers\nembed_model=test-model\n",
            encoding="utf-8",
        )

        return repo_dir, graph_path, commit

    @patch("graphify.embeddings._embed_batch")
    def test_desc_change_only_embeds_changed_node(self, mock_embed, git_repo_with_graph):
        """When only one node's desc changes, only that node should be re-embedded."""
        repo_dir, graph_path, old_commit = git_repo_with_graph

        # Change only node B's desc
        data = _make_graph_json([
            _node("A", desc="desc A", community=1),
            _node("B", desc="NEW desc B", community=2),
            _node("C", desc="desc C", community=3),
        ])
        data["built_at_commit"] = "new_commit_hash"
        graph_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        _commit(repo_dir)

        # Mock: return a 1-row matrix (only B changed)
        mock_embed.return_value = (np.array([[0.1, 0.2, 0.3, 0.4]], dtype=np.float32), "test-model")

        result = generate_embeddings_incremental(graph_path, backend="sentence-transformers", model="test-model")

        assert result is not None
        mock_embed.assert_called_once()
        # The texts passed to _embed_batch should contain only the changed node's desc
        args = mock_embed.call_args[0]
        texts = args[0]
        assert len(texts) == 1, f"expected 1 text (only B changed), got {len(texts)}"
        assert "NEW desc B" in texts[0]

    @patch("graphify.embeddings._embed_batch")
    def test_community_only_change_no_embed(self, mock_embed, git_repo_with_graph):
        """When only community changes (desc stays the same), no re-embed should happen."""
        repo_dir, graph_path, old_commit = git_repo_with_graph

        # Change only node A's community (desc unchanged)
        data = _make_graph_json([
            _node("A", desc="desc A", community=99),  # community changed
            _node("B", desc="desc B", community=2),
            _node("C", desc="desc C", community=3),
        ])
        data["built_at_commit"] = "new_commit_hash"
        graph_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        _commit(repo_dir)

        mock_embed.return_value = (np.zeros((0, 4), dtype=np.float32), "test-model")

        result = generate_embeddings_incremental(graph_path, backend="sentence-transformers", model="test-model")

        assert result is not None
        # _embed_batch should NOT be called (no desc changed)
        mock_embed.assert_not_called()

    @patch("graphify.embeddings._embed_batch")
    def test_new_node_gets_embedded(self, mock_embed, git_repo_with_graph):
        """A newly added node should be embedded."""
        repo_dir, graph_path, old_commit = git_repo_with_graph

        # Add a new node D
        data = _make_graph_json([
            _node("A", desc="desc A", community=1),
            _node("B", desc="desc B", community=2),
            _node("C", desc="desc C", community=3),
            _node("D", desc="desc D", community=4),  # new node
        ])
        data["built_at_commit"] = "new_commit_hash"
        graph_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        _commit(repo_dir)

        mock_embed.return_value = (np.array([[0.5, 0.6, 0.7, 0.8]], dtype=np.float32), "test-model")

        result = generate_embeddings_incremental(graph_path, backend="sentence-transformers", model="test-model")

        assert result is not None
        mock_embed.assert_called_once()
        args = mock_embed.call_args[0]
        texts = args[0]
        assert len(texts) == 1
        assert "desc D" in texts[0]

    @patch("graphify.embeddings._embed_batch")
    def test_deleted_node_removed_from_index(self, mock_embed, git_repo_with_graph):
        """A deleted node should be removed from the index."""
        repo_dir, graph_path, old_commit = git_repo_with_graph

        # Remove node C
        data = _make_graph_json([
            _node("A", desc="desc A", community=1),
            _node("B", desc="desc B", community=2),
            # C deleted
        ])
        data["built_at_commit"] = "new_commit_hash"
        graph_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        _commit(repo_dir)

        mock_embed.return_value = (np.zeros((0, 4), dtype=np.float32), "test-model")

        result = generate_embeddings_incremental(graph_path, backend="sentence-transformers", model="test-model")

        assert result is not None
        # No re-embed needed (only deletion)
        mock_embed.assert_not_called()

        # Check index: C should be gone
        emb_dir = graph_path.parent / "embeddings"
        index_data = json.loads((emb_dir / "embedding.index.json").read_text(encoding="utf-8"))
        assert "C" not in index_data["node_ids"], "deleted node C should not be in index"
        assert "A" in index_data["node_ids"]
        assert "B" in index_data["node_ids"]

    @patch("graphify.embeddings._embed_batch")
    def test_no_sidecar_falls_back_to_full(self, mock_embed, tmp_path):
        """When no sidecar exists, should fall back to full rebuild."""
        repo_dir = tmp_path / "repo"
        graph_dir = repo_dir / ".graph"
        graph_dir.mkdir(parents=True)
        graph_path = graph_dir / "graph.json"

        data = _make_graph_json([_node("A", desc="desc A")])
        graph_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        _init_git_repo(repo_dir)

        mock_embed.return_value = (np.array([[0.1, 0.2, 0.3, 0.4]], dtype=np.float32), "test-model")

        # No sidecar → full rebuild
        result = generate_embeddings_incremental(graph_path, backend="sentence-transformers", model="test-model")

        assert result is not None
        mock_embed.assert_called_once()
        args = mock_embed.call_args[0]
        texts = args[0]
        assert len(texts) == 1  # all nodes embedded

    @patch("graphify.embeddings._embed_batch")
    def test_corrupt_sidecar_falls_back_to_full(self, mock_embed, git_repo_with_graph):
        """When the sidecar is corrupt, should fall back to full rebuild."""
        repo_dir, graph_path, old_commit = git_repo_with_graph
        emb_dir = graph_path.parent / "embeddings"

        # Corrupt the .npy file
        (emb_dir / "embedding.npy").write_bytes(b"corrupt data")

        mock_embed.return_value = (np.array([[0.1, 0.2, 0.3, 0.4]], dtype=np.float32), "test-model")

        result = generate_embeddings_incremental(graph_path, backend="sentence-transformers", model="test-model")

        assert result is not None
        mock_embed.assert_called_once()  # full rebuild

    @patch("graphify.embeddings._embed_batch")
    def test_no_git_history_falls_back_to_set_comparison(self, mock_embed, tmp_path):
        """When not a git repo, should use set comparison (new/deleted only, no desc-change detection)."""
        graph_dir = tmp_path / ".graph"
        graph_dir.mkdir(parents=True)
        graph_path = graph_dir / "graph.json"

        # Initial graph + sidecar (no git)
        data = _make_graph_json([_node("A", desc="desc A"), _node("B", desc="desc B")])
        graph_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        _make_sidecar(graph_dir, ["A", "B"], model="test-model", dim=4, graph_commit="")

        # New version: A's desc changed (but no git history to detect it), B unchanged, C new
        data2 = _make_graph_json([
            _node("A", desc="CHANGED desc A"),  # desc changed but without git we can't detect it
            _node("B", desc="desc B"),
            _node("C", desc="desc C"),  # new node
        ])
        data2["built_at_commit"] = ""
        graph_path.write_text(json.dumps(data2, indent=2), encoding="utf-8")

        mock_embed.return_value = (np.array([[0.5, 0.6, 0.7, 0.8]], dtype=np.float32), "test-model")

        result = generate_embeddings_incremental(graph_path, backend="sentence-transformers", model="test-model")

        assert result is not None
        mock_embed.assert_called_once()
        args = mock_embed.call_args[0]
        texts = args[0]
        # Without git, only new nodes (C) are detected — A's desc change is missed.
        # This is the known limitation; the daily full rebuild catches it.
        assert len(texts) == 1
        assert "desc C" in texts[0]

    @patch("graphify.embeddings._embed_batch")
    def test_large_change_falls_back_to_full(self, mock_embed, git_repo_with_graph):
        """When >50% of nodes changed, should fall back to full rebuild."""
        repo_dir, graph_path, old_commit = git_repo_with_graph

        # Change desc of 2 out of 3 nodes (>50%)
        data = _make_graph_json([
            _node("A", desc="NEW desc A", community=1),
            _node("B", desc="NEW desc B", community=2),
            _node("C", desc="desc C", community=3),
        ])
        data["built_at_commit"] = "new_commit_hash"
        graph_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        _commit(repo_dir)

        # Full rebuild will call _embed_batch with ALL texts
        mock_embed.return_value = (
            np.array([[0.1, 0.2, 0.3, 0.4],
                       [0.5, 0.6, 0.7, 0.8],
                       [0.9, 0.1, 0.2, 0.3]], dtype=np.float32),
            "test-model",
        )

        result = generate_embeddings_incremental(graph_path, backend="sentence-transformers", model="test-model")

        assert result is not None
        mock_embed.assert_called_once()
        args = mock_embed.call_args[0]
        texts = args[0]
        assert len(texts) == 3, f"full rebuild should embed all 3 nodes, got {len(texts)}"


# ---------------------------------------------------------------------------
# BUG 1+2 tests: _check_single_project staleness detection
# ---------------------------------------------------------------------------

class TestCheckSingleProjectStaleness:
    """Tests for the staleness detection logic in _check_single_project.

    Covers:
    - BUG 1: same-commit content change (API failure scenario) → must be stale
    - BUG 2: non-git project desc-only change → must be stale
    - Normal scenarios: fresh / new-commit / node-count change
    """

    @pytest.fixture
    def project_with_sidecar(self, tmp_path):
        """Create a project dir with graph.json + embedding sidecar."""
        graph_dir = tmp_path / ".graph"
        graph_dir.mkdir(parents=True)
        graph_path = graph_dir / "graph.json"

        nodes = [_node("A", desc="desc A"), _node("B", desc="desc B")]
        data = _make_graph_json(nodes)
        data["built_at_commit"] = "commit_abc"
        graph_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

        # Create sidecar with matching commit
        _make_sidecar(graph_dir, ["A", "B"], model="test-model", dim=4, graph_commit="commit_abc")

        # Write graphifyrc
        (graph_dir / "graphifyrc").write_text(
            "embed_backend=sentence-transformers\nembed_model=test-model\n",
            encoding="utf-8",
        )

        return tmp_path, graph_path

    @patch("graphify.cli._launch_embedding_refresh")
    @patch("graphify.cli._do_embedding_refresh")
    def test_fresh_when_commit_matches_and_mtime_ok(self, mock_do, mock_launch, project_with_sidecar):
        """When commit matches and meta is newer than graph → fresh (no refresh)."""
        tmp_path, graph_path = project_with_sidecar

        # meta is newer than graph (just created after graph)
        import time as _t
        _t.sleep(0.05)
        # Touch meta to make it newer
        meta_path = graph_path.parent / "embeddings" / "embedding.meta.json"
        meta_path.touch()

        from graphify.cli import _check_single_project
        _check_single_project(graph_path, detach=True)

        mock_launch.assert_not_called()
        mock_do.assert_not_called()

    @patch("graphify.cli._launch_embedding_refresh")
    @patch("graphify.cli._do_embedding_refresh")
    def test_stale_when_commit_mismatch(self, mock_do, mock_launch, project_with_sidecar):
        """BUG coverage: different commit → stale → refresh triggered."""
        tmp_path, graph_path = project_with_sidecar

        # Change graph.json's built_at_commit and make it newer than meta
        import time as _t
        _t.sleep(0.1)
        data = json.loads(graph_path.read_text(encoding="utf-8"))
        data["built_at_commit"] = "commit_new"
        graph_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

        from graphify.cli import _check_single_project
        _check_single_project(graph_path, detach=True)

        mock_launch.assert_called_once()

    @patch("graphify.cli._launch_embedding_refresh")
    @patch("graphify.cli._do_embedding_refresh")
    def test_stale_when_same_commit_but_graph_newer(self, mock_do, mock_launch, project_with_sidecar):
        """BUG 1: same commit but graph.json mtime > meta mtime → must be stale.

        Scenario: post-commit hook rebuilt graph.json (same built_at_commit),
        but embedding API failed → meta not updated. graph.json is newer but
        commit matches. Without the fix, stale=False → never refreshes.
        """
        tmp_path, graph_path = project_with_sidecar

        # Rebuild graph.json at same commit but with newer mtime
        import time as _t
        _t.sleep(0.1)
        data = json.loads(graph_path.read_text(encoding="utf-8"))
        # Same commit, but change a desc (simulates rebuild after code change)
        data["nodes"][0]["desc"] = "NEW desc A"
        data["built_at_commit"] = "commit_abc"  # SAME commit
        graph_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

        from graphify.cli import _check_single_project
        _check_single_project(graph_path, detach=True)

        # Must detect as stale and trigger refresh
        mock_launch.assert_called_once()

    @patch("graphify.cli._launch_embedding_refresh")
    @patch("graphify.cli._do_embedding_refresh")
    def test_stale_when_non_git_and_graph_newer(self, mock_do, mock_launch, tmp_path):
        """BUG 2: non-git project, no commit info, graph newer than meta → stale.

        Without the fix, empty commits on both sides → stale = False (misses
        desc-only changes). The graph_is_newer flag should catch this.
        """
        graph_dir = tmp_path / ".graph"
        graph_dir.mkdir(parents=True)
        graph_path = graph_dir / "graph.json"

        # Non-git: no built_at_commit
        data = _make_graph_json([_node("A", desc="desc A"), _node("B", desc="desc B")])
        data.pop("built_at_commit", None)
        graph_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

        _make_sidecar(graph_dir, ["A", "B"], model="test-model", dim=4, graph_commit="")
        (graph_dir / "graphifyrc").write_text(
            "embed_backend=sentence-transformers\nembed_model=test-model\n",
            encoding="utf-8",
        )

        # Wait, then rebuild graph with same node count but different desc
        import time as _t
        _t.sleep(0.1)
        data2 = _make_graph_json([_node("A", desc="CHANGED desc A"), _node("B", desc="desc B")])
        data2.pop("built_at_commit", None)
        graph_path.write_text(json.dumps(data2, indent=2), encoding="utf-8")

        from graphify.cli import _check_single_project
        _check_single_project(graph_path, detach=True)

        mock_launch.assert_called_once()

    @patch("graphify.cli._launch_embedding_refresh")
    @patch("graphify.cli._do_embedding_refresh")
    def test_fresh_when_non_git_and_no_change(self, mock_do, mock_launch, tmp_path):
        """Non-git project, no commit, no mtime delta → fresh."""
        graph_dir = tmp_path / ".graph"
        graph_dir.mkdir(parents=True)
        graph_path = graph_dir / "graph.json"

        data = _make_graph_json([_node("A", desc="desc A")])
        data.pop("built_at_commit", None)
        graph_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

        _make_sidecar(graph_dir, ["A"], model="test-model", dim=4, graph_commit="")
        (graph_dir / "graphifyrc").write_text(
            "embed_backend=sentence-transformers\nembed_model=test-model\n",
            encoding="utf-8",
        )

        # Make meta newer than graph
        import time as _t
        _t.sleep(0.05)
        (graph_dir / "embeddings" / "embedding.meta.json").touch()

        from graphify.cli import _check_single_project
        _check_single_project(graph_path, detach=True)

        mock_launch.assert_not_called()
        mock_do.assert_not_called()

    @patch("graphify.cli._launch_embedding_refresh")
    @patch("graphify.cli._do_embedding_refresh")
    def test_stale_when_sidecar_missing(self, mock_do, mock_launch, tmp_path):
        """No sidecar → stale → refresh triggered."""
        graph_dir = tmp_path / ".graph"
        graph_dir.mkdir(parents=True)
        graph_path = graph_dir / "graph.json"

        data = _make_graph_json([_node("A", desc="desc A")])
        data["built_at_commit"] = "commit_abc"
        graph_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        (graph_dir / "graphifyrc").write_text(
            "embed_backend=sentence-transformers\nembed_model=test-model\n",
            encoding="utf-8",
        )

        from graphify.cli import _check_single_project
        _check_single_project(graph_path, detach=True)

        mock_launch.assert_called_once()

    @patch("graphify.cli._launch_embedding_refresh")
    @patch("graphify.cli._do_embedding_refresh")
    def test_no_backend_skips_check(self, mock_do, mock_launch, tmp_path):
        """When no embedding backend is configured → skip entirely."""
        graph_dir = tmp_path / ".graph"
        graph_dir.mkdir(parents=True)
        graph_path = graph_dir / "graph.json"

        data = _make_graph_json([_node("A", desc="desc A")])
        data["built_at_commit"] = "commit_abc"
        graph_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        # No graphifyrc → no backend configured

        from graphify.cli import _check_single_project
        _check_single_project(graph_path, detach=True)

        mock_launch.assert_not_called()
        mock_do.assert_not_called()


# ---------------------------------------------------------------------------
# BUG 4 test: _schedule_status checks correct cron command
# ---------------------------------------------------------------------------

class TestScheduleStatus:
    """Verify _schedule_status looks for the correct command string."""

    def test_status_finds_registered_cron(self, tmp_path, monkeypatch):
        """When cron has 'graphify check --all', status should find it."""
        import graphify.cli as cli_module

        # Mock crontab -l to return a line with the correct command
        cron_line = "30 2 * * * \"graphify\" check --all >> ~/.cache/graphify-daily.log 2>&1  # graphify-daily"
        mock_result = MagicMock()
        mock_result.stdout = cron_line + "\n"
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result):
            # Force POSIX path
            monkeypatch.setattr(os, "name", "posix")
            with patch.object(cli_module, "_is_wsl", return_value=False):
                # Capture stdout
                import io
                import contextlib
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    cli_module._schedule_status("graphify")
                output = buf.getvalue()
                assert "registered" in output.lower(), f"status should find the task: {output}"


# ---------------------------------------------------------------------------
# BUG 5 test: detach child uses correct GRAPHIFY_OUT and cwd
# ---------------------------------------------------------------------------

class TestLaunchEmbeddingRefresh:
    """Verify _launch_embedding_refresh passes correct env + cwd."""

    @patch("subprocess.Popen")
    def test_default_graphify_out_preserved(self, mock_popen, tmp_path, monkeypatch):
        """Default GRAPHIFY_OUT='.graph' should be passed to child as-is."""
        import graphify.cli as cli_module

        # Ensure clean env — previous tests may have set GRAPHIFY_OUT
        monkeypatch.delenv("GRAPHIFY_OUT", raising=False)
        # Reload paths to pick up the default
        import importlib
        import graphify.paths
        importlib.reload(graphify.paths)
        importlib.reload(cli_module)

        graph_dir = tmp_path / ".graph"
        graph_dir.mkdir(parents=True)

        # Mock _resolve_graphify_exe (imported from install.py into cli.py)
        with patch("graphify.install._resolve_graphify_exe", return_value="graphify"):
            cli_module._launch_embedding_refresh(graph_dir)

        # Check the Popen call
        assert mock_popen.called
        kwargs = mock_popen.call_args.kwargs
        env = kwargs.get("env", {})
        assert env.get("GRAPHIFY_OUT") == ".graph", \
            f"expected GRAPHIFY_OUT='.graph', got {env.get('GRAPHIFY_OUT')}"

    @patch("subprocess.Popen")
    def test_custom_graphify_out_preserved(self, mock_popen, tmp_path, monkeypatch):
        """Custom GRAPHIFY_OUT should be passed to child as-is."""
        import graphify.cli as cli_module

        monkeypatch.setenv("GRAPHIFY_OUT", "custom_graph")

        graph_dir = tmp_path / "custom_graph"
        graph_dir.mkdir(parents=True)

        with patch("graphify.install._resolve_graphify_exe", return_value="graphify"):
            cli_module._launch_embedding_refresh(graph_dir)

        assert mock_popen.called
        kwargs = mock_popen.call_args.kwargs
        env = kwargs.get("env", {})
        assert env.get("GRAPHIFY_OUT") == "custom_graph", \
            f"expected GRAPHIFY_OUT='custom_graph', got {env.get('GRAPHIFY_OUT')}"

    @patch("subprocess.Popen")
    def test_cwd_is_project_root(self, mock_popen, tmp_path, monkeypatch):
        """Child cwd should be the project root (graph_dir.parent)."""
        import graphify.cli as cli_module

        monkeypatch.delenv("GRAPHIFY_OUT", raising=False)

        project_root = tmp_path / "myproject"
        graph_dir = project_root / ".graph"
        graph_dir.mkdir(parents=True)

        with patch("graphify.install._resolve_graphify_exe", return_value="graphify"):
            cli_module._launch_embedding_refresh(graph_dir)

        assert mock_popen.called
        kwargs = mock_popen.call_args.kwargs
        cwd = kwargs.get("cwd", "")
        # cwd should be project_root (graph_dir.parent)
        assert str(project_root) in str(cwd) or str(cwd) in str(project_root), \
            f"cwd should be project root, got {cwd}"
