"""Benchmark: pure-lexical vs hybrid retrieval recall.

Loads tests/fixtures/search_benchmark/graph.json + queries.json and runs each
query under two modes:
  - pure lexical (semantic=False)
  - hybrid (semantic=True, with fuzzy tier; vector tier skipped when no
    embedding sidecar/API key is configured)

Prints recall@5 for each mode and a side-by-side comparison. The hybrid mode
should match or exceed pure lexical on every query (AC5).

Run:
    python tests/fixtures/search_benchmark/run_benchmark.py

When an embedding API key is configured (OPENAI_API_KEY etc.) AND an
embeddings sidecar exists at tests/fixtures/search_benchmark/embeddings/,
the vector tier is also exercised. Without those, the hybrid mode only gets
the fuzzy tier — still useful for catching typos (UserServise -> UserService)
and word-form variants, but the "login -> AuthService" rescue case (which
needs real semantic similarity) will not be exercised.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import networkx as nx
from networkx.readwrite import json_graph

# Allow `python tests/fixtures/search_benchmark/run_benchmark.py` from repo root.
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from graphify.serve import _score_query  # noqa: E402

FIXTURE_DIR = Path(__file__).parent
GRAPH_JSON = FIXTURE_DIR / "graph.json"
QUERIES_JSON = FIXTURE_DIR / "queries.json"
EMBEDDINGS_DIR = FIXTURE_DIR / "embeddings"

TOP_K = 5  # recall@5 — matches the spec's "graphify query --top-k 5" example


def _load_graph() -> nx.Graph:
    raw = json.loads(GRAPH_JSON.read_text(encoding="utf-8"))
    if "links" not in raw and "edges" in raw:
        raw = dict(raw, links=raw["edges"])
    # Mirror cli.py's _src/_tgt stamping so direction is preserved per-edge.
    raw = dict(
        raw,
        links=[
            {
                **link,
                "_src": link.get("_src", link.get("source")),
                "_tgt": link.get("_tgt", link.get("target")),
            }
            for link in raw.get("links", [])
        ],
    )
    try:
        G = json_graph.node_link_graph(raw, edges="links")
    except TypeError:
        G = json_graph.node_link_graph(raw)
    return G


def _load_queries() -> list[dict]:
    return json.loads(QUERIES_JSON.read_text(encoding="utf-8"))


def _run_mode(G: nx.Graph, queries: list[dict], *, semantic: bool) -> tuple[int, int, list[tuple[str, bool, bool]]]:
    """Return (hits, total, per_query (query, lexical_hit, hybrid_hit))."""
    # Try to attach a hybrid scorer so the vector tier fires when an
    # embeddings sidecar + API key are present. Cheap no-op otherwise.
    if semantic:
        try:
            from graphify.hybrid_scorer import HybridScorer
            if "_hybrid_scorer" not in G.graph:
                G.graph["_hybrid_scorer"] = HybridScorer(FIXTURE_DIR)
        except Exception:
            pass

    hits = 0
    per_query: list[tuple[str, bool, bool]] = []
    for entry in queries:
        query = entry["query"]
        expected = set(entry["expected"])
        # Build query embedding scores if a scorer is available.
        query_emb_scores = None
        if semantic:
            scorer = G.graph.get("_hybrid_scorer")
            if scorer is not None and scorer.available:
                query_emb_scores = scorer.vector_scores(query)
        # Tokenize the same way _query_graph_text does.
        from graphify.serve import _query_terms
        terms = _query_terms(query)
        hybrid_scorer = G.graph.get("_hybrid_scorer") if semantic else None
        qs = _score_query(
            G, terms,
            collect_per_term_seeds=False,
            query_embedding_scores=query_emb_scores,
            hybrid_scorer=hybrid_scorer,
            semantic=semantic,
        )
        top_k_ids = {nid for _score, nid in qs.ranked[:TOP_K]}
        hit = bool(expected & top_k_ids)
        if hit:
            hits += 1
        per_query.append((query, not semantic, hit))
    return hits, len(queries), per_query


def main() -> int:
    G = _load_graph()
    queries = _load_queries()

    lex_hits, total, _ = _run_mode(G, queries, semantic=False)
    # Re-attach a fresh scorer for the hybrid run (the lexical run above
    # intentionally didn't attach one because semantic=False).
    G.graph.pop("_hybrid_scorer", None)
    hyb_hits, _, per_query = _run_mode(G, queries, semantic=True)

    lex_recall = lex_hits / total if total else 0.0
    hyb_recall = hyb_hits / total if total else 0.0

    sidecar_present = (EMBEDDINGS_DIR / "text_embedding_3_small.npy").is_file() or any(EMBEDDINGS_DIR.glob("*.npy")) if EMBEDDINGS_DIR.is_dir() else False
    print(f"Mode: {'hybrid (vector+fuzzy)' if sidecar_present else 'hybrid (fuzzy only — no embeddings sidecar)'}")
    print(f"Pure lexical recall@{TOP_K}: {lex_hits}/{total} = {lex_recall:.1%}")
    print(f"Hybrid        recall@{TOP_K}: {hyb_hits}/{total} = {hyb_recall:.1%}")
    print()
    print("Per-query (✓=hit, ✗=miss):")
    for query, is_lex, is_hit in per_query:
        marker = "✓" if is_hit else "✗"
        print(f"  [{marker}] {query}")
    print()
    # AC5: hybrid recall should be >= pure lexical. (Strictly > is the goal,
    # but >= is the floor — fuzzy can only help, never hurt, because it only
    # fires when all 3 lexical tiers missed.)
    if hyb_recall >= lex_recall:
        print(f"PASS: hybrid recall ({hyb_recall:.1%}) >= pure lexical ({lex_recall:.1%})")
        return 0
    else:
        print(f"FAIL: hybrid recall ({hyb_recall:.1%}) < pure lexical ({lex_recall:.1%})")
        return 1


if __name__ == "__main__":
    sys.exit(main())
