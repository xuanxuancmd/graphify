"""学习模式内容生成（learn.json sidecar v3 —— 多视角 + 难度分层 + 导览）。

graph.html「学习」页签的数据源，面向**人类读者**：AI 生成或遗留的代码
让人看不懂、无法检视和维护。v3 在 v2 多视角基础上增加：

  难度分层      确定性信号（调用深度 / 跨模块数 / 控制流密度 / 异常密度）
               → 难度等级（simple/standard/complex）→ 特性文档按需生成节。
  项目导览      社区依赖 DAG 的 Kahn 拓扑排序 → 步骤式导览。
  领域视角      三层降级：DDD doc-anchor > 社区聚类 > LLM 增强。
  节点注解      LLM 为 top-N 高分节点附语言/模式教学注解（可选）。

v3 视角组织：
  业务流视角    从入口沿调用链走出的主路径：Mermaid 时序图 + 分步讲解
               + 当前步骤的符号上下文与代码锚点。
  代码架构视角  目录结构（按文件/目录聚合）+ 关键特性卡 + 基础类图。
  特性下钻视角  每个特性一篇深度分析文档（按难度分层：简单 2 节 / 标准 4 节
               / 复杂 6 节 + 按需 UML），全部锚到代码。

管线遵循 Swimm 式「先确定性、后生成」：时序图、类图、目录树、调用
统计、焦点行、抛错点、TODO 扫描全部从 graph.json + 源码确定性推导；
LLM（可选）只做最后的散文化（流程讲解、技术点命名、性能/可靠性叙
述、焦点行注释）。零 LLM 时输出纯结构化内容 —— 仍然完整可用。

增量缓存：业务流/特性/难度判定/领域描述/节点注解按涉及文件 SHA256
指纹缓存，未变更不重生成。CLI（run_learn）额外把每篇特性文档落盘
到 .graph/features/<id>.md。
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LEARN_SIDECAR_NAME = "learn.json"
LEARN_VERSION = 3
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

    只认 v3（多视角 + 难度分层 schema）；v1/v2 或损坏数据一律视为空，
    前端提示重新生成。
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
    if node_type in {"endpoint", "rest_endpoint", "route", "api", "handler", "controller"}:
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
        if str(data.get("node_kind") or "") in ("endpoint", "rest_endpoint") or re.match(r"^(GET|POST|PUT|DELETE|PATCH):", str(data.get("label") or "")):
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
    """从 seed 沿调用链贪心走主路径，产出时序图 + 步骤 + 上下文。

    端点种子（REST endpoint）的第一跳走 ``references`` 边找 handler，
    之后回到 calls/uses 调用链。
    """
    data = G.nodes[seed]
    label = str(data.get("label") or seed)
    node_kind = str(data.get("node_kind") or data.get("node_type") or "").lower()
    is_endpoint = node_kind in ("endpoint", "rest_endpoint") or bool(re.match(r"^(GET|POST|PUT|DELETE|PATCH):", label))

    # 首跳邻接：端点 → references 指向的符号（优先函数；类无调用出边，
    # 会截断走链）；普通种子直接用调用链。
    first_callees: set[str] = set()
    if is_endpoint:
        fn_refs: set[str] = set()
        other_refs: set[str] = set()
        for u, v, edata in G.edges(seed, data=True):
            tgt = str(edata.get("_tgt", v)) if str(edata.get("_src", u)) == str(seed) else str(edata.get("_src", u))
            if edata.get("relation") == "references" and tgt in G:
                if _kind_of(G.nodes[tgt]) == "function":
                    fn_refs.add(tgt)
                elif _kind_of(G.nodes[tgt]) in ("function", "class"):
                    other_refs.add(tgt)
        first_callees = fn_refs or other_refs
    if not first_callees:
        first_callees = set(callees.get(seed, ()))

    # 主路径：每步走分数最高的未访问 callee；装配/入口类文件
    # （config/app/main/index/server/routes）降权，让叙述留在领域层。
    def _walk_penalty(nid: str) -> int:
        sf = str(G.nodes[nid].get("source_file") or "").lower()
        return 1 if any(k in sf for k in ("config", "app.", "main.", "index.", "server", "routes")) else 0

    path: list[str] = [seed]
    visited = {seed}
    cur = seed
    first = True
    while len(path) <= _MAX_FLOW_MESSAGES:
        pool = first_callees if first else {c for c in callees.get(cur, ()) if c in G}
        nexts = [c for c in pool if c not in visited and _kind_of(G.nodes[c]) in ("function", "class")]
        first = False
        if not nexts:
            break
        nexts.sort(key=lambda n: (_walk_penalty(n), -scores.get(n, 0.0), str(G.nodes[n].get("label") or n)))
        cur = nexts[0]
        visited.add(cur)
        path.append(cur)

    # 运行时路径：端点种子自身（API spec）不作为参与者，从 handler 起。
    rt_path = path[1:] if is_endpoint and len(path) > 1 else path

    # 参与者：按文件聚合（同文件多函数折叠为一个 participant）。
    participants: list[str] = []
    part_of: dict[str, str] = {}
    for nid in rt_path:
        stem = _stem(str(G.nodes[nid].get("source_file") or ""))
        if stem not in part_of:
            part_of[stem] = stem
            participants.append(stem)
    if not participants:
        return None

    # mermaid 时序图。
    lines = ["sequenceDiagram", "    autonumber"]
    for i, p in enumerate(participants, 1):
        lines.append(f"    participant P{i} as {_mermaid_safe(p)}")
    entry_txt = label.replace(":", " ") if is_endpoint else f"调用 {label}()"
    lines.append(f"    Client ->> P1: {_mermaid_safe(entry_txt)}")
    prev_p = 1
    for nid in rt_path:
        stem = _stem(str(G.nodes[nid].get("source_file") or ""))
        pi = participants.index(stem) + 1
        fn_label = str(G.nodes[nid].get("label") or "")
        fn_name = fn_label[:-2] if fn_label.endswith("()") else fn_label
        if pi != prev_p:
            lines.append(f"    P{prev_p} ->> P{pi}: {_mermaid_safe(fn_name)}()")
        prev_p = pi
    mermaid = "\n".join(lines)

    # 步骤。
    steps: list[dict] = []
    edge_count = 0
    prev_p = 1
    prev_nid = None
    for nid in rt_path:
        ndata = G.nodes[nid]
        stem = _stem(str(ndata.get("source_file") or ""))
        pi = participants.index(stem) + 1
        fn_label = str(ndata.get("label") or "")
        fn_name = fn_label[:-2] if fn_label.endswith("()") else fn_label
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
            desc = _first_desc_line(ndata) or f"{fn_name} 被调用。"
            steps.append({
                "msg": f"{participants[prev_p - 1]} → {stem} · {fn_name}()",
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


def _mermaid_ident(s: str) -> str:
    """classDiagram 标识符清洗：仅字母数字下划线（点号会导致解析失败）。"""
    ident = re.sub(r"[^A-Za-z0-9_]", "_", str(s or "").strip(". "))
    return ident.strip("_")[:40] or "X"


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
        name = _mermaid_ident(str(G.nodes[c].get("label") or "Cls"))
        method_lines = []
        shown = 0
        for m in methods_of.get(c, []):
            if shown >= _MAX_METHODS_PER_CLASS:
                break
            method_lines.append(f"        +{_mermaid_ident(str(G.nodes[m].get('label') or 'm'))}()")
            shown += 1
        if method_lines:
            lines.append(f"    class {name} {{")
            lines.extend(method_lines)
            lines.append("    }")
        else:
            # 空类体 `class X {}` 是 classDiagram 语法错误 —— 无方法时省略花括号。
            lines.append(f"    class {name}")

    # 类间关系：A 的方法调用 B 的方法 → A --> B。
    class_by_file: dict[str, str] = {}
    for c in classes:
        class_by_file[str(G.nodes[c].get("source_file") or "")] = _mermaid_ident(str(G.nodes[c].get("label") or "Cls"))
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

def _symbol_span_map(G, root: Path) -> dict[str, tuple[str, int, int]]:
    """function/class 节点 → (source_file, start_line, 近似跨度)。

    跨度 = 下一符号声明行 - 当前行；文件最后一个符号回退为文件总行数
    （可读时），保证抛错/TODO 扫描能覆盖函数体到文件尾。
    """
    by_file: dict[str, list[tuple[int, str]]] = {}
    for nid, data in G.nodes(data=True):
        if not isinstance(data, dict) or _kind_of(data) not in ("function", "class"):
            continue
        sf = str(data.get("source_file") or "")
        ln = _line_of(data)
        if sf and ln > 0:
            by_file.setdefault(sf, []).append((ln, nid))
    file_len: dict[str, int] = {}
    for sf in by_file:
        lines = _read_lines(root, sf)
        if lines is not None:
            file_len[sf] = len(lines)
    out: dict[str, tuple[str, int, int]] = {}
    for sf, items in by_file.items():
        items.sort()
        for i, (ln, nid) in enumerate(items):
            nxt = items[i + 1][0] if i + 1 < len(items) else file_len.get(sf, ln + 12)
            out[nid] = (sf, ln, max(1, nxt - ln))
    return out


def _simple_inline(s: str) -> str:
    """结构化叙述里允许的极小 html：strong/code。"""
    return _clean_str(s, 800)


# ---------------------------------------------------------------------------
# 难度信号收集（零 LLM，纯确定性）
# ---------------------------------------------------------------------------

_ENTRY_TYPE_PATTERNS = [
    (re.compile(r"^(GET|POST|PUT|DELETE|PATCH):", re.I), "http"),
    (re.compile(r"^(GET|POST|PUT|DELETE|PATCH)\s+/", re.I), "http"),
    (re.compile(r"\b(cli|command|cmd)\b", re.I), "cli"),
    (re.compile(r"\b(event|listen|on_)\b", re.I), "event"),
    (re.compile(r"\b(cron|schedule|job)\b", re.I), "cron"),
]


def _infer_entry_type(entry: str) -> str:
    """从 flow entry 字符串推断入口类型。"""
    for pat, etype in _ENTRY_TYPE_PATTERNS:
        if pat.search(entry):
            return etype
    return "manual"


def _collect_difficulty_signals(G, flow: dict, spans: dict, scores: dict, root: Path) -> dict:
    """收集难度信号（零 LLM，纯确定性）。

    返回 ``{"score": float, "signals": {...}}``，score 归一化到 0-100。
    """
    path = flow.get("path") or []
    if not path:
        return {"score": 0.0, "signals": {"entry_type": _infer_entry_type(flow.get("entry", ""))}}

    call_depth = len(path)
    cross_modules = len(flow.get("participants", []))

    # control_flow_density: 对 path 中每个符号统计 if/for/while/switch/case/match/try/except/catch/throw/raise 关键词密度
    total_keywords = 0
    total_code_lines = 0
    for nid in path:
        if nid not in spans:
            continue
        sf, ln, span = spans[nid]
        lines = _read_lines(root, sf)
        if lines is None:
            continue
        end = min(len(lines), ln - 1 + max(span, 1))
        for idx in range(ln - 1, end):
            text = lines[idx]
            stripped = text.strip()
            if not stripped:
                continue
            total_code_lines += 1
            padded = " " + stripped + " "
            for kw in _FOCUS_KEYWORDS:
                total_keywords += 2 * (padded.count(f" {kw} ") + padded.count(f" {kw}("))
    control_flow_density = total_keywords / max(total_code_lines, 1)

    # exception_density: throw/raise 行数总和 ÷ 总代码跨度
    total_throw = 0
    total_span = 0
    for nid in path:
        if nid not in spans:
            continue
        sf, ln, span = spans[nid]
        total_span += span
        for hit in _scan_throw_lines(root, sf, ln, span, cap=999):
            total_throw += 1
    exception_density = total_throw / max(total_span, 1)

    # code_lines: path 中所有符号的代码跨度总和
    code_lines = sum(spans[nid][2] for nid in path if nid in spans)

    # focal_line_count: 对 path 中每个符号调 _structural_focal_lines，统计命中总数
    focal_line_count = 0
    for nid in path:
        if nid not in spans:
            continue
        sf, ln, span = spans[nid]
        focal_line_count += len(_structural_focal_lines(root, sf, ln, span))

    entry_type = _infer_entry_type(flow.get("entry", ""))

    signals = {
        "call_depth": call_depth,
        "cross_modules": cross_modules,
        "control_flow_density": round(control_flow_density, 4),
        "exception_density": round(exception_density, 4),
        "code_lines": code_lines,
        "focal_line_count": focal_line_count,
        "entry_type": entry_type,
    }

    raw = (
        call_depth * 0.25
        + cross_modules * 0.25
        + control_flow_density * 10
        + exception_density * 10
    )
    score = min(100.0, max(0.0, raw))
    return {"score": round(score, 2), "signals": signals}


def _build_uml_block(uml_type: str, G, flow: dict, path: list, participants: list, spans: dict, root: Path) -> str:
    """按 UML 类型生成对应的 mermaid 源码。"""
    if uml_type == "sequence":
        return flow.get("mermaid", "")
    if uml_type == "class":
        lines = ["classDiagram"]
        classes = [nid for nid in path if _kind_of(G.nodes.get(nid, {})) == "class"]
        if not classes:
            return ""
        for nid in classes[:5]:
            name = _mermaid_ident(str(G.nodes[nid].get("label") or "Cls"))
            lines.append(f"    class {name}")
        return "\n".join(lines)
    if uml_type == "module_dep":
        lines = ["graph LR"]
        seen: set[str] = set()
        for p in participants:
            ident = _mermaid_ident(p)
            if ident not in seen:
                seen.add(ident)
                lines.append(f"    {ident}({p})")
        for i in range(len(path) - 1):
            src = _stem(str(G.nodes[path[i]].get("source_file") or ""))
            tgt = _stem(str(G.nodes[path[i + 1]].get("source_file") or ""))
            if src != tgt:
                lines.append(f"    {_mermaid_ident(src)} --> {_mermaid_ident(tgt)}")
        return "\n".join(lines)
    if uml_type == "state":
        lines = ["stateDiagram-v2"]
        lines.append("    [*] --> Normal")
        has_error = False
        for nid in path:
            if nid not in spans:
                continue
            sf, ln, span = spans[nid]
            if _scan_throw_lines(root, sf, ln, span, cap=1):
                has_error = True
                break
        if has_error:
            lines.append("    Normal --> Error: 异常条件触发")
            lines.append("    Error --> [*]: 捕获/传播")
        else:
            lines.append("    Normal --> [*]")
        return "\n".join(lines)
    if uml_type == "flowchart":
        lines = ["flowchart TD"]
        lines.append("    Start([开始])")
        for i, nid in enumerate(path):
            label = _mermaid_safe(str(G.nodes[nid].get("label") or f"step{i}"))
            lines.append(f"    S{i}[{label}]")
        lines.append("    End([结束])")
        lines.append("    Start --> S0")
        for i in range(len(path) - 1):
            lines.append(f"    S{i} --> S{i + 1}")
        if path:
            lines.append(f"    S{len(path) - 1} --> End")
        return "\n".join(lines)
    return ""


def _build_feature_doc(G, flow: dict, root: Path, spans: dict, scores, *, difficulty: str | None = None, uml_needed: list | None = None) -> dict | None:
    """确定性组装特性下钻文档。

    difficulty/uml_needed 可选，默认 None 时退化为当前行为（生成全部六节）。
    - simple: 01 概览 + 06 已知限制
    - standard: 01 + 02 + 03（时序图按需）+ 06
    - complex: 完整 01-06 + 按需 UML 组合
    """
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

    uml_list = list(uml_needed) if uml_needed else []
    cross_modules = len(participants)

    # 确定要构建的节
    if difficulty is None:
        build_set = {"01", "02", "03", "04", "05", "06"}
    elif difficulty == "simple":
        build_set = {"01", "06"}
    elif difficulty == "standard":
        build_set = {"01", "02", "03", "06"}
    else:  # complex
        build_set = {"01", "02", "03", "04", "05", "06"}

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
    sec3_blocks: list[dict] = []
    # 时序图：默认包含；standard 仅当 uml_needed 含 sequence 或 cross_modules>=2 时才加
    include_sequence = (
        difficulty is None
        or difficulty == "complex"
        or "sequence" in uml_list
        or cross_modules >= 2
    )
    if include_sequence:
        sec3_blocks.append({"type": "mermaid", "src": flow["mermaid"]})
    # 代码走读对象：优先选有焦点行（关键算法信号）的符号，否则最高分。
    core = None
    core_focal: list[dict] = []
    for cand in sorted(path, key=lambda n: -scores.get(n, 0.0))[:3]:
        if cand not in spans:
            continue
        csf, cln, cspan = spans[cand]
        focal = _structural_focal_lines(root, csf, cln, cspan)
        if focal:
            core, core_focal = cand, focal
            break
        if core is None:
            core = cand
    if core is None:
        core = max(path, key=lambda n: scores.get(n, 0.0))
    if core in spans:
        sf, ln, span = spans[core]
        focal = core_focal or _structural_focal_lines(root, sf, ln, span)
        excerpt = _code_excerpt(root, sf, ln, span, focal)
        if excerpt:
            sec3_blocks.append({
                "type": "code", "file": sf, "start": ln, "end": excerpt["end"],
                "tier": "关键算法" if focal else "契约级",
                "lines": excerpt["lines"],
                "fn": str(G.nodes[core].get("label") or core),
            })
    # 复杂难度：按需追加 UML 块
    if difficulty == "complex":
        for utype in uml_list:
            if utype == "sequence":
                continue  # 已在上方加入
            uml_src = _build_uml_block(utype, G, flow, path, participants, spans, root)
            if uml_src:
                sec3_blocks.append({"type": "mermaid", "src": uml_src, "uml_type": utype})

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

    # 按难度组装实际节列表
    section_defs = [
        ("01", "特性概览", sec1_blocks),
        ("02", "关键技术点", sec2_blocks),
        ("03", "核心实现", sec3_blocks),
        ("04", "性能设计", sec4_blocks),
        ("05", "可靠性设计", sec5_blocks),
        ("06", "已知限制与验证", sec6_blocks),
    ]
    sections = [{"no": no, "title": title, "blocks": blocks} for no, title, blocks in section_defs if no in build_set]

    feature = {
        "id": "feat_" + flow["id"].removeprefix("flow_"),
        "name": flow["name"],
        "flow_id": flow["id"],
        "sections": sections,
        "outline": [{"no": s["no"], "title": s["title"]} for s in sections],
        "anchors": anchors[:14],
        "involved_files": involved_files,
        "difficulty": difficulty,
        "uml_needed": uml_list,
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
                if b.get("uml_type"):
                    out.append(f"_{b['uml_type']} 图_：")
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


def _build_features(G, flows, root: Path, spans, scores, *, difficulty_map: dict | None = None) -> list[dict]:
    feats = []
    dmap = difficulty_map or {}
    for flow in flows:
        diff_info = dmap.get(flow["id"], {})
        f = _build_feature_doc(G, flow, root, spans, scores,
                               difficulty=diff_info.get("difficulty"),
                               uml_needed=diff_info.get("uml_needed"))
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
# v3 LLM 增强：难度判定 + 节点注解
# ---------------------------------------------------------------------------

_DIFFICULTY_SYSTEM = """你在评估一个代码业务流的难度，并选择需要的 UML 图类型。

可选 UML 类型：
- sequence（时序图）：跨模块调用时序
- class（类图）：类继承与组合关系
- module_dep（模块依赖图）：文件/模块间依赖
- state（状态转移图）：状态机或异常流转
- flowchart（流程图）：控制流分支

只输出 JSON（无 markdown 代码块）：
{"difficulty": "simple"|"standard"|"complex", "uml_needed": ["sequence", ...], "reason": "..."}"""

_NODE_NOTES_SYSTEM = """你在为代码库的高分节点写教学注解。下面是若干节点（label/source_file/desc/代码片段）。
为每个节点返回一句话中文教学注解（1-2 句），点出语言特性或设计模式，不复述函数名。

只输出 JSON（无 markdown 代码块）：
{"notes": {"node_id_1": "注解...", "node_id_2": "注解..."}}"""

_VALID_UML_TYPES = frozenset({"sequence", "class", "module_dep", "state", "flowchart"})


def _difficulty_fallback(signals: dict) -> dict:
    """零 LLM / LLM 失败时的固定权重退化判定。"""
    score = signals.get("score", 0.0)
    sig = signals.get("signals", {})
    if score >= 66:
        difficulty = "complex"
    elif score >= 33:
        difficulty = "standard"
    else:
        difficulty = "simple"
    uml: list[str] = []
    cross = sig.get("cross_modules", 0)
    if cross >= 2:
        uml.append("sequence")
    if cross >= 3:
        uml.append("module_dep")
    if sig.get("exception_density", 0) > 0.05 or sig.get("focal_line_count", 0) > 8:
        uml.append("state")
    if sig.get("control_flow_density", 0) > 0.3:
        uml.append("flowchart")
    return {"difficulty": difficulty, "uml_needed": uml, "reason": "结构化启发式判定"}


def _difficulty_prompt(flow: dict, signals: dict) -> str:
    sig = signals.get("signals", {})
    lines = [_DIFFICULTY_SYSTEM, "", f"特性：{flow.get('name', '')}（入口 {flow.get('entry', '')}）", ""]
    lines.append(f"难度分数：{signals.get('score', 0)}/100")
    lines.append(f"  call_depth={sig.get('call_depth', 0)}")
    lines.append(f"  cross_modules={sig.get('cross_modules', 0)}")
    lines.append(f"  control_flow_density={sig.get('control_flow_density', 0)}")
    lines.append(f"  exception_density={sig.get('exception_density', 0)}")
    lines.append(f"  code_lines={sig.get('code_lines', 0)}")
    lines.append(f"  focal_line_count={sig.get('focal_line_count', 0)}")
    lines.append(f"  entry_type={sig.get('entry_type', 'manual')}")
    return "\n".join(lines)


def _judge_difficulty_ai(flow: dict, signals: dict, backend=None, model=None, usage_out=None) -> dict:
    """LLM 难度判断 + UML 选型。零 LLM 时用固定权重退化。"""
    llm_backend = None if backend in (None, "", "none") else backend
    if not llm_backend:
        return _difficulty_fallback(signals)
    try:
        raw = _llm_call(_difficulty_prompt(flow, signals), backend=llm_backend, model=model,
                        max_tokens=512, usage_out=usage_out)
        parsed = _parse_learn_json(raw)
        difficulty = str(parsed.get("difficulty") or "").strip().lower()
        if difficulty not in ("simple", "standard", "complex"):
            difficulty = "standard"
        uml_raw = parsed.get("uml_needed")
        uml: list[str] = []
        if isinstance(uml_raw, list):
            uml = [str(u).strip() for u in uml_raw if str(u).strip() in _VALID_UML_TYPES]
        reason = _clean_str(parsed.get("reason"), 400) or "LLM 判定"
        return {"difficulty": difficulty, "uml_needed": uml, "reason": reason}
    except Exception as exc:  # noqa: BLE001
        print(f"[graphify learn] 难度判定失败，退化为结构化: {exc}", file=sys.stderr)
        result = _difficulty_fallback(signals)
        result["reason"] = f"LLM 失败，结构化退化: {exc}"
        return result


def _build_node_notes(G, scores: dict, *, backend=None, model=None, usage_out=None, top_n=20) -> dict[str, str]:
    """LLM 为 top-N 高分节点附语言/模式教学注解。backend 为 None 时返回 {}。"""
    llm_backend = None if backend in (None, "", "none") else backend
    if not llm_backend:
        return {}
    sorted_nodes = sorted(scores.items(), key=lambda x: -x[1])[:top_n]
    if not sorted_nodes:
        return {}
    lines = [_NODE_NOTES_SYSTEM, ""]
    for nid, _score in sorted_nodes:
        data = G.nodes.get(nid, {})
        if not isinstance(data, dict):
            continue
        label = str(data.get("label") or nid)
        sf = str(data.get("source_file") or "")
        desc = str(data.get("desc") or "")[:200]
        ln = _line_of(data)
        lines.append(f"节点 {nid}:")
        lines.append(f"  label: {label}")
        lines.append(f"  source_file: {sf}")
        if ln:
            lines.append(f"  line: L{ln}")
        if desc:
            lines.append(f"  desc: {desc}")
        lines.append("")
    prompt = "\n".join(lines)
    try:
        raw = _llm_call(prompt, backend=llm_backend, model=model, max_tokens=2048, usage_out=usage_out)
        parsed = _parse_learn_json(raw)
        notes = parsed.get("notes")
        if not isinstance(notes, dict):
            return {}
        result: dict[str, str] = {}
        for nid, _ in sorted_nodes:
            note = _clean_str(notes.get(nid), 300)
            if note:
                result[nid] = note
        return result
    except Exception as exc:  # noqa: BLE001
        print(f"[graphify learn] 节点注解生成失败: {exc}", file=sys.stderr)
        return {}


# ---------------------------------------------------------------------------
# 组装
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# v3 视角：项目导览 / 社区导览 / 领域视角
# ---------------------------------------------------------------------------

_DEP_FILES = {
    "requirements.txt": "Python",
    "pyproject.toml": "Python",
    "package.json": "Node.js",
    "go.mod": "Go",
    "Cargo.toml": "Rust",
}
_EXT_TO_LANG = {
    ".py": "Python", ".ts": "TypeScript", ".tsx": "TypeScript",
    ".js": "JavaScript", ".jsx": "JavaScript", ".go": "Go",
    ".rs": "Rust", ".java": "Java", ".c": "C", ".cpp": "C++",
    ".rb": "Ruby", ".cs": "C#", ".kt": "Kotlin", ".swift": "Swift",
    ".php": "PHP", ".scala": "Scala", ".lua": "Lua", ".sh": "Shell",
    ".zig": "Zig", ".dart": "Dart",
}
_FRAMEWORK_PATTERNS = [
    (re.compile(r"\bfastapi\b"), "FastAPI"),
    (re.compile(r"\bflask\b"), "Flask"),
    (re.compile(r"\bdjango\b"), "Django"),
    (re.compile(r"\bexpress\b"), "Express"),
    (re.compile(r"\bgin-gonic\b|\"gin/"), "Gin"),
    (re.compile(r"\bactix\b"), "Actix"),
    (re.compile(r"\baxum\b"), "Axum"),
]


def _build_project_overview(G, communities: dict, community_labels: dict | None, flows: list, root: Path) -> dict:
    """返回 ``{"dir_structure", "feature_intro", "entry_points", "tech_stack"}``。"""
    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()
    n_comm = len(communities)
    n_flows = len(flows)

    callers, callees = _dep_maps(G)
    scores = _node_scores(G, callers, callees)
    tree = _build_tree(G, scores)[:15]

    entry_hints = [f.get("entry", "") for f in flows[:3]]
    entry_str = "、".join(e for e in entry_hints if e) or "（未识别）"
    feature_intro = (
        f"共 {n_nodes} 节点 {n_edges} 边 {n_comm} 社区。"
        f"识别 {n_flows} 条业务流，核心入口：{entry_str}。"
        f"建议从「项目导览」开始。"
    )

    entry_points: list[dict] = []
    for nid, data in G.nodes(data=True):
        if not isinstance(data, dict):
            continue
        label = str(data.get("label") or "")
        node_kind = str(data.get("node_kind") or data.get("node_type") or "").lower()
        is_ep = node_kind in ("endpoint", "rest_endpoint") or bool(re.match(r"^(GET|POST|PUT|DELETE|PATCH):", label))
        is_handler = bool(_ENTRY_FUNC_RE.match(label))
        if not (is_ep or is_handler):
            continue
        if is_ep or re.match(r"^(GET|POST|PUT|DELETE|PATCH):", label):
            ep_type = "http"
        elif re.search(r"\b(cli|command|cmd)\b", label, re.I):
            ep_type = "cli"
        elif re.search(r"\b(event|listen|on_)\b", label, re.I):
            ep_type = "event"
        elif re.search(r"\b(cron|schedule|job)\b", label, re.I):
            ep_type = "cron"
        else:
            ep_type = "manual"
        sf = str(data.get("source_file") or "")
        ln = _line_of(data)
        entry_points.append({
            "type": ep_type,
            "path": f"{sf} L{ln}" if sf and ln else sf,
            "handler": label,
        })

    # tech_stack: 从文件扩展名 + 依赖配置文件推导
    tech_stack: list[str] = []
    ext_counts: dict[str, int] = {}
    for nid, data in G.nodes(data=True):
        if not isinstance(data, dict):
            continue
        sf = str(data.get("source_file") or "")
        if not sf:
            continue
        sf_lower = sf.lower()
        for ext in _CODE_EXTS:
            if sf_lower.endswith(ext):
                ext_counts[ext] = ext_counts.get(ext, 0) + 1
                break
    # 只取 top-5 主语言（按文件数），避免大图列出十几种语言
    for ext, _count in sorted(ext_counts.items(), key=lambda x: -x[1])[:5]:
        lang = _EXT_TO_LANG.get(ext)
        if lang and lang not in tech_stack:
            tech_stack.append(lang)
    for dep_file, lang in _DEP_FILES.items():
        if (root / dep_file).is_file() and lang not in tech_stack:
            tech_stack.append(lang)
    # 框架检测
    for dep_file in _DEP_FILES:
        p = root / dep_file
        if not p.is_file():
            continue
        try:
            content = p.read_text(encoding="utf-8", errors="replace").lower()
        except OSError:
            continue
        for pat, name in _FRAMEWORK_PATTERNS:
            if pat.search(content) and name not in tech_stack:
                tech_stack.append(name)

    return {
        "dir_structure": tree,
        "feature_intro": feature_intro,
        "entry_points": entry_points[:20],
        "tech_stack": tech_stack,
    }


def _build_tour(G, communities: dict, community_labels: dict | None, scores: dict) -> list[dict]:
    """Kahn 拓扑排序社区，生成项目级导览。"""
    if not communities:
        return []

    node_to_comm: dict[str, int] = {}
    for cid, nodes in communities.items():
        for nid in nodes:
            node_to_comm[str(nid)] = cid

    # 社区依赖 DAG：A 的节点调用 B 的节点 → A→B
    comm_adj: dict[int, set[int]] = {cid: set() for cid in communities}
    comm_indeg: dict[int, int] = {cid: 0 for cid in communities}
    for u, v, data in G.edges(data=True):
        if not isinstance(data, dict) or data.get("relation") not in _DEP_RELATIONS:
            continue
        src = str(data.get("_src", u))
        tgt = str(data.get("_tgt", v))
        src_comm = node_to_comm.get(src)
        tgt_comm = node_to_comm.get(tgt)
        if src_comm is None or tgt_comm is None or src_comm == tgt_comm:
            continue
        if tgt_comm not in comm_adj[src_comm]:
            comm_adj[src_comm].add(tgt_comm)
            comm_indeg[tgt_comm] += 1

    # Kahn 拓扑排序
    queue = sorted(cid for cid in communities if comm_indeg[cid] == 0)
    order: list[int] = []
    queued: set[int] = set(queue)
    while queue:
        cid = queue.pop(0)
        order.append(cid)
        for nb in sorted(comm_adj[cid]):
            comm_indeg[nb] -= 1
            if comm_indeg[nb] == 0 and nb not in queued:
                queue.append(nb)
                queued.add(nb)
        queue.sort()

    # 环检测：剩余节点按最低分数断边继续
    remaining = [cid for cid in communities if cid not in set(order)]
    if remaining:
        remaining.sort(key=lambda c: sum(scores.get(n, 0.0) for n in communities.get(c, [])))
        order.extend(remaining)

    # 大图社区数可能成百上千，tour 限制为 top-N 最重要社区（5-15 步）。
    _MAX_TOUR_STEPS = 15
    _MIN_TOUR_STEPS = 5
    if len(order) > _MAX_TOUR_STEPS:
        # 按社区总分数排序取 top-N，再恢复拓扑序
        cid_score = {cid: sum(scores.get(n, 0.0) for n in communities.get(cid, [])) for cid in order}
        top = set(sorted(cid_score, key=lambda c: -cid_score[c])[:_MAX_TOUR_STEPS])
        order = [cid for cid in order if cid in top]
    elif len(order) < _MIN_TOUR_STEPS:
        # 不足 5 步时补齐（按分数取后续社区）
        cid_score = {cid: sum(scores.get(n, 0.0) for n in communities.get(cid, [])) for cid in communities}
        extra = [cid for cid in sorted(cid_score, key=lambda c: -cid_score[c]) if cid not in set(order)]
        order.extend(extra[:_MIN_TOUR_STEPS - len(order)])

    tour: list[dict] = []
    for i, cid in enumerate(order):
        nodes = communities.get(cid, [])
        top_nodes = sorted(nodes, key=lambda n: -scores.get(n, 0.0))[:12]
        labels = []
        for nid in top_nodes[:5]:
            nd = G.nodes.get(nid, {})
            if isinstance(nd, dict):
                label = str(nd.get("label") or nid)
                if label:
                    labels.append(label)
        label_str = "、".join(labels) if labels else "（无）"
        title = (community_labels or {}).get(cid) or f"Domain {cid}"
        tour.append({
            "order": i + 1,
            "title": title,
            "desc": f"本模块包含 {len(nodes)} 个节点，核心符号：{label_str}。",
            "nodeIds": top_nodes,
            "community_id": cid,
        })
    return tour


def _build_domains(G, communities: dict, community_labels: dict | None, scores: dict, root: Path, *, backend=None, model=None, usage_out=None) -> list[dict]:
    """三层降级领域视角：DDD doc-anchor > 社区聚类 > LLM 增强。"""
    llm_backend = None if backend in (None, "", "none") else backend

    node_to_comm: dict[str, int] = {}
    for cid, nodes in communities.items():
        for nid in nodes:
            node_to_comm[str(nid)] = cid

    # Tier 1: DDD doc-anchor 节点
    ddd_bc_nodes: list[tuple[str, dict]] = []
    for nid, data in G.nodes(data=True):
        if not isinstance(data, dict):
            continue
        tags = data.get("tags")
        if not isinstance(tags, list):
            continue
        if "ddd" not in tags:
            continue
        if "bounded_context" in tags:
            ddd_bc_nodes.append((nid, data))

    if ddd_bc_nodes:
        domains = _build_domains_ddd(G, ddd_bc_nodes, node_to_comm, communities, community_labels, scores)
    else:
        domains = _build_domains_cluster(G, communities, community_labels, scores, node_to_comm)

    # Tier 3: LLM 增强（可选）—— 在 build_learn_data 中带缓存执行
    if llm_backend and domains:
        _enhance_domains_llm(G, domains, backend=llm_backend, model=model, usage_out=usage_out)
    return domains


def _domains_cache_hit(current: list[dict], prev: list[dict]) -> bool:
    """检查领域结构是否与上次一致（id + community_id + node_count 匹配）。"""
    if not prev or len(current) != len(prev):
        return False
    prev_by_id = {d.get("id"): d for d in prev if isinstance(d, dict)}
    for dom in current:
        pd = prev_by_id.get(dom.get("id"))
        if not pd:
            return False
        if pd.get("community_id") != dom.get("community_id"):
            return False
        if pd.get("node_count") != dom.get("node_count"):
            return False
    return True


_DDD_TYPES = frozenset({
    "bounded_context", "aggregate_root", "domain_event", "invariant",
    "value_object", "domain_service", "contract", "business_flow_step",
    "glossary_term", "tech_constraint", "concept",
})


def _build_domains_ddd(G, bc_nodes: list, node_to_comm: dict, communities: dict, community_labels: dict | None, scores: dict) -> list[dict]:
    """Tier 1: 从 DDD doc-anchor bounded_context 节点构建领域。"""
    domains: list[dict] = []
    for i, (bc_id, bc_data) in enumerate(bc_nodes):
        cid = node_to_comm.get(bc_id, i)
        name = str(bc_data.get("label") or f"Domain {i}")

        key_files: set[str] = set()
        key_symbols: set[str] = set()
        cross_domain_map: dict[tuple, dict] = {}

        for u, v, edata in G.edges(bc_id, data=True):
            if not isinstance(edata, dict):
                continue
            rel = edata.get("relation")
            # 确定边方向：bc_id 出边
            if str(edata.get("_src", u)) == bc_id:
                target = str(edata.get("_tgt", v))
            else:
                target = str(edata.get("_src", u))
            if target not in G:
                continue
            tgt_data = G.nodes[target]
            if not isinstance(tgt_data, dict):
                continue
            tgt_kind = _kind_of(tgt_data)

            if rel == "references":
                # describes → key_files/key_symbols
                sf = str(tgt_data.get("source_file") or "")
                if sf:
                    key_files.add(sf)
                if tgt_kind in ("function", "class"):
                    key_symbols.add(str(tgt_data.get("label") or target))
            elif rel in ("conceptually_related_to", "cites"):
                # cross_domain
                tgt_comm = node_to_comm.get(target, -1)
                if tgt_comm >= 0 and tgt_comm != cid:
                    key = (tgt_comm, rel)
                    if key in cross_domain_map:
                        cross_domain_map[key]["count"] += 1
                    else:
                        cross_domain_map[key] = {"target": f"domain_{tgt_comm}", "via": rel, "count": 1}

        comm_nodes = communities.get(cid, [])
        domains.append({
            "id": f"domain_{i}",
            "name": name,
            "community_id": cid,
            "node_count": len(comm_nodes) or len(key_files) + len(key_symbols),
            "key_files": sorted(key_files)[:10],
            "key_symbols": sorted(key_symbols)[:10],
            "flows": [],
            "cross_domain": list(cross_domain_map.values()),
            "desc": _clean_str(bc_data.get("desc"), 400),
            "source": "ddd",
        })
    return domains


def _build_domains_cluster(G, communities: dict, community_labels: dict | None, scores: dict, node_to_comm: dict) -> list[dict]:
    """Tier 2: 社区聚类 = domain 骨架。"""
    domains: list[dict] = []
    for i, (cid, nodes) in enumerate(sorted(communities.items())):
        name = (community_labels or {}).get(cid) or f"Domain {cid}"
        sorted_nodes = sorted(nodes, key=lambda n: -scores.get(n, 0.0))
        key_files: set[str] = set()
        key_symbols: set[str] = set()
        for nid in sorted_nodes[:20]:
            data = G.nodes.get(nid, {})
            if not isinstance(data, dict):
                continue
            kind = _kind_of(data)
            sf = str(data.get("source_file") or "")
            if kind == "file" and sf:
                key_files.add(sf)
            elif kind in ("function", "class"):
                key_symbols.add(str(data.get("label") or nid))

        cross_domain_map: dict[tuple, dict] = {}
        for nid in nodes:
            for u, v, edata in G.edges(nid, data=True):
                if not isinstance(edata, dict) or edata.get("relation") not in _DEP_RELATIONS:
                    continue
                tgt = str(edata.get("_tgt", v)) if str(edata.get("_src", u)) == nid else str(edata.get("_src", u))
                tgt_comm = node_to_comm.get(tgt, -1)
                if tgt_comm < 0 or tgt_comm == cid:
                    continue
                key = (tgt_comm, edata.get("relation"))
                if key in cross_domain_map:
                    cross_domain_map[key]["count"] += 1
                else:
                    cross_domain_map[key] = {"target": f"domain_{tgt_comm}", "via": edata.get("relation"), "count": 1}

        domains.append({
            "id": f"domain_{i}",
            "name": name,
            "community_id": cid,
            "node_count": len(nodes),
            "key_files": sorted(key_files)[:10],
            "key_symbols": sorted(key_symbols)[:10],
            "flows": [],
            "cross_domain": list(cross_domain_map.values()),
            "desc": "",
            "source": "cluster",
        })
    return domains


_DOMAIN_LLM_SYSTEM = """你在为代码库的领域视角命名并写描述。下面是若干领域（名称/节点数/关键文件/关键符号）。
为每个领域返回一个更贴切的中文名称和 1-2 句描述。

只输出 JSON（无 markdown 代码块）：
{"domains": [{"id": "domain_0", "name": "...", "desc": "..."}, ...]}"""


def _enhance_domains_llm(G, domains: list[dict], *, backend: str, model: str | None, usage_out: dict | None) -> None:
    """Tier 3: LLM 为每 domain 命名 + 写描述。"""
    lines = [_DOMAIN_LLM_SYSTEM, ""]
    for d in domains:
        lines.append(f"领域 {d['id']}（当前名：{d['name']}）:")
        lines.append(f"  node_count: {d['node_count']}")
        lines.append(f"  key_files: {', '.join(d.get('key_files', [])[:5])}")
        lines.append(f"  key_symbols: {', '.join(d.get('key_symbols', [])[:5])}")
        lines.append("")
    prompt = "\n".join(lines)
    try:
        raw = _llm_call(prompt, backend=backend, model=model, max_tokens=2048, usage_out=usage_out)
        parsed = _parse_learn_json(raw)
        llm_domains = parsed.get("domains")
        if not isinstance(llm_domains, list):
            return
        by_id = {d.get("id"): d for d in llm_domains if isinstance(d, dict)}
        for dom in domains:
            llm = by_id.get(dom["id"])
            if not llm:
                continue
            name = _clean_str(llm.get("name"), 80)
            if name:
                dom["name"] = name
            desc = _clean_str(llm.get("desc"), 400)
            if desc:
                dom["desc"] = desc
            if dom.get("source") == "cluster":
                dom["source"] = "llm"
    except Exception as exc:  # noqa: BLE001
        print(f"[graphify learn] 领域 LLM 增强失败: {exc}", file=sys.stderr)


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
    """生成 learn.json v3 数据。backend 为 None/""/"none" 时纯结构化（零 LLM）。"""
    root = Path(root)
    callers, callees = _dep_maps(G)
    scores = _node_scores(G, callers, callees)
    spans = _symbol_span_map(G, root)

    llm_backend = None if backend in (None, "", "none") else backend
    prev = previous if isinstance(previous, dict) and previous.get("version") == LEARN_VERSION else {}
    prev_flows = {f.get("id"): f for f in prev.get("flows", []) if isinstance(f, dict)}
    prev_feats = {f.get("id"): f for f in prev.get("features", []) if isinstance(f, dict)}
    prev_difficulty = {k: v for k, v in (prev.get("difficulty", {}) or {}).items() if isinstance(v, dict)} if isinstance(prev.get("difficulty"), dict) else {}
    prev_node_notes = prev.get("node_notes") if isinstance(prev.get("node_notes"), dict) else {}
    regenerated = False

    flows = _build_flows(G, callers, callees, scores, root)

    # v3: 难度判定（先于特性文档生成）
    difficulty_map: dict[str, dict] = {}
    for flow in flows:
        signals = _collect_difficulty_signals(G, flow, spans, scores, root)
        fp = flow.get("fp", "")
        cached = prev_difficulty.get(flow["id"])
        if cached and cached.get("fp") == fp and cached.get("difficulty"):
            diff_info = cached
        else:
            diff_info = _judge_difficulty_ai(flow, signals, backend=llm_backend, model=model, usage_out=usage_out)
            diff_info["fp"] = fp
            regenerated = True
        difficulty_map[flow["id"]] = diff_info

    architecture = _build_architecture(G, communities, community_labels, scores, flows)
    features = _build_features(G, flows, root, spans, scores, difficulty_map=difficulty_map)

    # v3: 项目导览 / 社区导览 / 领域视角
    project_overview = _build_project_overview(G, communities, community_labels, flows, root)
    summary = project_overview["feature_intro"]
    tour = _build_tour(G, communities, community_labels, scores)
    # 领域视角：先结构化构建（Tier 1/2），LLM 增强（Tier 3）在下方带缓存执行
    domains = _build_domains(G, communities, community_labels, scores, root)

    # v3: 领域 LLM 增强（带缓存）
    prev_domains_list = prev.get("domains", []) if isinstance(prev.get("domains"), list) else []
    if llm_backend and domains:
        if _domains_cache_hit(domains, prev_domains_list):
            prev_by_id = {d.get("id"): d for d in prev_domains_list if isinstance(d, dict)}
            for dom in domains:
                pd = prev_by_id.get(dom["id"])
                if pd and pd.get("source") in ("llm", "ddd"):
                    dom["name"] = pd.get("name", dom["name"])
                    dom["desc"] = pd.get("desc", dom["desc"])
                    if pd.get("source") == "llm":
                        dom["source"] = "llm"
        else:
            _enhance_domains_llm(G, domains, backend=llm_backend, model=model, usage_out=usage_out)
            regenerated = True

    # v3: 节点注解（有 backend 时）—— 指纹按分数 top-20 节点计算（与 _build_node_notes 的选取逻辑一致）
    node_notes_fp = hashlib.sha256("|".join(sorted(scores, key=lambda n: -scores[n])[:20]).encode()).hexdigest()[:16] if scores else ""
    if llm_backend:
        if prev_node_notes and prev_node_notes.get("fp") == node_notes_fp and "notes" in prev_node_notes:
            node_notes = prev_node_notes.get("notes", {})
        else:
            node_notes = _build_node_notes(G, scores, backend=llm_backend, model=model, usage_out=usage_out)
            regenerated = True
    else:
        node_notes = {}

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
                regenerated = True
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
                regenerated = True
        if regenerated or not prev.get("project_summary"):
            try:
                raw = _llm_call(_SUMMARY_SYSTEM, backend=llm_backend, model=model,
                                max_tokens=512, usage_out=usage_out)
                parsed = _parse_learn_json(raw)
                s = _clean_str(parsed.get("summary"), 800)
                if s:
                    summary = s
            except Exception as exc:  # noqa: BLE001
                print(f"[graphify learn] 概览增强失败，保留结构化描述: {exc}", file=sys.stderr)
        else:
            summary = str(prev["project_summary"])

    data = {
        "version": LEARN_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "backend": llm_backend or "none",
        "project_summary": summary,
        "project_overview": project_overview,
        "tour": tour,
        "domains": domains,
        "flows": flows,
        "architecture": architecture,
        "features": features,
        "difficulty": difficulty_map,
        "node_notes": {"fp": node_notes_fp, "notes": node_notes} if llm_backend else {},
    }
    # 内部字段（path/involved_files/fp）不进 sidecar。
    for flow in data["flows"]:
        flow.pop("path", None)
    for feat in data["features"]:
        feat.pop("involved_files", None)
    # difficulty 内部字段（signals）不进 sidecar，但保留 fp 用于缓存
    for diff_info in data["difficulty"].values():
        diff_info.pop("signals", None)
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
    # 无向图的 source/target 方向会被 NetworkX 规范化吞掉（build.py 在主
    # 管线里补 _src/_tgt 正是这个原因）。直接加载 graph.json 时在这里
    # 注入，保证 calls/uses 边方向正确 —— 业务流走链依赖它。
    if not raw.get("directed", False):
        for _l in raw.get("links", []):
            if "_src" not in _l and _l.get("source") and _l.get("target"):
                _l["_src"] = _l["source"]
                _l["_tgt"] = _l["target"]
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
        f"{len(data['features'])} 篇特性文档（.graph/features/*.md）、"
        f"{len(data.get('tour', []))} 步导览、"
        f"{len(data.get('domains', []))} 个领域，后端 {data['backend']}。"
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
