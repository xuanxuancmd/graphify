"""Tag-vocabulary governance for AI-emitted node ``tags``.

``tags`` is a generic ``list[str]`` node field consumed by three surfaces:
``serve.py``'s string retrieval (conditional concatenation), the HTML tag
filter, and the Obsidian export. It exists for humans to quickly filter the
graph, so its value degrades directly with vocabulary divergence — one run's
``auth``, another's ``Authentication``/``authentication``, and the filter
panel fragments into noise.

Producers split into two tiers with different guarantees:

- **Deterministic extractors** (Tier 1 tool extractors like ``ddd.py`` /
  ``swagger.py``) emit closed, code-defined vocabularies — no governance
  needed.
- **Semantic extraction** (the built-in LLM prompt, custom YAML prompts, and
  cache replays of either) emits free-form tags — this module's scope.

The design mirrors graphify's "LLM picks the words, deterministic code
converges them" split, in two layers:

1. **Prompt layer (soft).** The current vocabulary is injected into the
   *user message* — never the system prompt: the semantic cache namespaces
   entries under the system-prompt fingerprint (#1939), so a per-run-evolving
   vocabulary baked into the system prompt would invalidate the entire
   semantic cache on every run. The model is told to prefer existing tags and
   mint new ones only when nothing fits.

2. **Merge layer (hard).** Every node entering the graph through the
   semantic tier — fresh extraction, custom prompt, or cache replay — is
   canonicalized against the vocabulary preloaded from ``graph.json``
   (plus this run's deterministic AST-tier tags): normalize, exact-match,
   then fuzzy-merge at ratio >= 0.9. The fuzzy pass catches *form* variants
   (case, hyphens, plurals: ``User-Service`` -> ``user_service``); true
   synonyms (``auth``/``认证``) are the prompt layer's job — deterministic
   fuzzy matching must never make semantic judgment calls like merging
   ``get``/``set``.

New tags that match nothing pass through unchanged and join the vocabulary
for the *next* run via ``graph.json`` — reuse-first with an open frontier,
not a fixed whitelist.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path

# Tags are coarse human-facing filters, not per-node metadata: three is the
# ceiling the extraction prompt asks for, enforced deterministically here.
MAX_TAGS_PER_NODE = 3
# A tag longer than a typical identifier is a description, not a filter.
MAX_TAG_LEN = 64
# Top-N vocabulary injected into the extraction prompt. The long tail is
# low-frequency and rarely reusable; 100 bounds prompt cost.
INJECTION_LIMIT = 100
# Fuzzy-merge threshold. 0.9 catches case/hyphen/plural variants
# ("user_services" vs "user_service", ratio 0.95) while leaving short
# near-neighbours ("get"/"set", ratio 0.5) untouched.
FUZZY_RATIO = 0.9
# Injection-safety: only structurally inert tags ([a-z0-9_]+, no CJK, no
# punctuation) are ever interpolated into a prompt. The vocabulary comes from
# graph.json — our own artifact, but a hostile/corrupt file must not get a
# free-form string into the user message.
_SAFE_INJECTION_RE = re.compile(r"[a-z0-9_]+")
# Whitespace and hyphens both fold to the snake_case canonical form.
_SEPARATORS_RE = re.compile(r"[\s\-]+")


def normalize_tag(raw: str) -> str | None:
    """Return the canonical form of one raw tag, or ``None`` if unusable.

    casefold + whitespace/hyphen → ``_`` + collapse/strip separators. CJK and
    other non-ASCII survive (they are legitimate filter values); the ASCII
    restriction applies only to the *injection* copy (see ``injection_list``).
    """
    folded = _SEPARATORS_RE.sub("_", raw.strip().casefold())
    folded = folded.strip("_")
    # Collapse runs of underscores left by adjacent separators ("a - b" → "a__b").
    while "__" in folded:
        folded = folded.replace("__", "_")
    if not folded or len(folded) > MAX_TAG_LEN:
        return None
    return folded


@dataclass
class TagVocabulary:
    """In-memory tag vocabulary: preload, prompt injection, and normalization.

    Lifecycle within one extract run:

    1. ``from_graph`` — preload tags from the existing ``graph.json``.
    2. ``absorb_nodes`` — fold in this run's deterministic AST-tier tags
       (``ddd``/``swagger`` extractors), so AI tags converge onto the
       deterministic vocabulary first.
    3. ``injection_list`` — the sanitized top-N list for the extraction
       prompt (user-message layer, see module docstring).
    4. ``normalize_nodes`` — canonicalize semantic-tier nodes at the merge
       point, covering fresh extraction, custom prompts, and cache replays
       uniformly. Idempotent, so replaying a normalized cache entry is safe.
    """

    counts: Counter[str] = field(default_factory=Counter)
    _canon_cache: dict[str, str] = field(default_factory=dict)
    _sorted: "list[tuple[str, int]] | None" = None

    @classmethod
    def from_graph(cls, graph_json: Path) -> "TagVocabulary":
        """Preload the vocabulary from an existing graph.json (missing → empty).

        Tolerant by design: a first run has no graph.json, and an unreadable
        or oversized one must degrade to "no vocabulary" (tags pass through
        unmerged) rather than abort extraction.
        """
        vocab = cls()
        try:
            from graphify.security import check_graph_file_size_cap
            check_graph_file_size_cap(graph_json)
            data = json.loads(graph_json.read_text(encoding="utf-8"))
            vocab.absorb_nodes(data.get("nodes", []))
        except Exception:
            pass
        return vocab

    def absorb_nodes(self, nodes: list) -> None:
        """Count tags across a node list (graph.json nodes or AST-tier nodes)."""
        for n in nodes:
            if not isinstance(n, dict):
                continue
            tags = n.get("tags")
            if not isinstance(tags, list):
                continue
            for t in tags:
                if not isinstance(t, str):
                    continue
                norm = normalize_tag(t)
                if norm is not None:
                    self.counts[norm] += 1
        self._canon_cache.clear()
        self._sorted = None

    def injection_list(self, limit: int = INJECTION_LIMIT) -> list[str]:
        """Return the prompt-safe top-N tags, most frequent first.

        Non-``[a-z0-9_]+`` entries (CJK, punctuation) are withheld from the
        injection copy only — they still participate in normalization and
        remain in graph.json.
        """
        out: list[str] = []
        for tag, _count in self._sorted_counts():
            if _SAFE_INJECTION_RE.fullmatch(tag):
                out.append(tag)
                if len(out) >= limit:
                    break
        return out

    def canonicalize(self, raw: str) -> str | None:
        """Map one raw tag onto the vocabulary: normalize → exact → fuzzy.

        Returns the canonical spelling (an existing vocabulary entry when one
        matches, else the normalized form of ``raw``), or ``None`` when the
        raw tag normalizes to nothing. Memoized per raw tag — node lists
        repeat tags heavily, so the fuzzy pass runs once per distinct tag,
        not once per node.
        """
        cached = self._canon_cache.get(raw)
        if cached is not None:
            return cached
        norm = normalize_tag(raw)
        if norm is None:
            return None
        if norm in self.counts:
            result: str | None = norm
        else:
            result = self._plural_variant(norm) or self._best_fuzzy(norm)
        self._canon_cache[raw] = result if result is not None else norm
        return result or norm

    def normalize_nodes(self, nodes: list) -> int:
        """Canonicalize ``tags`` on semantic-tier node dicts in place.

        Returns the number of nodes whose tags changed. Rules: drop non-str
        entries and non-list ``tags`` fields, canonicalize each tag, dedupe
        preserving order, cap at ``MAX_TAGS_PER_NODE``, and remove the field
        entirely when nothing survives (nodes without tags must stay
        byte-identical to a never-tagged node — see ``serve.py``'s
        conditional search-text concatenation).
        """
        changed = 0
        for n in nodes:
            if not isinstance(n, dict):
                continue
            tags = n.get("tags")
            if not isinstance(tags, list):
                if "tags" in n:
                    del n["tags"]  # malformed (str/dict/None) — not a tag list
                    changed += 1
                continue
            out: list[str] = []
            for t in tags:
                if not isinstance(t, str):
                    continue
                canon = self.canonicalize(t)
                if canon is not None and canon not in out:
                    out.append(canon)
            del out[MAX_TAGS_PER_NODE:]
            if out:
                if n.get("tags") != out:
                    n["tags"] = out
                    changed += 1
            elif "tags" in n:
                del n["tags"]
                changed += 1
        return changed

    def _sorted_counts(self) -> "list[tuple[str, int]]":
        """Vocabulary sorted by (-count, tag) — deterministic fuzzy tie-breaks."""
        if self._sorted is None:
            self._sorted = sorted(self.counts.items(), key=lambda kv: (-kv[1], kv[0]))
        return self._sorted

    def _plural_variant(self, norm: str) -> "str | None":
        """Resolve singular↔plural variants ("auths"↔"auth", "processes"↔"process").

        SequenceMatcher's ratio drops below FUZZY_RATIO for short plurals
        ("auths"/"auth" = 0.89), yet a trailing-s divergence is the most
        common AI tag variant. An explicit stem rule catches it without
        lowering the threshold — which would let "auth"/"author" (0.8) merge.
        """
        if norm.endswith("s") and not norm.endswith("ss"):
            stems = [norm[:-1]]
            if norm.endswith("es"):
                stems.append(norm[:-2])
            for stem in stems:
                if stem in self.counts:
                    return stem
        plural = norm + "s"
        if plural in self.counts:
            return plural
        return None

    def _best_fuzzy(self, norm: str) -> "str | None":
        """Best vocabulary entry at ratio >= FUZZY_RATIO, or None.

        Candidates walk the (-count, tag) ordering, so a ratio tie resolves
        to the more frequent (then lexicographically smaller) tag — the same
        deterministic preference a human curator would apply.
        """
        best: str | None = None
        best_ratio = FUZZY_RATIO
        for cand, _count in self._sorted_counts():
            # ratio <= 2*min(len)/(len+other) — beyond this gap 0.9 is
            # unreachable, and skipping saves a SequenceMatcher call.
            if abs(len(cand) - len(norm)) > 4:
                continue
            ratio = SequenceMatcher(None, norm, cand).ratio()
            if ratio > best_ratio:
                best, best_ratio = cand, ratio
        return best

    def __len__(self) -> int:
        return len(self.counts)
