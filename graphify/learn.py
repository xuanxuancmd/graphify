"""学习模式内容生成（learn.json sidecar v2 —— 多视角）。

graph.html「学习」页签的数据源，面向**人类读者**：AI 生成或遗留的代码
让人看不懂、无法检视和维护。v2 按「多视角」组织内容：

  业务流视角    从入口沿调用链走出的主路径：Mermaid 时序图 + 分步讲解
               + 当前步骤的符号上下文与代码锚点。
  代码架构视角  目录结构（按文件/目录聚合）+ 关键特性卡 + 基础类图。
  特性下钻视角  每个特性一篇深度分析文档（六节：概览 / 关键技术点 /
               核心实现 / 性能设计 / 可靠性设计 / 已知限制与验证），
               全部锚到代码；结构化渲染 + 可切换的 MD 源码。

管线遵循 Swimm 式「先确定性、后生成」：时序图、类图、目录树、调用
统计、焦点行、抛错点、TODO 扫描全部从 graph.json + 源码确定性推导；
LLM（可选）只做最后的散文化（流程讲解、技术点命名、性能/可靠性叙
述、焦点行注释）。零 LLM 时输出纯结构化内容 —— 仍然完整可用。

增量缓存：业务流/特性按涉及文件 SHA256 指纹缓存，未变更不重生成。
CLI（run_learn）额外把每篇特性文档落盘到 .graph/features/<id>.md。
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LEARN_SIDECAR_NAME = "learn.json"
LEARN_VERSION = 2
FEATURES_DIR_NAME = "features"

# 表达 "A 依赖 B" 的关系类型。
_DEP_RELATIONS = frozenset({"imports", "imports_from", "calls", "uses"})

_CODE_EXTS = frozenset({
    ".py", ".js", ".cjs", ".mjs", ".ts", ".tsx", ".jsx", ".go", ".rs",
    ".java", ".rb", ".c", ".h", ".cpp", ".hpp", ".cc", ".cs", ".kt",
    ".swift", ".php", ".scala", ".lua", ".sh", ".zig", ".dart",
})

_MAX_FLOWS = 6
_MAX_FLOW_MESSAGES = 14
_MAX_TREE_ROWS = 40
_MAX_CLASSES = 10
_MAX_METHODS_PER_CLASS = 6
_MAX_CODE_EXCERPT_LINES = 16
_DESC_CAP = 400
_MAX_STR = 2000

_ENTRY_FUNC_RE = re.compile(r"^(handle|on|do|run|serve)[A-Z_]")


# ---------------------------------------------------------------------------
# Sidecar 读写
# ---------------------------------------------------------------------------

def load_learn_sidecar(graph_html_path: Path) -> dict:
    """加载 graph.html 同目录的 learn.json。Best-effort，任何错误返回 {}。

    只认 v2（多视角 schema）；v1 或损坏数据一律视为空，前端提示重新生成。
    """
    sidecar = Path(graph_html_path).parent / LEARN_SIDECAR_NAME
    try:
        data = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict) or data.get("version") != LEARN_VERSION:
        return {}
    return data


# ---------------------------------------------------------------------------
# 基础工具（与 v1 同源）
# ---------------------------------------------------------------------------

def _file_sha(path: Path | None) -> str:
    if path is None:
        return ""
    h = hashlib.sha256()
    try:
        h.update(path.read_bytes())
    except OSError:
        return ""
    return h.hexdigest()


def _resolve_source(root: Path, source_file: str) -> Path | None:
    if not source_file:
        return None
    p = root / source_file
    if p.is_file():
        return p
    return None


def _kind_of(data: dict) -> str:
    """节点的人类可读类别：file / class / function / concept。"""
    label = str(data.get("label") or "")
    if str(data.get("file_type") or "") in ("concept", "rationale", "document", "paper", "image"):
        return "concept"
    lowered = label.lower()
    if lowered.endswith(tuple(_CODE_EXTS)) or lowered.endswith((".md", ".txt", ".rst", ".yaml", ".yml", ".json", ".toml")):
        return "file"
    node_type = str(data.get("node_type") or data.get("node_kind") or "").lower()
    if node_type in {"class", "klass", "struct", "interface", "enum", "trait", "model"}:
        return "class"
    if node_type in {"module", "file", "package", "namespace"}:
        return "file"
    if node_type in {"endpoint", "route", "api", "handler", "controller"}:
        return "function"
    if label[:1].isupper() and not label.endswith("()"):
        return "class"
    return "function"


def _dep_maps(G):
    """(callers, callees)：沿 _src→_tgt 真实方向的依赖邻接表。"""
    callers: dict[str, set[str]] = {}
    callees: dict[str, set[str]] = {}
    for u, v, data in G.edges(data=True):
        if data.get("relation") not in _DEP_RELATIONS:
            continue
        src = str(data.get("_src", u))
        tgt = str(data.get("_tgt", v))
        callees.setdefault(src, set()).add(tgt)
        callers.setdefault(tgt, set()).add(src)
    return callers, callees


def _node_scores(G, callers, callees) -> dict[str, float]:
    scores: dict[str, float] = {}
    for nid, data in G.nodes(data=True):
        if not isinstance(data, dict):
            continue
        fan_in = len(callers.get(nid, ()))
        fan_out = len(callees.get(nid, ()))
        deg = G.degree(nid)
        scores[nid] = fan_in * 2.0 + deg * 0.5 + fan_out * 0.3
    return scores


def _line_of(data: dict) -> int:
    loc = str(data.get("source_location") or "")
    if loc.startswith("L"):
        try:
            return int(loc[1:].split("-")[0].split(":")[0])
        except ValueError:
            return 0
    return 0


def _stem(source_file: str) -> str:
    """auth.service.ts → auth.service（参与者名）。"""
    s = str(source_file or "").replace("\\", "/").rstrip("/")
    if "/" in s:
        s = s.rsplit("/", 1)[1]
    for ext in (".tsx", ".ts", ".jsx", ".js", ".py", ".go", ".rs", ".java", ".cs", ".rb", ".php", ".kt", ".swift"):
        if s.endswith(ext):
            s = s[: -len(ext)]
            break
    return s or "module"


def _clean_str(v, cap: int = _MAX_STR) -> str:
    s = str(v or "").strip()
    return s[:cap]


def _first_desc_line(data: dict) -> str:
    desc = str(data.get("desc") or "").strip()
    if not desc:
        return ""
    return desc.split("\n")[0].strip()[:160]


# ---------------------------------------------------------------------------
# 焦点行启发式（Crosby：专家视线集中在复杂/比较语句行）
# ---------------------------------------------------------------------------

_FOCUS_COMMENT_MARKERS = ("NOTE", "WHY", "IMPORTANT", "HACK", "TODO", "FIXME", "RATIONALE")
_FOCUS_KEYWORDS = ("if", "elif", "for", "while", "switch", "case", "match", "try", "except", "catch", "throw", "raise", "return")
_FOCUS_OPERATORS = ("==", "!=", "<=", ">=", "&&", "||", "<", ">", "??", "?.")


def _read_lines(root: Path, sf: str) -> list[str] | None:
    p = _resolve_source(root, sf)
    if p is None:
        return None
    try:
        return p.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None


def _structural_focal_lines(root: Path, sf: str, start_line: int, span: int, *, cap: int = 5) -> list[dict]:
    """从源码确定性挑焦点行：控制流/比较运算密度最高 + 理由注释行。"""
    if start_line <= 0:
        return []
    lines = _read_lines(root, sf)
    if lines is None:
        return []
    end = min(len(lines), start_line - 1 + max(span, 1))
    scored: list[tuple[int, int, str]] = []
    for idx in range(start_line - 1, end):
        raw = lines[idx]
        text = raw.strip()
        if not text or len(text) < 8:
            continue
        comment_hit = next((m for m in _FOCUS_COMMENT_MARKERS if m in text.upper() and ("#" in raw or "//" in raw or "/*" in raw or raw.lstrip().startswith("*"))), None)
        if comment_hit:
            scored.append((10, idx + 1, text[:160]))
            continue
        score = 0
        padded = " " + text + " "
        for kw in _FOCUS_KEYWORDS:
            score += 2 * (padded.count(f" {kw} ") + padded.count(f" {kw}("))
        for op in _FOCUS_OPERATORS:
            score += text.count(op)
        score += text.count("!") - text.count("!=")
        if score >= 3:
            scored.append((score, idx + 1, text[:160]))
    scored.sort(key=lambda t: (-t[0], t[1]))
    picked = sorted(scored[:cap], key=lambda t: t[1])
    return [{"line": ln, "note": note} for _, ln, note in picked]


def _code_excerpt(root: Path, sf: str, start_line: int, span: int, focal: list[dict]) -> dict:
    """代码走读块：真实行号 + 焦点行标记。行内容截断保真。"""
    lines = _read_lines(root, sf)
    if lines is None or start_line <= 0:
        return {}
    n = max(1, min(span if span else 10, _MAX_CODE_EXCERPT_LINES))
    end = min(len(lines), start_line - 1 + n)
    focal_by_line = {f["line"]: f.get("note", "") for f in focal}
    out_lines = []
    for idx in range(start_line - 1, end):
        ln = idx + 1
        out_lines.append({
            "ln": ln,
            "text": lines[idx][:200],
            "focal": ln in focal_by_line,
            "note": focal_by_line.get(ln, ""),
        })
    return {"file": sf, "start": start_line, "end": end, "lines": out_lines}


def _scan_throw_lines(root: Path, sf: str, start_line: int, span: int, *, cap: int = 4) -> list[dict]:
    """可靠性素材：符号范围内 throw/raise 行。"""
    lines = _read_lines(root, sf)
    if lines is None or start_line <= 0:
        return []
    end = min(len(lines), start_line - 1 + max(span, 1))
    hits = []
    for idx in range(start_line - 1, end):
        text = lines[idx].strip()
        if re.search(r"\b(throw|raise)\b", text):
            hits.append({"line": idx + 1, "text": text[:140], "anchor": f"{sf} L{idx + 1}"})
            if len(hits) >= cap:
                break
    return hits


def _scan_todo_lines(root: Path, sf: str, *, cap: int = 3) -> list[dict]:
    """已知限制素材：文件内 TODO/FIXME/HACK。"""
    lines = _read_lines(root, sf)
    if lines is None:
        return []
    hits = []
    for idx, raw in enumerate(lines):
        m = re.search(r"#\s*(TODO|FIXME|HACK)\b[:：]?\s*(.+)", raw)
        if not m:
            m = re.search(r"//\s*(TODO|FIXME|HACK)\b[:：]?\s*(.+)", raw)
        if m:
            hits.append({"line": idx + 1, "kind": m.group(1), "text": m.group(2).strip()[:120], "anchor": f"{sf} L{idx + 1}"})
            if len(hits) >= cap:
                break
    return hits


# ---------------------------------------------------------------------------
# 业务流视角
# ---------------------------------------------------------------------------

def _flow_seeds(G, callers, callees, scores) -> list[str]:
    """流程入口优先级：端点节点 > handle/onXxx 处理函数 > 高分函数。"""
    endpoints = []
    handlers = []
    for nid, data in G.nodes(data=True):
        if not isinstance(data, dict) or _kind_of(data) not in ("function", "concept"):
            continue
        if str(data.get("node_kind") or "") == "endpoint" or re.match(r"^(GET|POST|PUT|DELETE|PATCH):", str(data.get("label") or "")):
            endpoints.append(nid)
        elif _ENTRY_FUNC_RE.match(str(data.get("label") or "")) and len(callers.get(nid, ())) <= 2:
            handlers.append(nid)
    endpoints.sort(key=lambda n: -scores.get(n, 0.0))
    handlers.sort(key=lambda n: -scores.get(n, 0.0))
    seeds = endpoints[:_MAX_FLOWS]
    if len(seeds) < _MAX_FLOWS:
        seen = set(seeds)
        for h in handlers:
            if h not in seen:
                seeds.append(h)
                seen.add(h)
            if len(seeds) >= _MAX_FLOWS:
                break
    if not seeds:
        # 退化：入口文件的高扇出函数。
        fallback = [
            nid for nid, data in G.nodes(data=True)
            if isinstance(data, dict) and _kind_of(data) == "function" and len(callees.get(nid, ())) >= 2
        ]
        fallback.sort(key=lambda n: -scores.get(n, 0.0))
        seeds = fallback[:_MAX_FLOWS]
    return seeds


def _mermaid_safe(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.\u4e00-\u9fff]+", "_", str(s or ""))[:40] or "P"


def _build_flow(G, seed: str, callers, callees, scores, root: Path) -> dict | None:
    """从 seed 沿调用链贪心走主路径，产出时序图 + 步骤 + 上下文。"""
    data = G.nodes[seed]
    label = str(data.get("label") or seed)
    is_endpoint = str(data.get("node_kind") or "") == "endpoint" or re.match(r"^(GET|POST|PUT|DELETE|PATCH):", label)

    # 主路径：每步走分数最高的未访问 callee。
    path: list[str] = [seed]
    visited = {seed}
    cur = seed
    while len(path) <= _MAX_FLOW_MESSAGES:
        nexts = [c for c in callees.get(cur, ()) if c in G and c not in visited and _kind_of(G.nodes[c]) in ("function", "class")]
        if not nexts:
            break
        nexts.sort(key=lambda n: -scores.get(n, 0.0))
        cur = nexts[0]
        visited.add(cur)
        path.append(cur)

    # 参与者：按文件聚合（同文件多函数折叠为一个 participant）。
    participants: list[str] = []
    part_of: dict[str, str] = {}
    for nid in path:
        stem = _stem(str(G.nodes[nid].get("source_file") or ""))
        if stem not in part_of:
            part_of[stem] = stem
            participants.append(stem)

    # mermaid 时序图。
    lines = ["sequenceDiagram", "    autonumber"]
    for i, p in enumerate(participants, 1):
        lines.append(f"    participant P{i} as {_mermaid_safe(p)}")
    entry_txt = label.replace(":", " ") if is_endpoint else f"调用 {label}()"
    lines.append(f"    Client ->> P1: {_mermaid_safe(entry_txt)}")
    prev_p = 1
    for nid in path:
        stem = _stem(str(G.nodes[nid].get("source_file") or ""))
        pi = participants.index(stem) + 1
        fn_label = str(G.nodes[nid].get("label") or "")
        if pi != prev_p:
            lines.append(f"    P{prev_p} ->> P{pi}: {_mermaid_safe(fn_label)}()")
        prev_p = pi
    mermaid = "\n".join(lines)

    # 步骤。
    steps: list[dict] = []
    edge_count = 0
    prev_p = 1
    prev_nid = None
    for nid in path:
        ndata = G.nodes[nid]
        stem = _stem(str(ndata.get("source_file") or ""))
        pi = participants.index(stem) + 1
        fn_label = str(ndata.get("label") or "")
        cite_sf = str(ndata.get("source_file") or "")
        cite_ln = _line_of(ndata)
        cite = f"{cite_sf} L{cite_ln}" if cite_sf and cite_ln else cite_sf
        if prev_nid is None:
            steps.append({
                "msg": f"Client → {participants[0]} · {entry_txt}",
                "desc": _first_desc_line(ndata) or f"请求进入 {participants[0]}。",
                "cite": cite,
            })
        else:
            edge_count += 1
            desc = _first_desc_line(ndata) or f"{fn_label} 被调用。"
            steps.append({
                "msg": f"{participants[prev_p - 1]} → {stem} · {fn_label}()",
                "desc": desc,
                "cite": cite,
            })
        prev_p, prev_nid = pi, nid
    # 收尾：指向特性下钻。
    steps.append({
        "msg": "下一步建议",
        "desc": "进入「特性下钻」查看完整分析文档（关键技术点 / 性能 / 可靠性）。",
        "cite": "feature doc",
    })

    # 上下文面板：主路径中分数最高的函数。
    core = max(path, key=lambda n: scores.get(n, 0.0))
    cdata = G.nodes[core]
    anchors = []
    for nid in path[:6]:
        nd = G.nodes[nid]
        sf = str(nd.get("source_file") or "")
        ln = _line_of(nd)
        if sf:
            anchors.append(f"{sf} L{ln}" if ln else sf)
    fps = sorted({
        _file_sha(_resolve_source(root, str(G.nodes[n].get("source_file") or "")))
        for n in path if G.nodes[n].get("source_file")
    } - {""})

    name = label
    if is_endpoint:
        seg = label.rsplit("/", 1)[-1] if "/" in label else label
        name = f"{seg} 流"
        entry = label.replace(":", " ")
    else:
        entry = f"{label}()"
    flow_desc = _first_desc_line(data)

    return {
        "id": "flow_" + _mermaid_safe(label).lower()[:30],
        "name": name,
        "entry": entry,
        "desc": flow_desc,
        "meta": f"{len(participants)} 参与者 · {len(path)} 跳",
        "provenance": f"{edge_count} 条调用边 · 源自 calls/uses（EXTRACTED）",
        "participants": participants,
        "mermaid": mermaid,
        "steps": steps,
        "context": {
            "node": str(cdata.get("label") or core),
            "intent": _first_desc_line(cdata) or f"{str(cdata.get('label') or core)}，位于 {cdata.get('source_file') or '未知文件'}。",
            "anchors": anchors[:8],
        },
        "fp": hashlib.sha256("|".join(fps).encode()).hexdigest()[:16],
        "path": path,
    }


def _build_flows(G, callers, callees, scores, root: Path) -> list[dict]:
    flows = []
    seen_names: set[str] = set()
    for seed in _flow_seeds(G, callers, callees, scores):
        flow = _build_flow(G, seed, callers, callees, scores, root)
        if not flow or flow["name"] in seen_names:
            continue
        seen_names.add(flow["name"])
        flows.append(flow)
    return flows


# ---------------------------------------------------------------------------
# 代码架构视角
# ---------------------------------------------------------------------------

def _build_tree(G, scores) -> list[dict]:
    """目录树行：目录行（文件数）+ 文件行（代表符号 + 行号）。"""
    files = []
    for nid, data in G.nodes(data=True):
        if not isinstance(data, dict) or _kind_of(data) != "file":
            continue
        sf = str(data.get("source_file") or "")
        if not sf:
            continue
        # 该文件的代表符号：同文件最高分函数。
        best = None
        for m, md in G.nodes(data=True):
            if m == nid or not isinstance(md, dict):
                continue
            if str(md.get("source_file") or "") != sf or _kind_of(md) not in ("function", "class"):
                continue
            if best is None or scores.get(m, 0.0) > scores.get(best, 0.0):
                best = m
        note = ""
        if best is not None:
            bd = G.nodes[best]
            note = f"{bd.get('label')} L{_line_of(bd)}" if _line_of(bd) else str(bd.get("label") or "")
        files.append((sf, note))
    files.sort()

    # 目录聚合。
    dir_counts: dict[str, int] = {}
    for sf, _ in files:
        parts = sf.replace("\\", "/").split("/")
        if len(parts) > 1:
            d = parts[0]
            dir_counts[d] = dir_counts.get(d, 0) + 1
        else:
            dir_counts["."] = dir_counts.get(".", 0) + 1

    rows: list[dict] = []
    dirs_done: set[str] = set()
    for sf, note in files:
        parts = sf.replace("\\", "/").split("/")
        if len(parts) > 1 and parts[0] not in dirs_done:
            dirs_done.add(parts[0])
            rows.append({"label": f"{parts[0]}/", "kind": "dir", "note": f"{dir_counts[parts[0]]} 文件"})
        indent = "    " if len(parts) > 1 else ""
        rows.append({"label": f"{indent}{parts[-1]}", "kind": "file", "note": note})
        if len(rows) >= _MAX_TREE_ROWS:
            break
    return rows


def _build_class_diagram(G, scores, callers, callees) -> str:
    """基础类图：类 + 方法（同文件归属）+ 类间调用关系。"""
    classes = []
    for nid, data in G.nodes(data=True):
        if not isinstance(data, dict) or _kind_of(data) != "class":
            continue
        if not data.get("source_file"):
            continue
        classes.append(nid)
    classes.sort(key=lambda n: -scores.get(n, 0.0))
    classes = classes[:_MAX_CLASSES]
    if not classes:
        return ""

    # 方法：同文件函数；文件只有一个类时全归它，否则按命名空间。
    by_file: dict[str, list[str]] = {}
    for nid in classes:
        sf = str(G.nodes[nid].get("source_file") or "")
        by_file.setdefault(sf, []).append(nid)
    methods_of: dict[str, list[str]] = {}
    for m, md in G.nodes(data=True):
        if not isinstance(md, dict) or _kind_of(md) != "function":
            continue
        sf = str(md.get("source_file") or "")
        group = by_file.get(sf)
        if not group:
            continue
        owner = group[0] if len(group) == 1 else None
        if owner is None:
            ns = str((md.get("metadata") or {}).get("namespace") or "")
            owner = next((c for c in group if str(G.nodes[c].get("label") or "") in ns), group[0])
        methods_of.setdefault(owner, []).append(m)

    lines = ["classDiagram"]
    for c in classes:
        name = _mermaid_safe(str(G.nodes[c].get("label") or "Cls"))
        lines.append(f"    class {name} {{")
        shown = 0
        for m in methods_of.get(c, []):
            if shown >= _MAX_METHODS_PER_CLASS:
                break
            lines.append(f"        +{_mermaid_safe(str(G.nodes[m].get('label') or 'm'))}()")
            shown += 1
        lines.append("    }")

    # 类间关系：A 的方法调用 B 的方法 → A --> B。
    class_by_file: dict[str, str] = {}
    for c in classes:
        class_by_file[str(G.nodes[c].get("source_file") or "")] = _mermaid_safe(str(G.nodes[c].get("label") or "Cls"))
    rels: set[tuple[str, str]] = set()
    for src, tgts in callees.items():
        src_sf = str(G.nodes.get(src, {}).get("source_file") or "")
        if src_sf not in class_by_file:
            continue
        for t in tgts:
            t_sf = str(G.nodes.get(t, {}).get("source_file") or "")
            if t_sf in class_by_file and t_sf != src_sf:
                rels.add((class_by_file[src_sf], class_by_file[t_sf]))
    for a, b in sorted(rels):
        lines.append(f"    {a} --> {b}")
    return "\n".join(lines)


def _build_architecture(G, communities, community_labels, scores, flows) -> dict:
    features = []
    for flow in flows:
        features.append({
            "name": flow["name"],
            "desc": flow.get("desc") or flow["entry"],
            "modules": " · ".join(flow["participants"][:4]),
            "flow_id": flow["id"],
        })
    return {
        "tree": _build_tree(G, scores),
        "features": features,
        "class_diagram": _build_class_diagram(G, scores, *_dep_maps(G)),
    }


# ---------------------------------------------------------------------------
# 特性下钻
# ---------------------------------------------------------------------------

def _symbol_span_map(G) -> dict[str, tuple[str, int, int]]:
    """function/class 节点 → (source_file, start_line, 近似跨度)。"""
    by_file: dict[str, list[tuple[int, str]]] = {}
    for nid, data in G.nodes(data=True):
        if not isinstance(data, dict) or _kind_of(data) not in ("function", "class"):
            continue
        sf = str(data.get("source_file") or "")
        ln = _line_of(data)
        if sf and ln > 0:
            by_file.setdefault(sf, []).append((ln, nid))
    out: dict[str, tuple[str, int, int]] = {}
    for sf, items in by_file.items():
        items.sort()
        for i, (ln, nid) in enumerate(items):
            nxt = items[i + 1][0] if i + 1 < len(items) else ln + 12
            out[nid] = (sf, ln, max(1, nxt - ln))
    return out


def _simple_inline(s: str) -> str:
    """结构化叙述里允许的极小 html：strong/code。"""
    return _clean_str(s, 800)


def _build_feature_doc(G, flow: dict, root: Path, spans: dict, scores) -> dict | None:
    """确定性组装特性下钻六节。"""
    path = flow.get("path") or []
    if not path:
        return None
    participants = flow["participants"]
    involved_files = sorted({
        str(G.nodes[n].get("source_file") or "") for n in path if G.nodes[n].get("source_file")
    } - {""})

    anchors: list[str] = []
    for nid in path[:8]:
        sf = str(G.nodes[nid].get("source_file") or "")
        ln = _line_of(G.nodes[nid])
        if sf:
            anchors.append(f"{sf} L{ln}" if ln else sf)

    # ── 01 概览 ──
    overview_p = (
        f"本特性对应业务流「{flow['name']}」，入口 {flow['entry']}。"
        f"主路径经过 {len(participants)} 个模块：{'、'.join(participants)}。"
    )
    if flow.get("desc"):
        overview_p += flow["desc"]
    sec1_blocks = [{"type": "p", "text": _simple_inline(overview_p)}]

    # ── 02 关键技术点 ──
    tp_items = []
    for nid in path:
        nd = G.nodes[nid]
        why = str(nd.get("rationale") or "").strip()
        if why:
            tp_items.append({
                "name": str(nd.get("label") or nid),
                "why": _simple_inline(why),
                "anchors": [f"{nd.get('source_file')} L{_line_of(nd)}"],
            })
    if not tp_items:
        for nid in path[1:4]:
            nd = G.nodes[nid]
            d = _first_desc_line(nd)
            if d:
                tp_items.append({
                    "name": str(nd.get("label") or nid),
                    "why": _simple_inline(d),
                    "anchors": [f"{nd.get('source_file')} L{_line_of(nd)}"],
                })
    sec2_blocks = [{"type": "techpoints", "items": tp_items[:4]}] if tp_items else []

    # ── 03 核心实现 ──
    sec3_blocks = [{"type": "mermaid", "src": flow["mermaid"]}]
    core = max(path, key=lambda n: scores.get(n, 0.0))
    if core in spans:
        sf, ln, span = spans[core]
        focal = _structural_focal_lines(root, sf, ln, span)
        excerpt = _code_excerpt(root, sf, ln, span, focal)
        if excerpt:
            sec3_blocks.append({
                "type": "code", "file": sf, "start": ln, "end": excerpt["end"],
                "tier": "关键算法" if focal else "契约级",
                "lines": excerpt["lines"],
                "fn": str(G.nodes[core].get("label") or core),
            })

    # ── 04 性能设计（结构性事实）──
    perf = []
    repo_calls = sum(1 for n in path if re.search(r"(find|get|query|save|update|delete|load|fetch)", str(G.nodes[n].get("label") or ""), re.I))
    if repo_calls:
        perf.append({"text": f"主路径含 {repo_calls} 次疑似仓储/IO 调用（按符号名启发式）。", "anchor": involved_files[0] if involved_files else ""})
    perf.append({"text": f"调用深度 {len(path)} 跳，跨 {len(participants)} 个模块。", "anchor": ""})
    sec4_blocks = [{"type": "bullets", "items": perf}]

    # ── 05 可靠性设计（抛错点扫描）──
    rel = []
    for nid in path:
        if nid not in spans:
            continue
        sf, ln, span = spans[nid]
        for hit in _scan_throw_lines(root, sf, ln, span, cap=2):
            rel.append({"text": f"L{hit['line']} 抛出异常：{hit['text']}", "anchor": hit["anchor"]})
    if not rel:
        rel.append({"text": "主路径未扫描到显式 throw/raise。", "anchor": ""})
    sec5_blocks = [{"type": "bullets", "items": rel[:4]}]

    # ── 06 已知限制与验证 ──
    limits = []
    for sf in involved_files[:4]:
        for hit in _scan_todo_lines(root, sf, cap=2):
            limits.append({"text": f"{hit['kind']}：{hit['text']}", "anchor": hit["anchor"]})
    test_refs = []
    for nid, data in G.nodes(data=True):
        if not isinstance(data, dict):
            continue
        tsf = str(data.get("source_file") or "")
        if "test" in tsf.lower() or "spec" in tsf.lower():
            for p in path:
                if G.has_edge(nid, p) or G.has_edge(p, nid):
                    test_refs.append(tsf)
                    break
        if len(test_refs) >= 3:
            break
    if not limits:
        limits.append({"text": "未扫描到 TODO/FIXME/HACK 标记。", "anchor": ""})
    if test_refs:
        limits.append({"text": "测试覆盖：" + "、".join(sorted(set(test_refs))), "anchor": sorted(set(test_refs))[0]})
    else:
        limits.append({"text": "未发现引用本特性符号的测试文件。", "anchor": ""})
    sec6_blocks = [{"type": "bullets", "items": limits[:5]}]

    sections = [
        {"no": "01", "title": "特性概览", "blocks": sec1_blocks},
        {"no": "02", "title": "关键技术点", "blocks": sec2_blocks},
        {"no": "03", "title": "核心实现", "blocks": sec3_blocks},
        {"no": "04", "title": "性能设计", "blocks": sec4_blocks},
        {"no": "05", "title": "可靠性设计", "blocks": sec5_blocks},
        {"no": "06", "title": "已知限制与验证", "blocks": sec6_blocks},
    ]

    feature = {
        "id": "feat_" + flow["id"].removeprefix("flow_"),
        "name": flow["name"],
        "flow_id": flow["id"],
        "sections": sections,
        "outline": [{"no": s["no"], "title": s["title"]} for s in sections],
        "anchors": anchors[:14],
        "involved_files": involved_files,
    }
    feature["doc_md"] = _assemble_doc_md(feature)
    fps = sorted(_file_sha(_resolve_source(root, sf)) for sf in involved_files) 
    feature["fp"] = hashlib.sha256("|".join(f for f in fps if f).encode()).hexdigest()[:16]
    return feature


def _assemble_doc_md(feature: dict) -> str:
    """把结构化 sections 拼成 markdown 源码（源码视图 + 落盘 .md）。"""
    out = [f"# {feature['name']}（特性下钻）", ""]
    for sec in feature["sections"]:
        out.append(f"## {sec['no']} {sec['title']}")
        out.append("")
        for b in sec["blocks"]:
            if b["type"] == "p":
                out.append(b["text"])
            elif b["type"] == "bullets":
                for it in b["items"]:
                    line = f"- {it['text']}"
                    if it.get("anchor"):
                        line += f" `{it['anchor']}`"
                    out.append(line)
            elif b["type"] == "techpoints":
                for it in b["items"]:
                    out.append(f"- **{it['name']}** — {it['why']}" + (f" `{'、'.join(it.get('anchors', []))}`" if it.get("anchors") else ""))
            elif b["type"] == "mermaid":
                out.append("```mermaid")
                out.append(b["src"])
                out.append("```")
            elif b["type"] == "code":
                out.append(f"`{b['file']}` L{b['start']}-L{b['end']}（{b.get('tier', '')}）：")
                out.append("```")
                for ln in b["lines"]:
                    marker = " ←" if ln.get("focal") else ""
                    out.append(f"{ln['ln']:>4} | {ln['text']}{marker}")
                out.append("```")
            out.append("")
    return "\n".join(out).rstrip() + "\n"


def _build_features(G, flows, root: Path, spans, scores) -> list[dict]:
    feats = []
    for flow in flows:
        f = _build_feature_doc(G, flow, root, spans, scores)
        if f:
            feats.append(f)
    return feats


# ---------------------------------------------------------------------------
# LLM 增强（可选）
# ---------------------------------------------------------------------------

_FLOW_SYSTEM = """你在为「人类读者」讲解一个代码库的业务流。下面是一个从调用图确定性生成的流程：
若干步骤（消息 + 结构化描述 + 溯源）。请为每一步重写 description（1-2 句中文，
讲清这一步做什么、为什么重要，可提关键约束），并给整个流程一个更贴切的中文 name，
以及 context_intent（主符号的一句话说明）。技术名词保留英文。

只输出 JSON（无 markdown 代码块）：
{"name": "...", "context_intent": "...", "steps": [{"desc": "..."}, ...]}
steps 数组长度必须与输入一致，按原顺序。"""

_FEATURE_SYSTEM = """你在为「人类读者」写一份特性的深度分析文档（面向接手陌生代码的工程师和 AI 代码审阅者）。
下面是该特性的六节结构化骨架（事实、代码走读、锚点全部来自真实代码，不得推翻）。
请补写叙述性内容：overview（概览段落）、tech_points（每项 name+why）、perf（性能分析）、
reliability（可靠性分析）、focal_notes（代码走读焦点行注释 {行号: 一句话说明}）。
要求：中文、简洁、每条判断都必须能对应到给出的代码事实，不得编造源码中不存在的行为。

只输出 JSON（无 markdown 代码块）：
{"overview": "...", "tech_points": [{"name": "...", "why": "..."}], "perf": ["..."], "reliability": ["..."], "focal_notes": {"60": "..."}}"""

_SUMMARY_SYSTEM = """用 2-3 句中文概括这个代码库：它是什么、由哪几块组成、从哪里读起。
只输出 JSON：{"summary": "..."}"""


def _parse_learn_json(raw: str) -> dict:
    """解析 LLM 返回的 learn JSON 对象（fence 剥离 + 平衡对象提取）。"""
    from graphify.llm import _json_fragment_candidates

    for cand in _json_fragment_candidates(raw or ""):
        try:
            obj = json.loads(cand)
        except ValueError:
            continue
        if isinstance(obj, dict):
            return obj
    raise ValueError("LLM 响应中没有可解析的 JSON 对象")


def _llm_call(prompt: str, *, backend: str, model: str | None, max_tokens: int, usage_out: dict | None):
    from graphify.llm import _call_llm, _resolve_max_tokens

    kwargs: dict = {"backend": backend, "max_tokens": _resolve_max_tokens(max_tokens)}
    if model:
        kwargs["model"] = model
    if usage_out is not None:
        kwargs["usage_out"] = usage_out
    return _call_llm(prompt, **kwargs)


def _flow_prompt(flow: dict) -> str:
    lines = [_FLOW_SYSTEM, "", f"流程：{flow['name']}（入口 {flow['entry']}）", ""]
    for i, s in enumerate(flow["steps"]):
        lines.append(f"第 {i + 1} 步：{s['msg']}")
        lines.append(f"  结构化描述：{s['desc']}")
        lines.append(f"  溯源：{s['cite']}")
    lines.append("")
    lines.append(f"主符号：{flow['context']['node']} —— {flow['context']['intent']}")
    return "\n".join(lines)


def _enhance_flow_llm(flow: dict, *, backend: str, model: str | None, usage_out: dict | None) -> None:
    try:
        raw = _llm_call(_flow_prompt(flow), backend=backend, model=model,
                        max_tokens=min(1024 + 160 * len(flow["steps"]), 12288), usage_out=usage_out)
        parsed = _parse_learn_json(raw)
    except Exception as exc:  # noqa: BLE001
        print(f"[graphify learn] 流程增强失败（{flow['name']}）: {exc}", file=sys.stderr)
        return
    name = _clean_str(parsed.get("name"), 80)
    if name:
        flow["name"] = name
    intent = _clean_str(parsed.get("context_intent"), 400)
    if intent:
        flow["context"]["intent"] = intent
    steps = parsed.get("steps")
    if isinstance(steps, list):
        for i, new in enumerate(steps):
            if i < len(flow["steps"]) and isinstance(new, dict):
                d = _clean_str(new.get("desc"), 600)
                if d:
                    flow["steps"][i]["desc"] = d


def _feature_prompt(feature: dict) -> str:
    lines = [_FEATURE_SYSTEM, "", f"特性：{feature['name']}"]
    for sec in feature["sections"]:
        lines.append(f"")
        lines.append(f"== {sec['no']} {sec['title']} ==")
        for b in sec["blocks"]:
            if b["type"] == "p":
                lines.append(b["text"])
            elif b["type"] == "bullets":
                for it in b["items"]:
                    lines.append(f"- {it['text']} [{it.get('anchor', '')}]")
            elif b["type"] == "techpoints":
                for it in b["items"]:
                    lines.append(f"- {it['name']}: {it['why']} [{'; '.join(it.get('anchors', []))}]")
            elif b["type"] == "mermaid":
                lines.append("(时序图，略 — 与流程视角一致)")
            elif b["type"] == "code":
                lines.append(f"代码走读 {b['file']} L{b['start']}-L{b['end']}（{b.get('tier', '')}）:")
                for ln in b["lines"]:
                    mark = " ←焦点" if ln.get("focal") else ""
                    lines.append(f"  {ln['ln']} | {ln['text']}{mark}")
    return "\n".join(lines)


def _enhance_feature_llm(feature: dict, *, backend: str, model: str | None, usage_out: dict | None) -> None:
    try:
        raw = _llm_call(_feature_prompt(feature), backend=backend, model=model,
                        max_tokens=4096, usage_out=usage_out)
        parsed = _parse_learn_json(raw)
    except Exception as exc:  # noqa: BLE001
        print(f"[graphify learn] 特性文档增强失败（{feature['name']}）: {exc}", file=sys.stderr)
        return
    overview = _clean_str(parsed.get("overview"), 1000)
    if overview:
        for sec in feature["sections"]:
            if sec["no"] == "01" and sec["blocks"] and sec["blocks"][0]["type"] == "p":
                sec["blocks"][0]["text"] = overview
                break
    tps = parsed.get("tech_points")
    if isinstance(tps, list) and tps:
        items = []
        for tp in tps[:4]:
            if isinstance(tp, dict):
                items.append({"name": _clean_str(tp.get("name"), 80), "why": _clean_str(tp.get("why"), 500), "anchors": []})
        if items:
            for sec in feature["sections"]:
                if sec["no"] == "02":
                    sec["blocks"] = [{"type": "techpoints", "items": items}]
    def _merge_bullets(no: str, key: str) -> None:
        vals = parsed.get(key)
        if not isinstance(vals, list) or not vals:
            return
        items = [{"text": _clean_str(v, 400), "anchor": ""} for v in vals[:4] if isinstance(v, str) and v.strip()]
        if items:
            for sec in feature["sections"]:
                if sec["no"] == no:
                    sec["blocks"] = [{"type": "bullets", "items": items}]
    _merge_bullets("04", "perf")
    _merge_bullets("05", "reliability")
    notes = parsed.get("focal_notes")
    if isinstance(notes, dict):
        for sec in feature["sections"]:
            for b in sec["blocks"]:
                if b["type"] == "code":
                    for ln in b["lines"]:
                        note = _clean_str(notes.get(str(ln["ln"])), 200)
                        if note:
                            ln["note"] = note
    feature["doc_md"] = _assemble_doc_md(feature)


# ---------------------------------------------------------------------------
# 组装
# ---------------------------------------------------------------------------

def _project_summary_structural(G, flows, communities) -> str:
    n_flows = len(flows)
    return (
        f"共 {G.number_of_nodes()} 个节点、{G.number_of_edges()} 条关系、{len(communities or {})} 个社区。"
        f"识别出 {n_flows} 条业务流，可从「业务流视角」开始阅读，再进入「特性下钻」看深度分析。"
    )


def build_learn_data(
    G,
    communities: dict[int, list[str]],
    *,
    root: Path,
    community_labels: dict[int, str] | None = None,
    backend: str | None = None,
    model: str | None = None,
    max_nodes: int = 120,
    previous: dict | None = None,
    usage_out: dict | None = None,
) -> dict:
    """生成 learn.json v2 数据。backend 为 None/""/"none" 时纯结构化（零 LLM）。"""
    root = Path(root)
    callers, callees = _dep_maps(G)
    scores = _node_scores(G, callers, callees)
    spans = _symbol_span_map(G)

    llm_backend = None if backend in (None, "", "none") else backend
    prev = previous if isinstance(previous, dict) and previous.get("version") == LEARN_VERSION else {}
    prev_flows = {f.get("id"): f for f in prev.get("flows", []) if isinstance(f, dict)}
    prev_feats = {f.get("id"): f for f in prev.get("features", []) if isinstance(f, dict)}

    flows = _build_flows(G, callers, callees, scores, root)
    architecture = _build_architecture(G, communities, community_labels, scores, flows)
    features = _build_features(G, flows, root, spans, scores)
    summary = _project_summary_structural(G, flows, communities)

    if llm_backend:
        for flow in flows:
            pf = prev_flows.get(flow["id"])
            if pf and pf.get("fp") == flow["fp"] and pf.get("steps"):
                # 缓存命中：复用上次 LLM 化的名称/叙述，结构字段保持新算。
                flow["name"] = pf.get("name") or flow["name"]
                flow["context"]["intent"] = pf.get("context", {}).get("intent") or flow["context"]["intent"]
                old_steps = pf.get("steps") or []
                for i, s in enumerate(flow["steps"]):
                    if i < len(old_steps) and old_steps[i].get("desc"):
                        s["desc"] = old_steps[i]["desc"]
            else:
                _enhance_flow_llm(flow, backend=llm_backend, model=model, usage_out=usage_out)
        # 架构特性卡名称跟随 LLM 化的流程名。
        by_id = {f["id"]: f for f in flows}
        for card in architecture["features"]:
            f = by_id.get(card["flow_id"])
            if f:
                card["name"] = f["name"]
        for feat in features:
            pf = prev_feats.get(feat["id"])
            if pf and pf.get("fp") == feat["fp"] and pf.get("sections"):
                feat["sections"] = pf["sections"]
                feat["doc_md"] = pf.get("doc_md") or _assemble_doc_md(feat)
            else:
                _enhance_feature_llm(feat, backend=llm_backend, model=model, usage_out=usage_out)
        try:
            raw = _llm_call(_SUMMARY_SYSTEM, backend=llm_backend, model=model,
                            max_tokens=512, usage_out=usage_out)
            parsed = _parse_learn_json(raw)
            s = _clean_str(parsed.get("summary"), 800)
            if s:
                summary = s
        except Exception as exc:  # noqa: BLE001
            print(f"[graphify learn] 概览增强失败，保留结构化描述: {exc}", file=sys.stderr)

    data = {
        "version": LEARN_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "backend": llm_backend or "none",
        "project_summary": summary,
        "flows": flows,
        "architecture": architecture,
        "features": features,
    }
    # 内部字段（path/involved_files/fp）不进 sidecar。
    for flow in data["flows"]:
        flow.pop("path", None)
    for feat in data["features"]:
        feat.pop("involved_files", None)
    return data


# ---------------------------------------------------------------------------
# CLI 入口：graphify learn [PATH] [flags]
# ---------------------------------------------------------------------------

_LEARN_USAGE = """Usage: graphify learn [PATH] [--graph PATH] [--backend B] [--model M]
                      [--no-llm] [--force]

为 graph.html 的「学习」页签生成多视角学习内容（业务流 / 代码架构 / 特性下钻），
写入 <root>/.graph/learn.json 与 <root>/.graph/features/*.md，并重新导出 graph.html。

  PATH          项目根目录（默认当前目录）
  --graph PATH  显式指定 graph.json 路径
  --backend B   LLM 后端（claude/kimi/ollama/gemini/openai/deepseek/...）
  --model M     覆盖后端默认模型
  --no-llm      纯结构化模式（零 LLM 成本，只出确定性内容）
  --force       忽略增量缓存，全部重新生成"""


def run_learn(argv: list[str]) -> None:
    import networkx as nx

    root_arg = "."
    graph_arg: str | None = None
    backend_arg: str | None = None
    model_arg: str | None = None
    no_llm = False
    force = False

    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("-h", "--help"):
            print(_LEARN_USAGE)
            return
        elif a == "--graph" and i + 1 < len(argv):
            graph_arg = argv[i + 1]; i += 2
        elif a == "--backend" and i + 1 < len(argv):
            backend_arg = argv[i + 1]; i += 2
        elif a == "--model" and i + 1 < len(argv):
            model_arg = argv[i + 1]; i += 2
        elif a == "--no-llm":
            no_llm = True; i += 1
        elif a == "--force":
            force = True; i += 1
        elif not a.startswith("-") and root_arg == ".":
            root_arg = a; i += 1
        else:
            print(f"未知参数: {a}", file=sys.stderr)
            print(_LEARN_USAGE, file=sys.stderr)
            sys.exit(1)

    graph_path = Path(graph_arg) if graph_arg else Path(root_arg) / ".graph" / "graph.json"
    graph_path = graph_path.resolve()
    if not graph_path.is_file():
        print(
            f"未找到 {graph_path}。先运行 /graphify（或 graphify extract）建图。",
            file=sys.stderr,
        )
        sys.exit(1)

    out_dir = graph_path.parent
    root = out_dir.parent if out_dir.name == ".graph" else out_dir

    raw = json.loads(graph_path.read_text(encoding="utf-8"))
    if "links" not in raw and "edges" in raw:
        raw = dict(raw, links=raw["edges"])
    try:
        G = nx.node_link_graph(raw, edges="links")
    except TypeError:
        G = nx.node_link_graph(raw)

    communities: dict[int, list[str]] = {}
    analysis_path = out_dir / ".graphify_analysis.json"
    if analysis_path.exists():
        try:
            _an = json.loads(analysis_path.read_text(encoding="utf-8"))
            communities = {int(k): v for k, v in _an.get("communities", {}).items()}
        except (OSError, ValueError):
            communities = {}
    if not communities:
        for node_id, data in G.nodes(data=True):
            cid_raw = (data or {}).get("community")
            if cid_raw is None:
                continue
            try:
                communities.setdefault(int(cid_raw), []).append(str(node_id))
            except (TypeError, ValueError):
                continue

    labels: dict[int, str] = {}
    labels_path = out_dir / ".graphify_labels.json"
    if labels_path.exists():
        try:
            labels = {int(k): v for k, v in json.loads(labels_path.read_text(encoding="utf-8")).items()}
        except (OSError, ValueError):
            labels = {}

    backend = backend_arg
    if not no_llm and not backend:
        try:
            from graphify.llm import detect_backend
            backend = detect_backend()
        except Exception:  # noqa: BLE001
            backend = None
        if not backend:
            print("提示：未检测到可用的 LLM 后端，使用纯结构化模式（--no-llm 等效）。")
    if no_llm:
        backend = None

    previous = None
    sidecar = out_dir / LEARN_SIDECAR_NAME
    if sidecar.exists() and not force:
        previous = load_learn_sidecar(sidecar) or None

    usage: dict = {}
    data = build_learn_data(
        G, communities,
        root=root,
        community_labels=labels or None,
        backend=backend,
        model=model_arg,
        previous=previous,
        usage_out=usage if backend else None,
    )

    sidecar.write_text(
        json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    # 特性文档落盘为 .md（可直接进 wiki / 评审）。
    feats_dir = out_dir / FEATURES_DIR_NAME
    feats_dir.mkdir(parents=True, exist_ok=True)
    for old in feats_dir.glob("*.md"):
        old.unlink()
    for feat in data["features"]:
        (feats_dir / f"{feat['id']}.md").write_text(feat["doc_md"], encoding="utf-8")

    print(
        f"learn.json 写入完成：{len(data['flows'])} 条业务流、"
        f"{len(data['architecture']['tree'])} 行目录树、"
        f"{len(data['architecture']['features'])} 张特性卡、"
        f"{len(data['features'])} 篇特性文档（.graph/features/*.md），后端 {data['backend']}。"
    )
    if usage:
        print(f"LLM 用量：输入 {usage.get('input', 0)} tokens，输出 {usage.get('output', 0)} tokens。")

    # 重新导出 graph.html，带上学习数据。
    try:
        from graphify.export import to_html as _to_html
        from graphify.cli import _load_review_queue
        _rq = _load_review_queue(out_dir)
        _to_html(
            G, communities, str(out_dir / "graph.html"),
            community_labels=labels or None,
            review_queue=_rq,
            learn_data=data,
        )
        print("graph.html 已更新（学习页签已注入多视角内容）。")
    except Exception as exc:  # noqa: BLE001 — HTML 失败不丢 sidecar
        print(f"警告：graph.html 重新导出失败（{exc}）。learn.json 已保留，可稍后运行 graphify export html。", file=sys.stderr)
