"""Fuzzy string matching tier for hybrid search.

Uses rapidfuzz (already a dependency) for Jaro-Winkler similarity. Triggered
only when the lexical 3-tier (exact/prefix/substring) misses on a per-token
basis, so it never interferes with precise queries.

The threshold (0.85) is set just above the JaroWinkler score a typical
single-character transposition produces (e.g. ``UserServise`` vs.
``UserService`` ≈ 0.93), so genuine typos fire and unrelated labels stay out.
"""
from __future__ import annotations

try:
    from rapidfuzz.distance import JaroWinkler
except ImportError:  # pragma: no cover - rapidfuzz is a hard dep, this only fires in unusual environments
    JaroWinkler = None  # type: ignore[assignment]

FUZZY_THRESHOLD = 0.85  # Only match if similarity >= 0.85


def fuzzy_score(query_token: str, label: str) -> float:
    """Jaro-Winkler similarity in [0, 1]. Returns 0 if below threshold.

    Comparison is case-insensitive (both sides lower-cased) because case is
    incidental to identifier spelling, not a semantic signal here. Returns 0
    for empty inputs so the caller's ``if fuzzy_bonus > 0`` gate stays simple.
    """
    if not query_token or not label:
        return 0.0
    if JaroWinkler is None:
        return 0.0
    sim = JaroWinkler.similarity(query_token.lower(), label.lower())
    return float(sim) if sim >= FUZZY_THRESHOLD else 0.0


def fuzzy_best_match(query_token: str, labels: list[str]) -> tuple[float, str | None]:
    """Find the best fuzzy match for query_token among labels.

    Returns ``(score, best_label)`` or ``(0.0, None)`` when no label clears
    the threshold. Used by tests; the live scorer path calls ``fuzzy_score``
    directly per (token, node_label) pair to avoid materialising the full
    label list.
    """
    best_score = 0.0
    best_label: str | None = None
    for label in labels:
        score = fuzzy_score(query_token, label)
        if score > best_score:
            best_score = score
            best_label = label
    return best_score, best_label
