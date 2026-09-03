"""Evaluation Agent — post-extraction confidence scoring for INFERRED items.

Runs after build_from_json completes. Evaluates all INFERRED edges and nodes
using an LLM agent that outputs discrete three-tier scores:

  - 0.95: Agent is confident the item is CORRECT
  - 0.50: Agent cannot determine correctness (honest uncertainty)
  - 0.05: Agent is confident the item is WRONG

EXTRACTED items (AST-extracted, score=1.0) and AMBIGUOUS items (tool multi-match,
score=0.2-0.3) are NOT evaluated — their scores are deterministic and fixed.

The agent receives an evidence packet collected by heuristic rules (Python,
free, no LLM) for each item, then makes a semantic judgment the rules cannot.
The heuristic rules only COLLECT evidence; they never assign scores.

Evidence collected (each has a clear causal rationale, no circular reasoning):
  - has_ast_corroboration: An AST-extracted edge already connects the same pair
  - is_self_loop: The edge connects a node to itself (suspicious)
  - source_mentions_target: Source file text contains the target's name
  - type_compatible: Node types match the relation (class→inherits→class)
  - llm_self_reported_score: The LLM's own confidence when it extracted this
  - node_verification: Whether the node's symbol was found in source text

Graceful degradation: if no LLM backend is configured, evaluation is skipped
and INFERRED items keep their default scores (0.55 or LLM self-reported).
"""
from __future__ import annotations

import json
import logging
from typing import Any

import networkx as nx

_LOG = logging.getLogger(__name__)

# Discrete score tiers — the Agent must output one of these, never anything
# in between. This prevents scores from clustering near the review threshold
# (0.8), where "reliable vs unreliable" is indistinguishable.
SCORE_CORRECT = 0.95
SCORE_UNCERTAIN = 0.50
SCORE_WRONG = 0.05
_VALID_SCORES = frozenset({SCORE_CORRECT, SCORE_UNCERTAIN, SCORE_WRONG})

# Batch size: items per LLM call. ~20 items keeps the prompt compact while
# amortizing the per-call overhead.
_BATCH_SIZE = 20

# Default confidence_score for INFERRED items before evaluation runs.
_INFERRED_DEFAULT_SCORE = 0.55


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def evaluate_graph(
    G: nx.Graph,
    *,
    backend: str | None = None,
    skip: bool = False,
) -> dict[str, int]:
    """Evaluate all INFERRED edges and nodes in *G* using an LLM agent.

    Modifies the graph in place: sets ``confidence_score``, ``evaluated``,
    and ``evaluation_reason`` on each evaluated item.

    Args:
        G: The NetworkX graph produced by build_from_json.
        backend: LLM backend name. If None, auto-detects via llm.detect_backend().
        skip: If True, skip evaluation entirely (e.g. --skip-evaluate flag).

    Returns:
        Stats dict: {edges_evaluated, nodes_evaluated, high, uncertain, low,
                     llm_calls, skipped}.
    """
    stats = {
        "edges_evaluated": 0, "nodes_evaluated": 0,
        "high": 0, "uncertain": 0, "low": 0,
        "llm_calls": 0, "skipped": 0,
    }

    if skip:
        _LOG.info("evaluate_graph: skipped (--skip-evaluate)")
        stats["skipped"] = 1
        return stats

    # Late import to avoid circular dependency (llm.py is heavy).
    from graphify.llm import detect_backend, _call_llm

    if backend is None:
        backend = detect_backend()
    if backend is None:
        _LOG.info("evaluate_graph: no LLM backend configured, skipping")
        stats["skipped"] = 1
        return stats

    # 1. Collect all INFERRED items (edges + nodes)
    items = _collect_items(G)
    if not items:
        _LOG.info("evaluate_graph: no INFERRED items to evaluate")
        return stats

    # 2. Batch and evaluate
    batches = _batch_items(items, _BATCH_SIZE)
    _LOG.info(
        "evaluate_graph: %d items in %d batches (backend=%s)",
        len(items), len(batches), backend,
    )

    for batch in batches:
        prompt = _build_prompt(batch)
        try:
            response = _call_llm(prompt, backend=backend, max_tokens=4000)
        except Exception as exc:
            _LOG.warning("evaluate_graph: LLM call failed: %s", exc)
            continue

        results = _parse_response(response)
        stats["llm_calls"] += 1

        for r in results:
            delta = _apply_score(G, r)
            for k, v in delta.items():
                stats[k] = stats.get(k, 0) + v

    return stats


def stamp_node_confidence(G: nx.Graph) -> None:
    """Set confidence fields on nodes based on _origin.

    Call this after build_from_json, BEFORE evaluate_graph, so that:
      - AST nodes get confidence="EXTRACTED", score=1.0
      - Semantic/LLM nodes get confidence="INFERRED", score=0.55 (default)
      - Nodes with verification="unverified" get score lowered to 0.2

    This mirrors what extract.py already does for edges, but for nodes
    (which currently lack confidence fields entirely — see llm.py:657).
    """
    for nid, data in G.nodes(data=True):
        if not isinstance(data, dict):
            continue
        # Don't overwrite an explicit confidence set by an extractor.
        if data.get("confidence") is None:
            origin = data.get("_origin", "semantic")
            if origin == "ast":
                data.setdefault("confidence", "EXTRACTED")
                data.setdefault("confidence_score", 1.0)
            else:
                data.setdefault("confidence", "INFERRED")
                data.setdefault("confidence_score", _INFERRED_DEFAULT_SCORE)
        # An unverified node (symbol not found in source) is inherently
        # low-confidence regardless of origin.
        if data.get("verification") == "unverified":
            data["confidence_score"] = min(
                float(data.get("confidence_score", 1.0)), 0.2
            )


# ---------------------------------------------------------------------------
# Item collection (edges + nodes)
# ---------------------------------------------------------------------------

def _collect_items(G: nx.Graph) -> list[dict]:
    """Collect all INFERRED edges and nodes that need Agent evaluation."""
    items: list[dict] = []

    # Edges
    for u, v, data in G.edges(data=True):
        conf = data.get("confidence", "EXTRACTED")
        if conf != "INFERRED":
            continue  # EXTRACTED (1.0) and AMBIGUOUS (0.2) are deterministic
        edge_id = f"edge::{u}|{v}|{data.get('relation', '')}"
        evidence = _collect_edge_evidence(G, u, v, data)
        items.append({
            "id": edge_id,
            "kind": "edge",
            "source": u,
            "target": v,
            "relation": data.get("relation", ""),
            "source_label": _node_label(G, u),
            "target_label": _node_label(G, v),
            "source_file": data.get("source_file", ""),
            "evidence": evidence,
        })

    # Nodes
    for nid, data in G.nodes(data=True):
        if not isinstance(data, dict):
            continue
        conf = data.get("confidence")
        if conf != "INFERRED":
            continue  # Only evaluate INFERRED (semantic/LLM) nodes
        evidence = _collect_node_evidence(G, nid, data)
        items.append({
            "id": f"node::{nid}",
            "kind": "node",
            "label": data.get("label", nid),
            "file_type": data.get("file_type", ""),
            "source_file": data.get("source_file", ""),
            "evidence": evidence,
        })

    return items


def _collect_edge_evidence(G: nx.Graph, u: str, v: str, data: dict) -> dict:
    """Collect heuristic evidence for an edge (Python, no LLM).

    Each field has a clear causal rationale — no circular reasoning.
    """
    u_data = G.nodes.get(u, {}) or {}
    v_data = G.nodes.get(v, {}) or {}

    return {
        # --- Source reliability ---
        "source_origin": data.get("_origin", "unknown"),
        "llm_self_reported_score": data.get("confidence_score"),
        "confidence_label": data.get("confidence", "INFERRED"),

        # --- Type compatibility ---
        # class→inherits→class is valid; class→inherits→function is not.
        "source_file_type": u_data.get("file_type", ""),
        "target_file_type": v_data.get("file_type", ""),
        "source_node_kind": u_data.get("node_kind", ""),
        "target_node_kind": v_data.get("node_kind", ""),
        "relation": data.get("relation", ""),

        # --- AST corroboration ---
        # An AST-extracted edge already connecting the same pair is ground
        # truth — strong support for the INFERRED edge.
        "has_ast_corroboration": _has_ast_edge(G, u, v),

        # --- Self-reference ---
        # A→calls→A is suspicious: functions rarely call themselves in the
        # structural sense that graphify extracts (recursion is a different
        # relation and is usually EXTRACTED by the AST pass).
        "is_self_loop": u == v,

        # --- Textual evidence ---
        # The source file's text contains the target's name — textual
        # evidence that the relationship exists in the source material.
        "source_mentions_target": _source_mentions_target(G, u_data, v_data),

        # --- Node verification status ---
        # A node whose symbol was not found in its source file (verification
        # = "unverified") is a fabrication risk.
        "source_verified": u_data.get("verification", "verified"),
        "target_verified": v_data.get("verification", "verified"),
    }


def _collect_node_evidence(G: nx.Graph, nid: str, data: dict) -> dict:
    """Collect heuristic evidence for a node (Python, no LLM)."""
    return {
        # --- Source reliability ---
        "origin": data.get("_origin", "unknown"),
        "llm_self_reported_score": data.get("confidence_score"),

        # --- Verification ---
        # verification="unverified" means the node's label symbol was not
        # found in the source file text — a fabrication signal.
        "verification": data.get("verification", "verified"),

        # --- Structural signals ---
        "file_type": data.get("file_type", ""),
        "has_source_file": bool(data.get("source_file")),
        "degree": G.degree(nid) if nid in G else 0,

        # --- All edge confidences touching this node ---
        "edge_confidences": [
            d.get("confidence", "EXTRACTED")
            for _, _, d in G.edges(nid, data=True)
        ] if nid in G else [],
    }


# ---------------------------------------------------------------------------
# Heuristic evidence helpers (Python, no LLM)
# ---------------------------------------------------------------------------

def _has_ast_edge(G: nx.Graph, u: str, v: str) -> bool:
    """True if an EXTRACTED edge already connects u and v (AST ground truth).

    In a plain ``nx.Graph`` (not MultiGraph), parallel edges are collapsed,
    so an INFERRED edge between (u, v) cannot have a separate EXTRACTED edge
    between the same pair. This heuristic fires only when the SAME edge that
    connects the pair is EXTRACTED — which means it's primarily useful when
    called on edges that haven't been filtered to INFERRED yet, or in future
    MultiGraph contexts. It's still collected as evidence so the Agent has the
    full picture.
    """
    if u not in G or v not in G:
        return False
    if G.has_edge(u, v):
        ed = G.edges[u, v]
        if ed.get("confidence", "EXTRACTED") == "EXTRACTED":
            return True
    return False


def _source_mentions_target(
    G: nx.Graph, u_data: dict, v_data: dict
) -> bool | None:
    """True if the source file of u mentions the target node's label.

    Returns None when the check can't be performed (no source file, or the
    file can't be read). The Agent treats None as "no evidence either way".
    """
    import os
    source_file = u_data.get("source_file", "")
    target_label = v_data.get("label", "")
    if not source_file or not target_label:
        return None
    # Only check identifiers of reasonable length to avoid false positives
    # from short labels matching substrings.
    if len(target_label) < 3:
        return None
    try:
        if not os.path.isfile(source_file):
            return None
        with open(source_file, "r", encoding="utf-8", errors="replace") as fh:
            content = fh.read(65536)  # cap at 64KB for perf
        return target_label.lower() in content.lower()
    except Exception:
        return None


def _node_label(G: nx.Graph, nid: str) -> str:
    """Safely get a node's label."""
    data = G.nodes.get(nid, {})
    return (data or {}).get("label", nid) if isinstance(data, dict) else nid


# ---------------------------------------------------------------------------
# Batching
# ---------------------------------------------------------------------------

def _batch_items(items: list[dict], batch_size: int) -> list[list[dict]]:
    """Split items into batches of *batch_size*."""
    if batch_size < 1:
        batch_size = 1
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]


# ---------------------------------------------------------------------------
# LLM prompt construction
# ---------------------------------------------------------------------------

_EVALUATION_SYSTEM = """\
You are a graphify evaluation agent. You receive a batch of extracted graph items
(nodes and edges) with evidence collected by heuristic rules. Your job is to
evaluate each item's correctness and assign a confidence score.

Output ONLY valid JSON — no explanation, no markdown fences, no preamble.

Scoring rules (DISCRETE three tiers, NEVER use values in between):
- 0.95: You are confident this item is CORRECT. Evidence strongly supports it.
- 0.50: You CANNOT determine correctness. Evidence is insufficient or contradictory.
- 0.05: You are confident this item is WRONG. Evidence contradicts it or it is
        clearly a fabrication/mismatch.

NEVER output 0.7, 0.8, or any value near the 0.8 review threshold. Either you
know (0.95/0.05) or you don't (0.50).

Evidence fields (for edges):
- has_ast_corroboration: An AST-extracted edge already connects the same pair — strong support
- is_self_loop: The edge connects a node to itself — suspicious
- source_mentions_target: The source file text contains the target's name — textual support
- source_node_kind/target_node_kind: The AST kind (class, function, file, etc.)
- relation: calls, imports, inherits, references, semantically_similar_to, etc.
- llm_self_reported_score: The LLM's own confidence when it extracted this — reference, but calibrate (LLMs tend to be overconfident)
- source_verified/target_verified: "verified" = symbol found in source, "unverified" = not found (fabrication risk)

Evidence fields (for nodes):
- verification: "verified" = symbol found in source file, "unverified" = not found
- origin: "ast" = tree-sitter extracted, "semantic" = LLM extracted
- degree: number of edges touching this node
- edge_confidences: list of confidence labels on this node's edges

For each item, output:
{"id": "<item_id>", "score": 0.95|0.50|0.05, "reason": "<one sentence>"}

Output a JSON array of these objects.
"""


def _build_prompt(batch: list[dict]) -> str:
    """Build the LLM evaluation prompt for a batch of items."""
    # Strip down to the essentials the Agent needs — don't send the full
    # evidence dict if some fields are None.
    items_json = []
    for item in batch:
        compact = {
            "id": item["id"],
            "kind": item["kind"],
        }
        if item["kind"] == "edge":
            compact["source"] = item.get("source_label", item["source"])
            compact["target"] = item.get("target_label", item["target"])
            compact["relation"] = item["relation"]
        else:
            compact["label"] = item["label"]
            compact["file_type"] = item["file_type"]
        # Only include non-None evidence
        compact["evidence"] = {
            k: v for k, v in item.get("evidence", {}).items()
            if v is not None and v != "" and v != []
        }
        items_json.append(compact)

    return _EVALUATION_SYSTEM + "\nItems to evaluate:\n" + json.dumps(
        items_json, ensure_ascii=False, indent=2
    )


# ---------------------------------------------------------------------------
# LLM response parsing
# ---------------------------------------------------------------------------

def _parse_response(response: str) -> list[dict]:
    """Parse the LLM's JSON response into a list of {id, score, reason}.

    Tolerates:
    - Extra text before/after the JSON array
    - JSON wrapped in markdown fences (```json ... ```)
    - Scores that are close to but not exactly the tier values (clamped)
    """
    if not response or not response.strip():
        return []

    text = response.strip()

    # Strip markdown fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first line (```json or ```) and last line (```)
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    # Find the JSON array boundaries
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        _LOG.warning("evaluate: no JSON array found in response: %s", text[:200])
        return []

    json_str = text[start:end + 1]
    try:
        results = json.loads(json_str)
    except json.JSONDecodeError as exc:
        _LOG.warning("evaluate: JSON parse error: %s", exc)
        return []

    if not isinstance(results, list):
        return []

    # Clamp scores to the nearest valid tier
    parsed = []
    for r in results:
        if not isinstance(r, dict):
            continue
        item_id = r.get("id")
        score = r.get("score")
        reason = r.get("reason", "")
        if item_id is None or score is None:
            continue
        # Clamp to nearest tier
        score = _clamp_to_tier(float(score))
        parsed.append({"id": str(item_id), "score": score, "reason": str(reason)})

    return parsed


def _clamp_to_tier(score: float) -> float:
    """Clamp a score to the nearest valid tier (0.95, 0.50, 0.05)."""
    if score in _VALID_SCORES:
        return score
    # Find nearest tier
    tiers = sorted(_VALID_SCORES, key=lambda t: abs(t - score))
    return tiers[0]


# ---------------------------------------------------------------------------
# Score application
# ---------------------------------------------------------------------------

def _apply_score(G: nx.Graph, result: dict) -> dict:
    """Apply an evaluation result back to the graph.

    Returns a stats delta dict with counters (0 or 1) that the caller
    accumulates into the running totals.
    """
    item_id = result["id"]
    score = result["score"]
    reason = result["reason"]

    delta = {"high": 0, "uncertain": 0, "low": 0,
             "edges_evaluated": 0, "nodes_evaluated": 0}

    if item_id.startswith("edge::"):
        # Format: edge::<source>|<target>|<relation>
        rest = item_id[len("edge::"):]
        parts = rest.split("|")
        if len(parts) < 3:
            return delta
        u, v, relation = parts[0], parts[1], "|".join(parts[2:])
        if not G.has_edge(u, v):
            return delta
        ed = G.edges[u, v]
        ed["confidence_score"] = score
        ed["evaluated"] = True
        ed["evaluation_reason"] = reason
        delta["edges_evaluated"] = 1
    elif item_id.startswith("node::"):
        nid = item_id[len("node::"):]
        if nid not in G:
            return delta
        nd = G.nodes[nid]
        if not isinstance(nd, dict):
            return delta
        nd["confidence_score"] = score
        nd["evaluated"] = True
        nd["evaluation_reason"] = reason
        delta["nodes_evaluated"] = 1
    else:
        return delta

    # Track score distribution
    if score >= SCORE_CORRECT:
        delta["high"] = 1
    elif score <= SCORE_WRONG:
        delta["low"] = 1
    else:
        delta["uncertain"] = 1

    return delta
