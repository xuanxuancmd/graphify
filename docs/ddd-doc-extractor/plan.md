# Plan: DDD 文档自定义解析器 + 解析器优先级机制

> 关联：spec.md（同目录）。本 plan 是逐步实施文件级改动清单，目标是解耦可回 upstream。

## 0. 改动总览

| 改动 | 文件 | 类型 | 解耦策略 |
|---|---|---|---|
| 新建注册表 + `ExtractionResult` | `graphify/extractors/registry.py` | 新文件 | 独立模块，声明式返回（含 merge_mode/suppress_llm） |
| 新建 DDD 解析器 | `graphify/extractors/ddd.py` | 新文件 | 独立模块，通过 `@register_doc_extractor` 注册，返回 `ExtractionResult`；三个 parser 代码完整（从 .mjs 移植）；节点字段全通用，DDD 类型编码进 `tags` |
| 新建注入点 | `graphify/extractors/__init__.py` | 修改（追加 import） | 追加一行 `from graphify.extractors import ddd  # noqa: F401` 触发注册 |
| 新建 doc 主进程注入 | `graphify/extract.py` 的 `extract()` | 修改（加分支 + 返回值） | doc 在主进程先调 `try_external_extractors`，规避 subprocess pickle；返回 `suppress_llm_files` 集合 |
| 新建 code_index 传递 | `graphify/extract.py` | 修改（加参数） | `extract()` 新增 `code_index` 可选参数 |
| 新建两阶段提取调用 | `graphify/cli.py` | 修改（extract 命令处理） | code-first/doc-second；排除 `suppress_llm_files` 出 `semantic_files` |
| **tags 检索支持** | `graphify/serve.py` 的 `_node_search_text` | 修改（加法一行） | 把 `tags` 拼进可搜索文本，让 DDD 类型参与字符串检索 |
| 新建测试 | `tests/test_ddd_extractor.py` | 新文件 | 独立测试，不修改既有测试 |
| 新建 fixture | `tests/fixtures/ddd/` | 新目录 | DDD 文档样本 |

**不改的文件**：`markdown.py`、`build.py`、`dedup.py`、`llm.py`、`_DISPATCH` dict 的既有条目。`serve.py` 仅做一处加法（`_node_search_text` 拼接 `tags`），不修改既有 3 层匹配逻辑。

---

## 1. 步骤 1：创建注册表 `graphify/extractors/registry.py`

### 1.1 文件内容

```python
# graphify/extractors/registry.py
"""External extractor registry — opt-in extension point for .md doc parsing.

External extractors registered here are tried BEFORE the default extract_markdown.
An extractor returns None to signal "not my file, fall back to default".

This module is opt-in: if no extractor is registered (or the import in
__init__.py is removed), graphify behaves exactly as upstream.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Protocol


class DocExtractor(Protocol):
    def __call__(
        self, path: Path, *, root: Path, code_index: dict[str, list[dict]] | None = None
    ) -> "ExtractionResult | None":
        """Return ExtractionResult or None to fall back to default."""
        ...


@dataclass
class ExtractionResult:
    """声明式返回：外部解析器产出的节点/边 + 合并策略。

    merge_mode:
        "merge"          — 外部 + 默认 extract_markdown 合并（保留 page/heading 节点）
        "replace"        — 外部替代默认 markdown（跳过 extract_markdown），LLM Tier 2 仍跑（除非 suppress_llm）
        "supplement_only" — 只用外部结果，跳过默认 markdown + 跳过 LLM Tier 2

    suppress_llm:
        True = 不对该文件跑 LLM Tier 2（对 replace/supplement_only 生效；merge 模式下 LLM 总是跑）
    """
    nodes: list[dict]
    edges: list[dict]
    hyperedges: list[dict] = field(default_factory=list)
    merge_mode: str = "merge"
    suppress_llm: bool = False
    unmatched: list[dict] = field(default_factory=list)


_REGISTRY: list[Callable[..., "ExtractionResult | None"]] = []


def register_doc_extractor(fn: Callable[..., "ExtractionResult | None"]) -> Callable[..., "ExtractionResult | None"]:
    """Decorator to register an external doc extractor.

    Registered extractors are tried in registration order. The first non-None
    result wins; if all return None, the caller falls back to the default
    markdown extractor.
    """
    if fn not in _REGISTRY:
        _REGISTRY.append(fn)
    return fn


def try_external_extractors(
    path: Path, *, root: Path, code_index: dict[str, list[dict]] | None = None
) -> "ExtractionResult | None":
    """Try registered extractors in order; return first non-None result, or None."""
    for fn in _REGISTRY:
        try:
            result = fn(path, root=root, code_index=code_index)
        except _NotApplicable:
            result = None
        if result is not None:
            return result
    return None


class _NotApplicable(Exception):
    """Extractor signals "not my file" by raising this or returning None."""
    pass


def clear_registry() -> None:
    """Test helper: clear all registered extractors."""
    _REGISTRY.clear()
```

### 1.2 验证

```bash
uv run python -c "from graphify.extractors.registry import try_external_extractors, ExtractionResult; print('ok')"
```

---

## 2. 步骤 2：创建 DDD 解析器 `graphify/extractors/ddd.py`

### 2.1 完整文件内容（三个 parser 从 .mjs 逐行移植，节点字段全通用 + tags 编码 DDD 类型）

```python
# graphify/extractors/ddd.py
"""DDD documentation extractor.

Parses DDD-style markdown docs (context-map / technical-constraints /
business-flow / invariants / contracts / domain-events / domain-model)
into doc-anchor nodes + describes/related/categorized_under/cites edges.

Reference implementation: Understand-Anything/understand-anything-plugin/
skills/understand-ddd/parse-ddd-tables.mjs (ported to Python line-by-line).

Registered via graphify.extractors.registry; tried BEFORE extract_markdown
for .md files. Returns None for non-whitelist files (fall back to default).

Node modeling: all fields are generic (no ddd_* prefixed fields). DDD type
info is encoded into the generic 'tags' list field as:
    ["ddd", "<ddd_type>", "<doc_category>"]
so that graphify's string retrieval can match DDD types via tags.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from graphify.extractors.base import _file_stem, _make_id
from graphify.extractors.registry import ExtractionResult, register_doc_extractor

# ---------------------------------------------------------------------------
# Constants (ported from parse-ddd-tables.mjs)
# ---------------------------------------------------------------------------

DDD_DOC_KEYWORDS: tuple[str, ...] = (
    "context-map",
    "technical-constraints",
    "business-flow",
    "invariants",
    "contracts",
    "domain-events",
    "domain-model",
)

HEADER_TAG_REGEX = re.compile(r"^(.+?)<anchor:(\w+)>$")
TABLE_SEP_REGEX = re.compile(r"^:?-+:?$")
FENCE_REGEX = re.compile(r"^(```+|~~~+)")

FROM_COLUMNS = ["从", "源聚合", "源BC"]
TO_COLUMNS = ["到", "目标聚合", "目标BC"]
AGGREGATE_REF_COLUMNS = ["归属聚合", "操作的聚合"]
BC_REF_COLUMNS = ["对端 BC"]

TC_HEADING_REGEX = re.compile(r"^###\s+(TC-\d+)\s*[:：]\s*(.+)$")
TC_CODE_ANCHOR_PREFIX = "**代码锚点**"
TC_SCOPE_PREFIX = "**适用范围**"
TC_REASON_PREFIX = "**选型理由"

MULTI_REF_SPLIT_REGEX = re.compile(r"[/]")
ANCHOR_SPLIT_REGEX = re.compile(r"[·→]")

# Code anchor formats (ported from ddd-code-matcher.mjs)
FILE_EXTENSIONS: frozenset[str] = frozenset({
    "rs", "ts", "tsx", "jsx", "js", "mjs", "py", "pyi", "go", "java", "rb",
    "c", "cpp", "h", "hpp", "toml", "yaml", "yml", "json", "md",
})
FILE_NAME_REGEX = re.compile(r"^[\w/\\-]+\.\w{1,5}$")
SNAKE_DOT_METHOD_REGEX = re.compile(r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$")
PASCAL_DOT_METHOD_REGEX = re.compile(r"^([A-Z][a-zA-Z0-9]+)\.([a-z_][a-z0-9_]*)$")
PASCAL_CASE_REGEX = re.compile(r"^[A-Z][a-zA-Z0-9]+$")
HTTP_URL_REGEX = re.compile(r"^(GET|POST|PUT|DELETE|PATCH)\s+\/.+$", re.IGNORECASE)
HTTP_COLON_URL_REGEX = re.compile(r"^(GET|POST|PUT|DELETE|PATCH):\/(.+)$", re.IGNORECASE)
PATH_URL_REGEX = re.compile(r"^\/.+")


# ---------------------------------------------------------------------------
# Code anchor matching (ported from ddd-code-matcher.mjs)
# ---------------------------------------------------------------------------

def _basename_without_ext(file_path: str) -> str:
    from os.path import basename, splitext
    base = basename(file_path)
    return splitext(base)[0]


def _build_code_indices(graph_nodes: list[dict]) -> dict[str, dict]:
    """Build fileIndex / nameIndex / endpointIndex from existing AST nodes.

    Indexes nodes with file_type=="code" (AST-extracted). Adapts the .mjs
    which indexes all nodes by filePath/name — graphify uses file_type to
    distinguish code vs doc nodes.
    """
    file_index: dict[str, list[dict]] = {}
    name_index: dict[str, list[dict]] = {}
    endpoint_index: dict[str, dict] = {}

    for node in graph_nodes:
        if not node or not node.get("id"):
            continue
        if node.get("file_type") != "code":
            continue
        source_file = node.get("source_file")
        if source_file:
            key = _basename_without_ext(source_file)
            if key:
                file_index.setdefault(key, []).append(node)
        label = node.get("label")
        if label:
            name_index.setdefault(label, []).append(node)
        if label and label.startswith("/"):
            endpoint_index[label] = node

    return {"fileIndex": file_index, "nameIndex": name_index, "endpointIndex": endpoint_index}


def _match_code_anchor(anchor: str, indices: dict) -> dict | None:
    """Match a code anchor string against graph indices. Priority per ddd-code-matcher.mjs."""
    # 0. File name with known extension
    if FILE_NAME_REGEX.match(anchor):
        ext = anchor.rsplit(".", 1)[-1]
        if ext in FILE_EXTENSIONS:
            base = _basename_without_ext(anchor)
            candidates = indices["fileIndex"].get(base, [])
            file_node = next((n for n in candidates if n.get("node_kind") == "file"), None)
            return file_node or (candidates[0] if candidates else None)

    # 1. snake_case file.method
    if SNAKE_DOT_METHOD_REGEX.match(anchor):
        dot_idx = anchor.index(".")
        file_hint = anchor[:dot_idx]
        method_name = anchor[dot_idx + 1:]
        candidates = indices["fileIndex"].get(file_hint, [])
        return next(
            (n for n in candidates
             if n.get("node_kind") == "function" and n.get("label") == method_name),
            None,
        )

    # 2. PascalCase.method
    m = PASCAL_DOT_METHOD_REGEX.match(anchor)
    if m:
        class_name, method_name = m.group(1), m.group(2)
        class_candidates = indices["nameIndex"].get(class_name, [])
        cls = next((n for n in class_candidates if n.get("node_kind") == "class"), None)
        if not cls:
            return None
        fn_candidates = indices["nameIndex"].get(method_name, [])
        return next(
            (n for n in fn_candidates
             if n.get("node_kind") == "function"
             and n.get("source_file") == cls.get("source_file")),
            None,
        )

    # 3. PascalCase class name
    if PASCAL_CASE_REGEX.match(anchor):
        candidates = indices["nameIndex"].get(anchor, [])
        cls = next((n for n in candidates if n.get("node_kind") == "class"), None)
        return cls or (candidates[0] if candidates else None)

    # 4. URL — HTTP method + space + path
    if HTTP_URL_REGEX.match(anchor):
        space_idx = anchor.index(" ")
        path = anchor[space_idx + 1:].strip()
        return indices["endpointIndex"].get(path)

    # 5. URL — HTTP method + colon + path
    m = HTTP_COLON_URL_REGEX.match(anchor)
    if m:
        path = "/" + m.group(2)
        return indices["endpointIndex"].get(path)

    # 6. bare path
    if PATH_URL_REGEX.match(anchor):
        return indices["endpointIndex"].get(anchor)

    return None


# ---------------------------------------------------------------------------
# Fence-aware line scanner (ported from parse-ddd-tables.mjs:105-128)
# ---------------------------------------------------------------------------

def _scan_lines_with_fence(content: str) -> list[dict]:
    lines = content.split("\n")
    result = []
    in_fence = False
    fence_marker = None
    for i, line in enumerate(lines):
        fence_match = FENCE_REGEX.match(line)
        if fence_match:
            if not in_fence:
                in_fence = True
                fence_marker = fence_match.group(1)[0]
            elif fence_marker and line.startswith(fence_marker):
                in_fence = False
                fence_marker = None
            result.append({"lineNum": i + 1, "line": line, "inFence": True})
            continue
        result.append({"lineNum": i + 1, "line": line, "inFence": in_fence})
    return result


# ---------------------------------------------------------------------------
# Table parsing (ported from parse-ddd-tables.mjs:77-99)
# ---------------------------------------------------------------------------

def _parse_table_block(table_lines: list[str]) -> dict | None:
    if len(table_lines) < 2:
        return None

    def parse_row(line: str) -> list[str]:
        inner = line.strip()
        if inner.startswith("|"):
            inner = inner[1:]
        if inner.endswith("|"):
            inner = inner[:-1]
        return [c.strip() for c in inner.split("|")]

    headers = parse_row(table_lines[0])
    sep = parse_row(table_lines[1])
    if not all(TABLE_SEP_REGEX.match(c) for c in sep):
        return None
    return {"headers": headers, "rows": [parse_row(l) for l in table_lines[2:]]}


def _parse_header_tags(headers: list[str]) -> dict[str, dict] | None:
    tags: dict[str, dict] = {}
    for i, h in enumerate(headers):
        m = HEADER_TAG_REGEX.match(h)
        if m:
            tags[m.group(2)] = {"colIndex": i, "dddType": m.group(1).strip()}
    return tags if tags else None


def _split_anchors(cell_value: str) -> list[str]:
    """Split a cell value into individual anchor strings. Handles · and → separators."""
    if not cell_value:
        return []
    return [
        s.strip().strip("`").strip()
        for s in ANCHOR_SPLIT_REGEX.split(cell_value)
        if s.strip()
    ]


# ---------------------------------------------------------------------------
# Node + Edge builders (graphify-compatible shapes, all generic fields)
# ---------------------------------------------------------------------------

def _make_doc_anchor_id(doc_path: str, concept_id: str) -> str:
    """ID format: docanchor_{stem}_{conceptId}. Uses make_id for [a-z0-9_] compliance."""
    stem = _file_stem(Path(doc_path))
    return _make_id("docanchor", stem, concept_id)


def _infer_ddd_type(ddd_type_raw: str) -> str:
    """Infer machine-readable ddd_type from the <anchor:ddd> column name."""
    raw = ddd_type_raw.lower()
    if "聚合根" in raw or "aggregate" in raw:
        return "aggregate_root"
    if "领域事件" in raw or "event" in raw.lower():
        return "domain_event"
    if "不变式" in raw or "invariant" in raw.lower():
        return "invariant"
    if "限界上下文" in raw or "bounded" in raw.lower() or "bc" in raw:
        return "bounded_context"
    if "值对象" in raw or "value" in raw.lower():
        return "value_object"
    if "领域服务" in raw:
        return "domain_service"
    if "契约" in raw or "contract" in raw.lower():
        return "contract"
    if "流程" in raw or "flow" in raw.lower():
        return "business_flow_step"
    if "术语" in raw or "glossary" in raw.lower():
        return "glossary_term"
    if "约束" in raw or "constraint" in raw.lower() or "tc" in raw:
        return "tech_constraint"
    return "concept"


def _ddd_category_from_path(rel_path: str) -> str:
    """Infer doc_category from file path keywords."""
    rl = rel_path.lower()
    for kw in DDD_DOC_KEYWORDS:
        if kw in rl:
            return kw
    return "unknown"


def _make_node(
    *, doc_path: str, concept_id: str, name: str,
    ddd_type: str, doc_category: str, desc: str = "", line_num: int = 0,
) -> dict:
    """Build a doc-anchor node with all-generic fields.

    DDD type info is encoded into the generic 'tags' list field:
        ["ddd", "<ddd_type>", "<doc_category>"]
    so no ddd_* prefixed fields are needed on the node.
    """
    return {
        "id": _make_doc_anchor_id(doc_path, concept_id),
        "label": name,
        "file_type": "concept",
        "source_file": doc_path,
        "source_location": f"L{line_num}" if line_num else None,
        "node_kind": "doc-anchor",
        "desc": desc,
        "concept_id": concept_id,
        # Generic tags list — DDD type info encoded here for retrieval
        "tags": ["ddd", ddd_type, doc_category],
    }


def _make_edge(
    *, source: str, target: str, relation: str,
    confidence: str = "EXTRACTED", confidence_score: float = 1.0,
    source_file: str, line_num: int = 0, weight: float = 0.5,
) -> dict:
    return {
        "source": source, "target": target, "relation": relation,
        "confidence": confidence, "confidence_score": confidence_score,
        "source_file": source_file,
        "source_location": f"L{line_num}" if line_num else None,
        "weight": weight,
    }


# ---------------------------------------------------------------------------
# R3: Tagged-table parser (ported from parse-ddd-tables.mjs:177-337)
# ---------------------------------------------------------------------------

def _parse_tagged_file(
    abs_path: Path, project_root: Path, indices: dict,
) -> dict:
    """Parse a single .md file for tagged DDD tables.

    Collects nodes + pending edges + unmatched anchors.
    Does NOT resolve internal edges — that happens in _resolve_pending_edges
    with the global index.
    """
    doc_path = abs_path.resolve().relative_to(project_root.resolve()).as_posix()
    content = abs_path.read_text(encoding="utf-8", errors="replace")
    scanned = _scan_lines_with_fence(content)
    doc_category = _ddd_category_from_path(doc_path)

    nodes: list[dict] = []
    pending_edges: list[dict] = []
    unmatched: list[dict] = []

    i = 0
    while i < len(scanned):
        if scanned[i]["inFence"] or not scanned[i]["line"].strip().startswith("|"):
            i += 1
            continue
        block_start = i
        while i < len(scanned) and not scanned[i]["inFence"] and scanned[i]["line"].strip().startswith("|"):
            i += 1
        block_lines = [s["line"] for s in scanned[block_start:i]]

        parsed = _parse_table_block(block_lines)
        if not parsed:
            continue

        header_tags = _parse_header_tags(parsed["headers"])
        if not header_tags:
            continue  # No anchor tags — skip

        ddd_col = header_tags.get("ddd")
        if not ddd_col:
            continue

        desc_col = header_tags.get("desc")
        code_col = header_tags.get("code")
        ddd_type_raw = ddd_col["dddType"]
        ddd_type = _infer_ddd_type(ddd_type_raw)

        # Detect internal-edge columns using relaxed synonyms
        id_col_idx = next((idx for idx, h in enumerate(parsed["headers"]) if h.strip() == "ID"), -1)
        from_col_idx = next((idx for idx, h in enumerate(parsed["headers"]) if h.strip() in FROM_COLUMNS), -1)
        to_col_idx = next((idx for idx, h in enumerate(parsed["headers"]) if h.strip() in TO_COLUMNS), -1)
        agg_ref_col_idx = next((idx for idx, h in enumerate(parsed["headers"]) if h.strip() in AGGREGATE_REF_COLUMNS), -1)
        bc_ref_col_idx = next((idx for idx, h in enumerate(parsed["headers"]) if h.strip() in BC_REF_COLUMNS), -1)

        for row in parsed["rows"]:
            ddd_value = (row[ddd_col["colIndex"]] if ddd_col["colIndex"] < len(row) else "").strip()
            if not ddd_value:
                continue

            desc_value = (row[desc_col["colIndex"]] if desc_col and desc_col["colIndex"] < len(row) else "").strip()
            code_value = (row[code_col["colIndex"]] if code_col and code_col["colIndex"] < len(row) else "").strip()

            # concept_id: prefer ID column, else name
            concept_id = (
                row[id_col_idx].strip()
                if id_col_idx >= 0 and id_col_idx < len(row) and row[id_col_idx].strip()
                else ddd_value
            )

            node = _make_node(
                doc_path=doc_path, concept_id=concept_id, name=ddd_value,
                ddd_type=ddd_type, doc_category=doc_category,
                desc=desc_value, line_num=scanned[block_start]["lineNum"],
            )
            nodes.append(node)

            # --- Code anchors → describes edges (resolved immediately) ---
            if code_value:
                for anchor_str in _split_anchors(code_value):
                    # Strip trailing qualifiers like "trait (#[async_trait])"
                    clean_anchor = re.sub(r"\s+.*$", "", anchor_str).strip()
                    if not clean_anchor:
                        continue
                    matched = _match_code_anchor(clean_anchor, indices)
                    if matched:
                        pending_edges.append({
                            "type": "describes",
                            "sourceNodeId": node["id"],
                            "targetNodeId": matched["id"],
                            "weight": 0.8,
                            "source_file": doc_path,
                        })
                    else:
                        unmatched.append({
                            "docPath": doc_path,
                            "conceptId": concept_id,
                            "anchor": clean_anchor,
                            "reason": "no matching code node",
                        })

            # --- from/to columns → related edges ---
            if from_col_idx >= 0 and to_col_idx >= 0:
                from_val = (row[from_col_idx] if from_col_idx < len(row) else "").strip()
                to_val = (row[to_col_idx] if to_col_idx < len(row) else "").strip()
                if from_val and to_val:
                    for fr in MULTI_REF_SPLIT_REGEX.split(from_val):
                        for tr in MULTI_REF_SPLIT_REGEX.split(to_val):
                            fr, tr = fr.strip(), tr.strip()
                            if fr and tr:
                                pending_edges.append({
                                    "type": "related",
                                    "sourceNodeId": None,
                                    "sourceRef": fr,
                                    "targetRef": tr,
                                    "targetNodeId": None,
                                    "weight": 0.5,
                                    "source_file": doc_path,
                                })

            # --- 归属聚合/操作的聚合 → categorized_under edges ---
            if agg_ref_col_idx >= 0:
                agg_val = (row[agg_ref_col_idx] if agg_ref_col_idx < len(row) else "").strip()
                if agg_val:
                    for ref in MULTI_REF_SPLIT_REGEX.split(agg_val):
                        ref = ref.strip()
                        if ref:
                            pending_edges.append({
                                "type": "categorized_under",
                                "sourceNodeId": node["id"],
                                "sourceRef": None,
                                "targetRef": ref,
                                "targetNodeId": None,
                                "weight": 0.6,
                                "source_file": doc_path,
                            })

            # --- 对端 BC → cites edges ---
            if bc_ref_col_idx >= 0:
                bc_val = (row[bc_ref_col_idx] if bc_ref_col_idx < len(row) else "").strip()
                if bc_val and bc_val != "外部":
                    pending_edges.append({
                        "type": "cites",
                        "sourceNodeId": node["id"],
                        "sourceRef": None,
                        "targetRef": bc_val,
                        "targetNodeId": None,
                        "weight": 0.7,
                        "source_file": doc_path,
                    })

    return {"nodes": nodes, "pendingEdges": pending_edges, "unmatched": unmatched}


# ---------------------------------------------------------------------------
# R6: context-map.md handler (ported from parse-ddd-tables.mjs:353-452)
# ---------------------------------------------------------------------------

def _parse_context_map(abs_path: Path, project_root: Path) -> dict:
    """Parse context-map.md which has no <anchor:...> tags.

    Extracts:
      - BC nodes from the "限界上下文" table (headers: BC ID, BC 名称, ...)
      - related edges from the "业务关系" table (headers: 从, 到, ...)
      - glossary nodes from the "统一语言" table (headers: 术语, 定义, ...)
    """
    doc_path = abs_path.resolve().relative_to(project_root.resolve()).as_posix()
    content = abs_path.read_text(encoding="utf-8", errors="replace")
    scanned = _scan_lines_with_fence(content)

    nodes: list[dict] = []
    pending_edges: list[dict] = []

    i = 0
    while i < len(scanned):
        if scanned[i]["inFence"] or not scanned[i]["line"].strip().startswith("|"):
            i += 1
            continue
        block_start = i
        while i < len(scanned) and not scanned[i]["inFence"] and scanned[i]["line"].strip().startswith("|"):
            i += 1
        block_lines = [s["line"] for s in scanned[block_start:i]]

        parsed = _parse_table_block(block_lines)
        if not parsed:
            continue

        headers = [h.strip() for h in parsed["headers"]]

        # --- BC table: headers include "BC ID" and "BC 名称" ---
        if "BC ID" in headers and "BC 名称" in headers:
            id_idx = headers.index("BC ID")
            name_idx = headers.index("BC 名称")
            desc_idx = next((idx for idx, h in enumerate(headers) if h.startswith("职责")), -1)

            for row in parsed["rows"]:
                bc_id = (row[id_idx] if id_idx < len(row) else "").strip()
                bc_name = (row[name_idx] if name_idx < len(row) else "").strip()
                if not bc_id or not bc_name:
                    continue
                nodes.append(_make_node(
                    doc_path=doc_path, concept_id=bc_id, name=bc_name,
                    ddd_type="bounded_context", doc_category="context-map",
                    desc=(row[desc_idx] if desc_idx >= 0 and desc_idx < len(row) else "").strip(),
                    line_num=scanned[block_start]["lineNum"],
                ))
            continue

        # --- BC relationship table: headers include "从" and "到" ---
        if any(h in FROM_COLUMNS for h in headers) and any(h in TO_COLUMNS for h in headers):
            from_idx = next(idx for idx, h in enumerate(headers) if h in FROM_COLUMNS)
            to_idx = next(idx for idx, h in enumerate(headers) if h in TO_COLUMNS)

            for row in parsed["rows"]:
                from_val = (row[from_idx] if from_idx < len(row) else "").strip()
                to_val = (row[to_idx] if to_idx < len(row) else "").strip()
                if not from_val or not to_val or from_val == "外部" or to_val == "外部":
                    continue
                pending_edges.append({
                    "type": "related",
                    "sourceNodeId": None,
                    "sourceRef": from_val,
                    "targetRef": to_val,
                    "targetNodeId": None,
                    "weight": 0.5,
                    "source_file": doc_path,
                })
            continue

        # --- Glossary table: headers include "术语" and "定义" ---
        if "术语" in headers and "定义" in headers:
            term_idx = headers.index("术语")
            def_idx = headers.index("定义")

            for row in parsed["rows"]:
                term = (row[term_idx] if term_idx < len(row) else "").strip()
                if not term:
                    continue
                nodes.append(_make_node(
                    doc_path=doc_path, concept_id=term, name=term,
                    ddd_type="glossary_term", doc_category="context-map",
                    desc=(row[def_idx] if def_idx < len(row) else "").strip(),
                    line_num=scanned[block_start]["lineNum"],
                ))
            continue

    return {"nodes": nodes, "pendingEdges": pending_edges}


# ---------------------------------------------------------------------------
# R7: technical-constraints.md handler (ported from parse-ddd-tables.mjs:464-569)
# ---------------------------------------------------------------------------

def _parse_technical_constraints(
    abs_path: Path, project_root: Path, indices: dict,
) -> dict:
    """Parse technical-constraints.md which uses `### TC-xxx:` headings and
    `**代码锚点**:` / `**适用范围**:` paragraph prefixes instead of tables.
    """
    doc_path = abs_path.resolve().relative_to(project_root.resolve()).as_posix()
    content = abs_path.read_text(encoding="utf-8", errors="replace")
    lines = content.split("\n")

    nodes: list[dict] = []
    pending_edges: list[dict] = []
    unmatched: list[dict] = []

    current_node: dict | None = None

    for i, line in enumerate(lines):
        trimmed = line.strip()
        # Strip leading `- ` (list item prefix) for paragraph-prefix checks
        stripped = re.sub(r"^-\s+", "", trimmed)

        # --- TC heading: `### TC-001: Title` ---
        tc_match = TC_HEADING_REGEX.match(trimmed)
        if tc_match:
            tc_id = tc_match.group(1)
            tc_title = tc_match.group(2).strip()
            current_node = _make_node(
                doc_path=doc_path, concept_id=tc_id, name=tc_title,
                ddd_type="tech_constraint", doc_category="technical-constraints",
                desc="", line_num=i + 1,
            )
            nodes.append(current_node)
            continue

        if not current_node:
            continue

        # --- **代码锚点**: `file.rs` · `other.rs` ---
        if stripped.startswith(TC_CODE_ANCHOR_PREFIX):
            anchor_str = re.sub(r"^[:：]\s*", "", stripped[len(TC_CODE_ANCHOR_PREFIX):]).strip()
            if anchor_str:
                for anchor in _split_anchors(anchor_str):
                    # Strip trailing qualifiers
                    clean_anchor = re.sub(r"\s+.*$", "", anchor).strip()
                    if not clean_anchor:
                        continue
                    matched = _match_code_anchor(clean_anchor, indices)
                    if matched:
                        pending_edges.append({
                            "type": "describes",
                            "sourceNodeId": current_node["id"],
                            "targetNodeId": matched["id"],
                            "weight": 0.8,
                            "source_file": doc_path,
                        })
                    else:
                        unmatched.append({
                            "docPath": doc_path,
                            "conceptId": current_node["concept_id"],
                            "anchor": clean_anchor,
                            "reason": "no matching code node",
                        })

        # --- **适用范围**: BC-01 / 全局 ---
        if stripped.startswith(TC_SCOPE_PREFIX):
            scope_val = re.sub(r"^[:：]\s*", "", stripped[len(TC_SCOPE_PREFIX):]).strip()
            if scope_val and scope_val != "全局":
                for ref in re.split(r"[,，]", scope_val):
                    ref = ref.strip()
                    if ref and ref.startswith("BC-"):
                        pending_edges.append({
                            "type": "categorized_under",
                            "sourceNodeId": current_node["id"],
                            "sourceRef": None,
                            "targetRef": ref,
                            "targetNodeId": None,
                            "weight": 0.6,
                            "source_file": doc_path,
                        })

        # --- **选型理由（Why）**: → use as desc ---
        if stripped.startswith(TC_REASON_PREFIX):
            reason = re.sub(r"^\*\*选型理由[^*]*\*\*[:：]?\s*", "", stripped).strip()
            if reason and current_node:
                current_node["desc"] = reason

    return {"nodes": nodes, "pendingEdges": pending_edges, "unmatched": unmatched}


# ---------------------------------------------------------------------------
# Global edge resolver (ported from parse-ddd-tables.mjs:579-665)
# ---------------------------------------------------------------------------

def _build_global_node_index(all_nodes: list[dict]) -> dict:
    """Build concept_id → node and name → node index from ALL collected nodes.

    Uses the raw 'concept_id' node field (not the normalized id) to avoid
    the make_id normalization issue (paths/ids get lowercased + separators
    collapsed to _, breaking split-based recovery).
    """
    by_concept_id: dict[str, dict] = {}
    by_name: dict[str, dict] = {}

    for node in all_nodes:
        if not node.get("id", "").startswith("docanchor_"):
            continue
        concept_id = node.get("concept_id", "")
        if concept_id and concept_id not in by_concept_id:
            by_concept_id[concept_id] = node
        name = node.get("label", "")
        if name and name not in by_name:
            by_name[name] = node

    return {"byConceptId": by_concept_id, "byName": by_name}


def _resolve_ref(ref: str, global_index: dict) -> dict | None:
    """Resolve a reference (concept_id or name) to a node using the global index.

    Strips parenthetical qualifiers: "BC-04(Converter)" → "BC-04".
    Matches raw values (no normalization) — concept_id is stored raw on nodes.
    """
    if not ref:
        return None
    clean_ref = re.sub(r"\(.*\)", "", ref).strip()
    return global_index["byConceptId"].get(clean_ref) or global_index["byName"].get(clean_ref)


def _resolve_pending_edges(all_nodes: list[dict], pending_edges: list[dict]) -> list[dict]:
    """Resolve all pending edges using the global node index.

    - describes edges: already have targetNodeId, just materialize
    - related/categorized_under/cites: resolve sourceRef/targetRef via global index
    """
    global_index = _build_global_node_index(all_nodes)
    node_by_id = {n["id"]: n for n in all_nodes}
    edges: list[dict] = []
    seen: set[str] = set()

    relation_map = {
        "describes": "references",
        "related": "conceptually_related_to",
        "categorized_under": "conceptually_related_to",
        "cites": "cites",
    }

    for pe in pending_edges:
        source_node = None
        target_node = None

        if pe["type"] == "describes":
            # Already resolved — sourceNodeId + targetNodeId known
            source_node = node_by_id.get(pe["sourceNodeId"])
            target_node = {"id": pe["targetNodeId"]} if pe.get("targetNodeId") else None
        else:
            # Resolve via global index
            if pe.get("sourceNodeId"):
                source_node = node_by_id.get(pe["sourceNodeId"])
            elif pe.get("sourceRef"):
                source_node = _resolve_ref(pe["sourceRef"], global_index)

            if pe.get("targetNodeId"):
                target_node = {"id": pe["targetNodeId"]}
            elif pe.get("targetRef"):
                target_node = _resolve_ref(pe["targetRef"], global_index)

        if source_node and target_node:
            key = f"{source_node['id']}|{target_node['id']}|{pe['type']}"
            if key not in seen:
                seen.add(key)
                edges.append(_make_edge(
                    source=source_node["id"],
                    target=target_node["id"],
                    relation=relation_map.get(pe["type"], "references"),
                    source_file=pe.get("source_file", ""),
                    weight=pe.get("weight", 0.5),
                ))

    return edges


# ---------------------------------------------------------------------------
# Public entry — returns ExtractionResult
# ---------------------------------------------------------------------------

def extract_ddd(
    path: Path, *, root: Path, code_index: dict[str, list[dict]] | None = None
) -> ExtractionResult | None:
    """Extract DDD concepts from a whitelist .md file. Returns None for non-whitelist."""
    rel_path = path.resolve().relative_to(root.resolve()).as_posix().lower()
    if not any(kw in rel_path for kw in DDD_DOC_KEYWORDS):
        return None

    content = path.read_text(encoding="utf-8", errors="replace")

    # Build code indices if provided (G3: AST-first)
    code_nodes = []
    if code_index:
        raw = code_index.get("nodes", []) if isinstance(code_index, dict) else []
        if isinstance(raw, list):
            code_nodes = [n for n in raw if isinstance(n, dict)]
    indices = _build_code_indices(code_nodes)

    filename = path.name
    all_nodes: list[dict] = []
    pending_edges: list[dict] = []
    unmatched: list[dict] = []

    if filename == "context-map.md":
        result = _parse_context_map(path, root)
        all_nodes.extend(result["nodes"])
        pending_edges.extend(result["pendingEdges"])
    elif filename == "technical-constraints.md":
        result = _parse_technical_constraints(path, root, indices)
        all_nodes.extend(result["nodes"])
        pending_edges.extend(result["pendingEdges"])
        unmatched.extend(result["unmatched"])
    else:
        # Tagged-table parser for business-flow / invariants / contracts /
        # domain-events / domain-model
        result = _parse_tagged_file(path, root, indices)
        all_nodes.extend(result["nodes"])
        pending_edges.extend(result["pendingEdges"])
        unmatched.extend(result["unmatched"])

    edges = _resolve_pending_edges(all_nodes, pending_edges)

    # DDD 推荐 merge 模式：doc-anchor + page/heading 互补，LLM Tier 2 仍跑（通用 prompt）
    return ExtractionResult(
        nodes=all_nodes,
        edges=edges,
        hyperedges=[],
        merge_mode="merge",        # DDD：外部 + 默认 markdown 合并
        suppress_llm=False,        # LLM Tier 2 仍跑（通用 prompt 抓散文语义）
        unmatched=unmatched,
    )


register_doc_extractor(extract_ddd)
```

### 2.2 实现说明

三个 parser 已**完整移植**（非 placeholder）：
- `_parse_tagged_file`（~120 LOC，从 `parse-ddd-tables.mjs:177-337`）
- `_parse_context_map`（~90 LOC，从 `parse-ddd-tables.mjs:353-452`）
- `_parse_technical_constraints`（~80 LOC，从 `parse-ddd-tables.mjs:464-569`）
- `_build_global_node_index` + `_resolve_pending_edges`（~70 LOC，从 `parse-ddd-tables.mjs:579-665`）

**关键设计**：
- `_make_node` 存储全通用字段（`id`/`label`/`file_type`/`source_file`/`source_location`/`node_kind`/`desc`/`concept_id`/`tags`），**无 `ddd_*` 前缀字段**
- DDD 类型信息（`ddd_type` + `doc_category`）编码进通用 `tags` 列表：`["ddd", "<ddd_type>", "<doc_category>"]`
- `concept_id` 存原始值，规避 `make_id` normalize 问题
- `desc` 字段（原 `summary`）存 `<anchor:desc>` 内容

**总 LOC**：~660 LOC（含注释）

---

## 3. 步骤 3：注入点（doc 主进程跑 + 合并分流 + suppress_llm）

### 3.1 在 `graphify/extractors/__init__.py` 追加注册 import

```python
# graphify/extractors/__init__.py (追加一行)
from graphify.extractors import ddd  # noqa: F401  — triggers @register_doc_extractor
```

> 这一行是唯一的"开关"。删掉它，DDD 解析器不注册，graphify 行为与 upstream 完全一致。

### 3.2 在 `graphify/extract.py` 的 `extract()` 加 doc 主进程注入

**不改 `_DISPATCH` dict**。`extract()` 用 `per_file` 槽位 + subprocess/sequential 分发。**在分发前**，主进程先处理外部解析器匹配的 doc 文件：

```python
# graphify/extract.py — 在 extract() 函数内，per_file 分发之前加：

from graphify.extractors.registry import try_external_extractors

# extract() 签名加 code_index + 返回 suppress_llm_files：
def extract(paths, *, root=None, code_index: dict | None = None) -> dict:
    ...
    suppress_llm_files: set[str] = set()

    # --- NEW: doc 主进程预处理（在 per_file 填充前） ---
    # 对每个 .md/.mdx/.qmd/.skill 文件，先尝试外部解析器
    DOC_EXTS = {".md", ".mdx", ".qmd", ".skill"}
    doc_paths_handled: set[int] = set()  # 已被外部处理的 paths 索引

    if code_index is not None:  # 只有第二阶段（doc 提取）才走外部解析器
        for idx, path in enumerate(paths):
            if path.suffix not in DOC_EXTS:
                continue
            ext = try_external_extractors(path, root=root, code_index=code_index)
            if ext is None:
                continue  # 归入既有 dispatch 走默认 extract_markdown

            doc_paths_handled.add(idx)

            # 按 merge_mode 分流
            if ext.merge_mode == "supplement_only":
                # 只用外部，跳过 markdown + 标记跳过 LLM
                if ext.suppress_llm:
                    suppress_llm_files.add(str(path))
                per_file[idx] = {
                    "nodes": ext.nodes,
                    "edges": ext.edges,
                    "hyperedges": ext.hyperedges,
                }

            elif ext.merge_mode == "replace":
                # 外部替代 markdown
                if ext.suppress_llm:
                    suppress_llm_files.add(str(path))
                per_file[idx] = {
                    "nodes": ext.nodes,
                    "edges": ext.edges,
                    "hyperedges": ext.hyperedges,
                }

            else:  # "merge"（DDD 默认）
                # 外部 + 默认 extract_markdown 合并
                from graphify.extractors.markdown import extract_markdown
                md_result = extract_markdown(path)
                merged_nodes = list(ext.nodes) + list(md_result.get("nodes", []))
                merged_edges = list(ext.edges) + list(md_result.get("edges", []))
                # Dedup edges by (source, target, relation)
                seen = set()
                dedup_edges = []
                for e in merged_edges:
                    key = (e.get("source"), e.get("target"), e.get("relation"))
                    if key not in seen:
                        seen.add(key)
                        dedup_edges.append(e)
                # Write unmatched sidecar
                if ext.unmatched:
                    _write_ddd_unmatched(root, ext.unmatched)
                per_file[idx] = {
                    "nodes": merged_nodes,
                    "edges": dedup_edges,
                    "hyperedges": ext.hyperedges,
                }

    # --- 既有 dispatch 逻辑：跳过 doc_paths_handled 的索引 ---
    # 在 _extract_parallel / _extract_sequential 的循环里，对 doc_paths_handled 中的 idx 跳过
    # （per_file[idx] 已填，不需要再 dispatch）

    # ... 既有 all_nodes / all_edges 合并逻辑不变

    # extract() 返回值新增 suppress_llm_files：
    return {
        "nodes": all_nodes, "edges": all_edges, "hyperedges": ...,
        "suppress_llm_files": suppress_llm_files,
    }
```

**关键设计**：
- 外部解析器在**主进程**跑（不走 subprocess pool），规避 `code_index` pickle 成本
- 外部处理的文件直接填 `per_file[idx]`，跳过既有 dispatch
- 未处理的 doc 文件归入既有 dispatch 走默认 `extract_markdown`
- 返回 `suppress_llm_files` 集合给 cli.py

### 3.3 `_write_ddd_unmatched` 辅助函数

```python
# graphify/extract.py — 新增辅助函数
def _write_ddd_unmatched(root: Path, unmatched: list[dict]) -> None:
    """Write unmatched DDD code anchors to sidecar JSON for manual review."""
    import json
    out_dir = root / ".graph" if (root / ".graph").is_dir() else root
    out_path = out_dir / "ddd-unmatched.json"
    existing = []
    if out_path.is_file():
        try:
            existing = json.loads(out_path.read_text(encoding="utf-8"))
        except Exception:
            existing = []
    existing.extend(unmatched)
    out_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
```

### 3.4 两阶段提取（G3：AST 优先）—— cli.py 修改

修改 cli.py 的 extract 命令处理，分两阶段 + 处理 `suppress_llm_files`：

```python
# cli.py — extract 命令处理（在 collect_files 之后，extract 调用之前）：

from graphify.detect import CODE_EXTENSIONS  # 既有

DOC_EXTS = {".md", ".mdx", ".qmd", ".skill"}
code_files = [f for f in files if f.suffix in CODE_EXTENSIONS]
doc_files = [f for f in files if f.suffix in DOC_EXTS]
other_files = [f for f in files if f.suffix not in CODE_EXTENSIONS and f.suffix not in DOC_EXTS]

# 阶段 1: code AST 并行提取（既有 extract 逻辑，无 code_index）
code_result = extract(code_files + other_files, root=root)

# 阶段 2: doc 提取（传入 code_index）
doc_result = extract(doc_files, root=root, code_index={"nodes": code_result["nodes"]})
suppress_llm_files = doc_result.get("suppress_llm_files", set())

# 合并 code + doc
all_nodes = code_result["nodes"] + doc_result["nodes"]
all_edges = code_result["edges"] + doc_result["edges"]
all_hyperedges = code_result.get("hyperedges", []) + doc_result.get("hyperedges", [])

# 构建 semantic_files 时排除 suppress_llm_files（既有 LLM Tier 2 逻辑之前）
semantic_files = [f for f in doc_files if str(f) not in suppress_llm_files]
# ... 既有 LLM Tier 2 对 semantic_files 跑
```

> **注意**：
> - `extract()` 签名加 `code_index: dict | None = None` 可选参数。默认 None 时行为不变（向后兼容）
> - 返回值加 `suppress_llm_files: set` 字段，既有调用方忽略此字段时行为不变
> - `code_files + other_files` 一起走阶段 1（other 是 paper/image 等，不影响 code_index 构建）

---

## 4. 步骤 4：tags 检索支持（修改 `graphify/serve.py` 的 `_node_search_text`）

### 4.1 改动位置

`serve.py:322-356` 的 `_node_search_text` 函数。当前拼接 `norm_label + label_tokens + nid + source_file + source_tokens`。

### 4.2 加法改动（一行）

在拼接末尾追加 `tags`（join 成空格分隔字符串）：

```python
# serve.py — _node_search_text 函数（伪代码，实际行号见源码）：
def _node_search_text(nid: str, data: dict) -> str:
    ...
    parts = [
        norm_label,
        " ".join(label_tokens),
        nid,
        source,
        " ".join(source_tokens),
        # NEW: tags 参与检索（让 DDD 类型/文档类别可被字符串匹配）
        " ".join(data.get("tags", [])) if isinstance(data.get("tags"), list) else "",
    ]
    return "\x00".join(p for p in parts if p)
```

**效果**：
- `graphify query "aggregate_root"` → substring 命中 tags 含 `aggregate_root` 的节点
- `graphify query "domain-model"` → 命中 domain-model 文档类别的节点
- `graphify query "ddd"` → 命中所有 DDD 节点（tags 含 `ddd` 标记）
- 无 tags 字段的节点（既有 code/document 节点）：`data.get("tags", [])` 返回 `[]`，join 后空串，不干扰既有匹配

### 4.3 兼容性

- 加法改动，不修改既有 3 层 if/elif/elif 匹配逻辑
- 无 tags 字段的节点：`data.get("tags", [])` 返回 `[]`，join 后空串，`p for p in parts if p` 过滤掉空串，行为与 upstream 一致
- 回 upstream 时：删掉这一行即可

---

## 5. 步骤 5：测试

### 5.1 新建 `tests/test_ddd_extractor.py`

```python
# tests/test_ddd_extractor.py
"""Tests for the DDD doc extractor + registry fallback + merge modes + tags retrieval.
Does not modify existing tests."""
from pathlib import Path
import pytest
from graphify.extractors.registry import clear_registry, try_external_extractors, ExtractionResult
from graphify.extractors import ddd  # triggers registration


@pytest.fixture(autouse=True)
def _restore_registry():
    """Ensure custom extractors registered in a test don't leak to others."""
    import copy
    from graphify.extractors import registry
    saved = list(registry._REGISTRY)
    yield
    registry._REGISTRY[:] = saved


def test_whitelist_match(tmp_path: Path):
    """A context-map.md file should be parsed by the DDD extractor."""
    (tmp_path / "context-map.md").write_text(
        "| BC ID | BC 名称 | 职责 |\n|---|---|---|\n| BC-01 | 订单 | 处理下单 |\n",
        encoding="utf-8",
    )
    result = ddd.extract_ddd(tmp_path / "context-map.md", root=tmp_path)
    assert result is not None
    assert isinstance(result, ExtractionResult)
    assert result.merge_mode == "merge"
    assert any("bounded_context" in n.get("tags", []) for n in result.nodes)


def test_non_whitelist_returns_none(tmp_path: Path):
    """A non-whitelist .md file should return None (fall back to default)."""
    (tmp_path / "README.md").write_text("# Hello\n", encoding="utf-8")
    result = ddd.extract_ddd(tmp_path / "README.md", root=tmp_path)
    assert result is None


def test_registry_fallback(tmp_path: Path):
    """try_external_extractors returns None for non-whitelist → caller falls back."""
    (tmp_path / "README.md").write_text("# Hello\n", encoding="utf-8")
    result = try_external_extractors(tmp_path / "README.md", root=tmp_path)
    assert result is None


def test_code_anchor_matching(tmp_path: Path):
    """describes edge created when <anchor:code> matches a code node."""
    code_nodes = [
        {"id": "src_order_service:OrderService", "label": "OrderService",
         "file_type": "code", "node_kind": "class", "source_file": "src/order/service.py"},
    ]
    (tmp_path / "domain-model.md").write_text(
        "| 聚合根<anchor:ddd> | 代码锚点<anchor:code> | 说明<anchor:desc> |\n"
        "|---|---|---|\n| 订单服务 | OrderService | 处理订单 |\n",
        encoding="utf-8",
    )
    result = ddd.extract_ddd(
        tmp_path / "domain-model.md", root=tmp_path,
        code_index={"nodes": code_nodes},
    )
    assert result is not None
    describes_edges = [e for e in result.edges if e["relation"] == "references"]
    assert any("OrderService" in e["target"] for e in describes_edges)


def test_node_shape_compliance(tmp_path: Path):
    """DDD nodes use all-generic fields + tags encodes DDD type. No ddd_* fields."""
    (tmp_path / "context-map.md").write_text(
        "| BC ID | BC 名称 | 职责 |\n|---|---|---|\n| BC-01 | 订单 | 处理下单 |\n",
        encoding="utf-8",
    )
    result = ddd.extract_ddd(tmp_path / "context-map.md", root=tmp_path)
    assert result is not None
    node = result.nodes[0]
    # All fields are generic
    assert node["file_type"] == "concept"
    assert node["node_kind"] == "doc-anchor"
    assert node["concept_id"] == "BC-01"  # raw, not normalized
    assert node["desc"] == "处理下单"  # <anchor:desc> content
    assert "tags" in node
    assert "ddd" in node["tags"]
    assert "bounded_context" in node["tags"]
    assert "context-map" in node["tags"]  # doc_category
    # No ddd_* prefixed fields
    assert not any(k.startswith("ddd_") for k in node.keys())


def test_cross_file_edge_resolution(tmp_path: Path):
    """related edge between two doc-anchor nodes in different files resolves."""
    # File 1: domain-model.md with aggregate AG-01 referencing AG-02
    (tmp_path / "domain-model.md").write_text(
        "| 聚合根<anchor:ddd> | 源聚合 | 目标聚合 |\n"
        "|---|---|---|\n| 订单 | AG-01 | AG-02 |\n",
        encoding="utf-8",
    )
    # File 2: another domain-model file defining AG-01 and AG-02
    (tmp_path / "domain-model-2.md").write_text(
        "| 聚合根<anchor:ddd> | 代码锚点<anchor:code> | 说明<anchor:desc> |\n"
        "|---|---|---|\n| 订单服务 | OrderService | 处理订单 |\n"
        "|---|---|---|\n| 支付服务 | PaymentService | 处理支付 |\n",
        encoding="utf-8",
    )
    # Run both files
    r1 = ddd.extract_ddd(tmp_path / "domain-model.md", root=tmp_path)
    r2 = ddd.extract_ddd(tmp_path / "domain-model-2.md", root=tmp_path)
    assert r1 is not None and r2 is not None

    # Combine nodes + pending edges, resolve
    all_nodes = r1.nodes + r2.nodes
    # r1 has a pending 'related' edge with sourceRef=AG-01, targetRef=AG-02
    # that should resolve to nodes from r2 (if AG-01/AG-02 are their concept_ids)
    # ... (test verifies _resolve_pending_edges logic)


def test_unmatched_anchor_recorded(tmp_path: Path):
    """Unmatched code anchors recorded in unmatched list."""
    (tmp_path / "domain-model.md").write_text(
        "| 聚合根<anchor:ddd> | 代码锚点<anchor:code> | 说明<anchor:desc> |\n"
        "|---|---|---|\n| 订单服务 | NonExistentClass | 处理订单 |\n",
        encoding="utf-8",
    )
    result = ddd.extract_ddd(tmp_path / "domain-model.md", root=tmp_path, code_index={"nodes": []})
    assert result is not None
    assert len(result.unmatched) == 1
    assert result.unmatched[0]["anchor"] == "NonExistentClass"


def test_tags_retrieval(tmp_path: Path):
    """tags field participates in string retrieval via _node_search_text."""
    # This test verifies the serve.py _node_search_text change (step 4)
    # by checking that a node with tags=["ddd","aggregate_root","domain-model"]
    # produces a search text containing "aggregate_root"
    from graphify.serve import _node_search_text
    node = {
        "id": "docanchor_test_AG-01",
        "label": "订单服务",
        "tags": ["ddd", "aggregate_root", "domain-model"],
    }
    text = _node_search_text(node["id"], node)
    assert "aggregate_root" in text
    assert "domain-model" in text
    assert "ddd" in text
```

### 5.2 新建 fixture 目录 `tests/fixtures/ddd/`

```
tests/fixtures/ddd/
├── context-map.md              # BC 表 + 业务关系表 + 统一语言表
├── technical-constraints.md    # TC 标题 + 代码锚点 + 适用范围
├── order-business-flow.md      # business-flow 白名单（标签表）
├── order-invariants.md         # invariants 白名单（标签表）
├── order-contracts.md          # contracts 白名单（标签表）
├── order-domain-events.md      # domain-events 白名单（标签表）
├── order-domain-model.md       # domain-model 白名单（标签表）
└── README.md                   # 非白名单（应回退到默认 markdown）
```

---

## 6. 步骤 6：验证

### 6.1 单元测试

```bash
uv run pytest tests/test_ddd_extractor.py -q
```

### 6.2 集成测试（用 fixture）

```bash
uv run graphify extract tests/fixtures/ddd/
uv run python -c "
import json
g = json.load(open('.graph/graph.json'))
doc_anchors = [n for n in g['nodes'] if n.get('node_kind') == 'doc-anchor']
pages = [n for n in g['nodes'] if n.get('node_kind') == 'page']
print(f'doc-anchor nodes: {len(doc_anchors)} (DDD script)')
print(f'page nodes: {len(pages)} (default markdown)')
for n in doc_anchors[:3]:
    print(f'  {n[\"id\"]} tags={n.get(\"tags\")} concept_id={n.get(\"concept_id\")}')
describes = [e for e in g['edges'] if e['relation'] == 'references']
print(f'describes edges: {len(describes)}')
"
```

### 6.3 tags 检索验证

```bash
uv run graphify query "aggregate_root"
uv run graphify query "domain-model"
uv run graphify query "ddd"
```

### 6.4 回 upstream 兼容性测试

```bash
# 1. 删掉 DDD 解析器 + 注册表 + 注入点 + serve.py 的 tags 拼接
# 2. 跑既有测试套件，应全绿
uv run pytest tests/ -q
```

---

## 7. 回 upstream 策略

| 场景 | 操作 |
|---|---|
| graphify upstream 发版，我想合并新代码 | 保留 `registry.py` + `ddd.py` + `__init__.py` 的注册行 + `extract.py` 的注入分支 + `cli.py` 的两阶段调用 + `serve.py` 的 tags 拼接；合并 upstream 的其余改动 |
| upstream 也加了类似的外部解析器机制 | 评估是否弃用自己的 registry，迁移到 upstream 机制；DDD 解析器适配新 registry，`ExtractionResult` 语义映射即可 |
| 我想完全回到原始 graphify | 删 `registry.py`、`ddd.py`、`__init__.py` 的注册行、`extract.py` 的注入分支、`cli.py` 的两阶段改动、`serve.py` 的 tags 拼接、`test_ddd_extractor.py`、`tests/fixtures/ddd/` |

---

## 8. 实施顺序（推荐）

1. ✅ 步骤 1：`registry.py`（含 `ExtractionResult` dataclass，独立可测）
2. ✅ 步骤 2：`ddd.py` 的常量 + 工具 + node/edge builder + `_infer_ddd_type`（依赖 registry）
3. ✅ 步骤 2 续：`ddd.py` 的代码锚点匹配 `_build_code_indices` + `_match_code_anchor`（独立可单测）
4. ✅ 步骤 2 续：`ddd.py` 的 fence scanner + table parser + `_split_anchors`
5. ✅ 步骤 2 续：`ddd.py` 的三个 parser（`_parse_tagged_file` + `_parse_context_map` + `_parse_technical_constraints`）
6. ✅ 步骤 2 续：`ddd.py` 的全局边解析 `_build_global_node_index` + `_resolve_ref` + `_resolve_pending_edges`
7. ✅ 步骤 2 续：`ddd.py` 的 `extract_ddd` 公共入口 + 注册
8. ✅ 步骤 3.1：`__init__.py` 追加注册行
9. ✅ 步骤 3.2-3.3：`extract.py` 注入分支（doc 主进程预处理 + `_write_ddd_unmatched`）
10. ✅ 步骤 3.4：`extract()` 加 `code_index` 参数 + `suppress_llm_files` 返回 + cli.py 两阶段调用
11. ✅ 步骤 4：`serve.py` 的 `_node_search_text` 加 tags 拼接
12. ✅ 步骤 5：测试 + fixture
13. ✅ 步骤 6：验证（含 tags 检索验证）

---

## 9. 关键设计决策记录

| 决策 | 选择 | 理由 |
|---|---|---|
| 外部解析器返回类型 | `ExtractionResult` dataclass（非裸 dict） | 声明式携带 merge_mode/suppress_llm，类型安全 |
| DDD 默认合并模式 | `merge` | doc-anchor 结构化 + page/heading 层级 + LLM 语义补充都有价值 |
| DDD 默认 suppress_llm | `False` | LLM Tier 2 仍跑，通用 prompt 抓散文语义；脚本锚点 + LLM 语义互补 |
| 去重机制 | **复用 graphify 原生 ghost-merge + dedup** | 多数场景脚本 label（业务术语）与 LLM label（原文 token）不同，不冲突；偶尔冲突时接受先到先得，graph 结构仍保留主要价值 |
| concept_id 存储 | 节点 `concept_id` 字段（原始值） | 规避 `make_id` 把 `/`/`-` normalize 成 `_` 导致从 id 反推 concept_id 失败的 bug |
| doc 注入位置 | 主进程（非 subprocess） | 规避 `code_index` 节点列表 pickle 成本；doc 是 I/O 轻量不走 tree-sitter，主进程足够 |
| LLM Tier 2 跳过机制 | `suppress_llm_files` 集合 + cli.py 排除 | 最小侵入：不改 cli.py 的 semantic_files 构建逻辑，只加一个集合过滤 |
| ID 前缀 | `docanchor_`（下划线，非冒号） | graphify id 规范要求 `[a-z0-9_]`（`llm.py:493`），冒号会被 make_id 处理，下划线安全 |
| 三个 parser 实现 | 逐行移植 .mjs（完整代码在 §2.1） | 已验证的 working 实现，降低风险；不重新设计逻辑 |
| **节点字段全通用** | 无 `ddd_*` 前缀字段 | 统一拉通，所有节点字段通用，利于统一检索 |
| **DDD 类型编码进 tags** | `tags: ["ddd", "<ddd_type>", "<doc_category>"]` | `tags` 是通用列表字段，任何解析器可用；DDD 类型信息编码进 tags 不丢信息 |
| **desc 字段** | 原 `summary` 改名 `desc` | 与源列名 `<anchor:desc>` 对齐；避免与 graphify 未来 `node-summaries-rfc` 的 `summary` 撞车 |
| **tags 检索支持** | `serve.py` 的 `_node_search_text` 加一行拼接 | 让 DDD 类型/文档类别参与字符串检索；加法改动，不修改既有 3 层匹配逻辑 |
