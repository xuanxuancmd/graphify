# generate GRAPH_REPORT.md - the human-readable audit trail
from __future__ import annotations
import re
from datetime import date
from pathlib import Path
import networkx as nx


def _portable_root_label(root: str) -> str:
    """Portable label for the report header — the project directory basename.

    GRAPH_REPORT.md is a tracked artifact in practice, so its header must not
    bake the generator host's absolute path into the file: the same graph would
    otherwise produce different bytes on different machines and leak the build
    machine's directory layout into git history (#2628, same class as #2598).

    Taking the basename strips any leading absolute path without touching the
    filesystem, and makes `graphify update .`, `graphify update ./proj`, and
    `graphify update /abs/path/proj` all label the header `proj`. Only the
    degenerate `.`/``/`..` cases need a cwd resolve to recover the real name;
    if even that fails, fall back to the raw value.
    """
    raw = str(root).replace("\\", "/")
    name = Path(raw).name
    if name in ("", ".", ".."):
        try:
            name = Path(raw).resolve().name
        except (OSError, RuntimeError):
            name = ""
    return name or raw


def _safe_community_name(label: str) -> str:
    """Mirrors export.safe_name so community hub filenames and report wikilinks always agree."""
    cleaned = re.sub(r'[\\/*?:"<>|#^[\]]', "", label.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")).strip()
    cleaned = re.sub(r"\.(md|mdx|markdown)$", "", cleaned, flags=re.IGNORECASE)
    return cleaned or "unnamed"


def load_learning_for_report(graph_path) -> dict | None:
    """Assemble the report's work-memory inputs from sibling artifacts.

    Reads the ``.graphify_learning.json`` overlay (preferred sources) next to
    ``graph_path`` and re-aggregates the memory docs for the query-scoped
    dead-ends. Best-effort: returns None if neither is available, so the report
    simply omits the section. Never raises.
    """
    from pathlib import Path as _Path
    try:
        gp = _Path(graph_path)
        from graphify.reflect import load_learning_overlay, load_memory_docs, aggregate_lessons
        overlay = load_learning_overlay(gp)
        dead_ends: list[dict] = []
        mem = gp.parent / "memory"
        if mem.is_dir():
            agg = aggregate_lessons(load_memory_docs(mem))
            dead_ends = agg.get("dead_ends", [])
        if not overlay and not dead_ends:
            return None
        return {"overlay": overlay, "dead_ends": dead_ends}
    except Exception:
        return None


def _learning_section(lines: list, learning: dict | None, top_n: int = 10) -> None:
    """Append the ``## Work-memory lessons`` section, or nothing when empty."""
    if not learning:
        return
    overlay = learning.get("overlay") or {}
    dead_ends = learning.get("dead_ends") or []
    preferred = [
        (nid, e) for nid, e in overlay.items()
        if isinstance(e, dict) and e.get("status") == "preferred"
    ]
    # Most-corroborated first (uses desc), then by score, then id for stability.
    preferred.sort(key=lambda kv: (-kv[1].get("uses", 0),
                                   -float(kv[1].get("score", 0) or 0), kv[0]))
    if not preferred and not dead_ends:
        return
    lines += ["", "## 工作记忆经验"]
    if preferred:
        lines += ["", "**首选来源** —— 已被过往会话印证；从这里开始查。"]
        for nid, e in preferred[:top_n]:
            label = e.get("label") or nid
            stale = " _（代码已变更——需重新验证）_" if e.get("stale") else ""
            lines.append(f"- `{label}`（{e.get('uses', 0)}× 有用，"
                         f"score={e.get('score', 0)}){stale}")
    if dead_ends:
        lines += ["", "**已知死胡同** —— 这些问题查不出结果；别再重复推导。"]
        for d in dead_ends:
            nodes = ", ".join(f"`{n}`" for n in d.get("nodes", []))
            lines.append(f"- \"{d.get('question', '')}\""
                         + (f" -> {nodes}" if nodes else ""))


def generate(
    G: nx.Graph,
    communities: dict[int, list[str]],
    cohesion_scores: dict[int, float],
    community_labels: dict[int, str],
    god_node_list: list[dict],
    surprise_list: list[dict],
    detection_result: dict,
    token_cost: dict,
    root: str,
    suggested_questions: list[dict] | None = None,
    min_community_size: int = 3,
    built_at_commit: str | None = None,
    learning: dict | None = None,
    obsidian: bool = False,
) -> str:
    today = date.today().isoformat()

    # JSON deserialization produces string keys; normalize to int so .get(cid) works.
    if community_labels:
        community_labels = {int(k) if isinstance(k, str) else k: v for k, v in community_labels.items()}

    confidences = [d.get("confidence", "EXTRACTED") for _, _, d in G.edges(data=True)]
    total = len(confidences) or 1
    ext_pct = round(confidences.count("EXTRACTED") / total * 100)
    inf_pct = round(confidences.count("INFERRED") / total * 100)
    amb_pct = round(confidences.count("AMBIGUOUS") / total * 100)

    inf_edges = [(u, v, d) for u, v, d in G.edges(data=True) if d.get("confidence") == "INFERRED"]
    inf_scores = [d.get("confidence_score", 0.5) for _, _, d in inf_edges]
    inf_avg = round(sum(inf_scores) / len(inf_scores), 2) if inf_scores else None

    lines = [
        f"# 图谱报告 - {_portable_root_label(root)}  ({today})",
        "",
        "## 语料检查",
    ]
    if detection_result.get("warning"):
        lines.append(f"- {detection_result['warning']}")
    else:
        lines += [
            f"- {detection_result['total_files']} 个文件 · 约 {detection_result['total_words']:,} 词",
            "- 判定：语料规模足够大，图结构能带来价值。",
        ]

    from .analyze import _is_file_node as _ifn
    non_empty = {cid: nodes for cid, nodes in communities.items()
                 if any(not _ifn(G, n) for n in nodes)}
    thin_count_summary = sum(
        1 for nodes in communities.values()
        if 0 < sum(1 for n in nodes if not _ifn(G, n)) < min_community_size
    )
    shown_count = len(communities) - thin_count_summary

    lines += [
        "",
        "## 概要",
        f"- {G.number_of_nodes()} 个节点 · {G.number_of_edges()} 条边 · {len(communities)} 个社区"
        + (f"（展示 {shown_count} 个，省略 {thin_count_summary} 个稀疏社区）" if thin_count_summary else ""),
        f"- 提取：{ext_pct}% EXTRACTED · {inf_pct}% INFERRED · {amb_pct}% AMBIGUOUS"
        + (f" · INFERRED：{len(inf_edges)} 条边（平均置信度：{inf_avg}）" if inf_avg is not None else ""),
        f"- Token 开销：{token_cost.get('input', 0):,} 输入 · {token_cost.get('output', 0):,} 输出",
    ]

    if built_at_commit:
        lines += [
            "",
            "## 图谱新鲜度",
            f"- 构建自提交：`{built_at_commit[:8]}`",
            "- 运行 `git rev-parse HEAD` 并与之对比，以检查图谱是否陈旧。",
            "- 代码变更后运行 `graphify update .`（无 API 开销）。",
        ]

    # Community hub navigation. The `_COMMUNITY_*.md` notes these wikilinks target
    # are only created by the opt-in `--obsidian` export, and the report is written
    # at build time (before any export runs), so emitting wikilinks by default left
    # every link dangling — polluting an Obsidian vault's graph view and rendering as
    # literal brackets everywhere else (#1712). Emit wikilinks only when the caller
    # signals Obsidian output; otherwise a plain list, which navigates nowhere-to-break.
    if non_empty:
        lines += ["", "## 社区枢纽（导航）"]
        for cid in non_empty:
            label = community_labels.get(cid, f"社区 {cid}")
            if obsidian:
                safe = _safe_community_name(label)
                lines.append(f"- [[_COMMUNITY_{safe}|{label}]]")
            else:
                lines.append(f"- {label}")

    lines += [
        "",
        "## God Nodes（连接数最多——核心抽象）",
    ]
    for i, node in enumerate(god_node_list, 1):
        lines.append(f"{i}. `{node['label']}` - {node['degree']} 条边")

    lines += ["", "## 意外连接（你多半没注意到这些）"]
    if surprise_list:
        for s in surprise_list:
            relation = s.get("relation", "related_to")
            note = s.get("note", "")
            files = s.get("source_files", ["", ""])
            conf = s.get("confidence", "EXTRACTED")
            cscore = s.get("confidence_score")
            if conf == "INFERRED" and cscore is not None:
                conf_tag = f"INFERRED {cscore:.2f}"
            else:
                conf_tag = conf
            sem_tag = " [语义相似]" if relation == "semantically_similar_to" else ""
            lines += [
                f"- `{s['source']}` --{relation}--> `{s['target']}`  [{conf_tag}]{sem_tag}",
                f"  {files[0]} → {files[1]}" + (f"  _{note}_" if note else ""),
            ]
    else:
        lines.append("- 未检测到——所有连接都在同一批源文件内部。")

    # Circular imports surfaced from file-level dependency graph. Only meaningful
    # for code — a documents-only corpus has no imports, so the section is pure
    # noise there ("None detected" on every run). Emit it only when the graph
    # actually contains code (#1657).
    _has_code = any(
        d.get("file_type") == "code" for _, d in G.nodes(data=True)
    ) or any(
        d.get("relation") in ("imports", "imports_from")
        for *_e, d in G.edges(data=True)
    )
    if _has_code:
        from .analyze import find_import_cycles
        cycles = find_import_cycles(G)
        lines += ["", "## 导入循环"]
        if cycles:
            for c in cycles:
                cycle = c.get("cycle", [])
                length = c.get("length", len(cycle))
                if not cycle:
                    continue
                cycle_path = " -> ".join(cycle + [cycle[0]])
                lines.append(f"- {length} 个文件的循环：`{cycle_path}`")
        else:
            lines.append("- 未检测到。")

    hyperedges = G.graph.get("hyperedges", [])
    if hyperedges:
        lines += ["", "## 超边（群组关系）"]
        for h in hyperedges:
            node_labels = ", ".join(h.get("nodes", []))
            conf = h.get("confidence", "INFERRED")
            cscore = h.get("confidence_score")
            conf_tag = f"{conf} {cscore:.2f}" if cscore is not None else conf
            lines.append(f"- **{h.get('label', h.get('id', ''))}** — {node_labels} [{conf_tag}]")

    lines += ["", f"## 社区（共 {len(communities)} 个，省略 {thin_count_summary} 个稀疏社区）"]
    for cid, nodes in communities.items():
        label = community_labels.get(cid, f"社区 {cid}")
        score = cohesion_scores.get(cid, 0.0)
        # Filter method/function stubs from display - they're structural noise
        real_nodes = [n for n in nodes if not _ifn(G, n)]
        if not real_nodes:
            continue
        if len(real_nodes) < min_community_size:
            continue
        display = [G.nodes[n].get("label", n) for n in real_nodes[:8]]
        suffix = f"（还有 {len(real_nodes)-8} 个）" if len(real_nodes) > 8 else ""
        lines += [
            "",
            f"### 社区 {cid} —— \"{label}\"",
            f"凝聚度：{score:.2f}",
            f"节点（共 {len(real_nodes)} 个）：{', '.join(display)}{suffix}",
        ]

    ambiguous = [(u, v, d) for u, v, d in G.edges(data=True) if d.get("confidence") == "AMBIGUOUS"]
    if ambiguous:
        lines += ["", "## 歧义边——需复核"]
        for u, v, d in ambiguous:
            ul = G.nodes[u].get("label", u)
            vl = G.nodes[v].get("label", v)
            lines += [
                f"- `{ul}` → `{vl}`  [AMBIGUOUS]",
                f"  {d.get('source_file', '')} · 关系：{d.get('relation', 'unknown')}",
            ]

    # --- Gaps section ---
    from .analyze import _is_file_node, _is_concept_node

    isolated = [
        n for n in G.nodes()
        if G.degree(n) <= 1
        and not _is_file_node(G, n)
        and not _is_concept_node(G, n)
        and G.nodes[n].get("file_type") != "rationale"
    ]
    thin_communities = {
        cid: nodes for cid, nodes in communities.items()
        if 0 < sum(1 for n in nodes if not _is_file_node(G, n)) < 3
    }
    gap_count = len(isolated) + len(thin_communities)

    if gap_count > 0 or amb_pct > 20:
        lines += ["", "## 知识空白"]
        if isolated:
            isolated_labels = [G.nodes[n].get("label", n) for n in isolated[:5]]
            suffix = f"（还有 {len(isolated)-5} 个）" if len(isolated) > 5 else ""
            lines.append(f"- **{len(isolated)} 个孤立节点：** {', '.join(f'`{l}`' for l in isolated_labels)}{suffix}")
            lines.append("  这些节点的连接数 ≤1——可能漏掉了边，或组件未文档化。")
        if thin_communities:
            lines.append(f"- **{len(thin_communities)} 个稀疏社区（<{min_community_size} 个节点）已从报告中省略** —— 运行 `graphify query` 探索孤立节点。")
        if amb_pct > 20:
            lines.append(f"- **歧义比例偏高：{amb_pct}% 的边为 AMBIGUOUS。** 请复核上面的“歧义边”一节。")

    # --- Work-memory lessons (derived overlay) ---
    # Preferred sources come from the .graphify_learning.json sidecar; the
    # query-scoped dead-ends come from the reflect aggregate. Section omitted
    # entirely when neither is present, so a graph with no work-memory is
    # byte-identical to the pre-feature report.
    _learning_section(lines, learning)

    if suggested_questions:
        lines += ["", "## 建议提问"]
        no_signal = len(suggested_questions) == 1 and suggested_questions[0].get("type") == "no_signal"
        if no_signal:
            lines.append(f"_{suggested_questions[0]['why']}_")
        else:
            lines.append("_这张图谱特别适合回答以下问题：_")
            lines.append("")
            for q in suggested_questions:
                if q.get("question"):
                    lines.append(f"- **{q['question']}**")
                    lines.append(f"  _{q['why']}_")

    return "\n".join(lines)
