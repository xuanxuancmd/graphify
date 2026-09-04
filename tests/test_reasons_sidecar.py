"""Tests for the audit reasons sidecar (graph.json stays explanation-free).

Extraction-time `reason` / `evidence_quote` fields are audit provenance: they
must be stripped from graph.json (MR-visible data) and persisted to the
temp/reasons.json sidecar instead. The sidecar must carry forward reasons for
edges preserved from a previous build and evict entries whose edge is gone,
because an incremental rebuild loads semantic edges from an already-stripped
graph.json.
"""
import json

from graphify.build import build_from_json
from graphify.export import to_json
from graphify.exporters.html import to_html

_REASON = "Both validate user input the same way"
_QUOTE = "def validate(user): return user is not None"
_EDGE_KEY = "a|b|semantically_similar_to"


def _extraction() -> dict:
    return {
        "nodes": [
            {"id": "a", "label": "A", "file_type": "code", "source_file": "a.py"},
            {"id": "b", "label": "B", "file_type": "code", "source_file": "b.py"},
        ],
        "edges": [
            {
                "source": "a", "target": "b", "relation": "semantically_similar_to",
                "confidence": "INFERRED", "confidence_score": 0.75,
                "source_file": "a.py", "weight": 1.0,
                "reason": _REASON, "evidence_quote": _QUOTE,
            },
        ],
        "input_tokens": 0, "output_tokens": 0,
    }


def test_to_json_strips_reason_into_sidecar(tmp_path):
    """graph.json links must not carry reason/evidence_quote; the sidecar must."""
    G = build_from_json(_extraction())
    out = tmp_path / "graph.json"
    assert to_json(G, {0: ["a", "b"]}, str(out)) is True

    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["links"], "no links written"
    for link in data["links"]:
        assert "reason" not in link, f"reason leaked into graph.json: {link}"
        assert "evidence_quote" not in link, f"quote leaked into graph.json: {link}"

    sidecar = tmp_path / "temp" / "reasons.json"
    assert sidecar.exists(), "reasons sidecar not written"
    sc = json.loads(sidecar.read_text(encoding="utf-8"))
    assert sc["schema_version"] == 1
    assert sc["edges"][_EDGE_KEY]["reason"] == _REASON
    assert sc["edges"][_EDGE_KEY]["evidence_quote"] == _QUOTE


def test_sidecar_carries_forward_when_rebuilt_from_clean_graph(tmp_path):
    """An incremental rebuild reloads stripped edges from graph.json — the
    sidecar merge must keep their reasons instead of dropping them."""
    G = build_from_json(_extraction())
    out = tmp_path / "graph.json"
    to_json(G, {0: ["a", "b"]}, str(out))

    # Simulate the reload: build from the on-disk (stripped) graph.json.
    reloaded = json.loads(out.read_text(encoding="utf-8"))
    G2 = build_from_json(reloaded)
    to_json(G2, {0: ["a", "b"]}, str(out))

    sc = json.loads((tmp_path / "temp" / "reasons.json").read_text(encoding="utf-8"))
    assert sc["edges"][_EDGE_KEY]["reason"] == _REASON, (
        "carry-forward lost the reason of a preserved edge"
    )


def test_sidecar_evicts_deleted_edges(tmp_path):
    """When the edge no longer exists, its sidecar entry must be pruned."""
    G = build_from_json(_extraction())
    out = tmp_path / "graph.json"
    to_json(G, {0: ["a", "b"]}, str(out))
    sidecar = tmp_path / "temp" / "reasons.json"
    assert sidecar.exists()

    # Rebuild WITHOUT the edge (nodes unchanged, so no shrink-refusal).
    gone = {
        "nodes": _extraction()["nodes"],
        "edges": [],
        "input_tokens": 0, "output_tokens": 0,
    }
    G2 = build_from_json(gone)
    assert to_json(G2, {0: ["a", "b"]}, str(out)) is True
    assert not sidecar.exists(), "stale sidecar entry survived its edge"


def _no_llm(monkeypatch):
    """Keep to_html's project-description fallback from making real LLM calls."""
    import graphify.llm as llm_mod
    monkeypatch.setattr(llm_mod, "detect_backend", lambda: None)
    monkeypatch.setattr(llm_mod, "_call_llm", lambda *a, **k: "")


def test_to_html_embeds_reason_from_graph_attrs(tmp_path, monkeypatch):
    _no_llm(monkeypatch)
    G = build_from_json(_extraction())
    html_path = tmp_path / "graph.html"
    assert to_html(G, {0: ["a", "b"]}, str(html_path)) is True
    html = html_path.read_text(encoding="utf-8")
    # Extraction provenance reaches the audit UI.
    assert _REASON in html, "edge reason missing from embedded data"
    assert _QUOTE in html, "evidence quote missing from embedded data"
    # Edge audit parity: the edge detail entry point exists.
    assert "function showEdgeInfo" in html
    # Review queue items carry edge identity for click-through.
    assert '"edge"' in html or "'edge'" in html
    # The wrap fix for the source-file truncation bug.
    assert "word-break:break-all" in html


def test_to_html_falls_back_to_sidecar(tmp_path, monkeypatch):
    """`graphify export html` rebuilds G from a stripped graph.json — the
    sidecar next to it must re-attach the reasons."""
    _no_llm(monkeypatch)
    G = build_from_json(_extraction())
    out = tmp_path / "graph.json"
    to_json(G, {0: ["a", "b"]}, str(out))

    reloaded = json.loads(out.read_text(encoding="utf-8"))
    G2 = build_from_json(reloaded)  # attrs stripped; sidecar must fill in
    html_path = tmp_path / "graph.html"
    assert to_html(G2, {0: ["a", "b"]}, str(html_path)) is True
    html = html_path.read_text(encoding="utf-8")
    assert _REASON in html, "sidecar fallback did not re-attach the reason"
    assert _QUOTE in html, "sidecar fallback did not re-attach the quote"
