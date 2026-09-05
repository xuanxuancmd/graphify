"""learn.json v2（多视角学习内容）生成器的测试。

覆盖：业务流确定性生成（时序图/步骤/上下文）、架构视角（目录树/特性卡/
类图）、特性下钻六节（焦点行代码走读/抛错扫描/TODO 扫描）、LLM 增强
（mock + 缓存 + 防幻觉合并）、sidecar 读写（v1 视为空）、CLI 端到端
（--no-llm，含 features/*.md 落盘）、以及 to_html 注入与字节一致性。
"""

import json
import tempfile
from pathlib import Path

import networkx as nx
import pytest

from graphify.learn import (
    FEATURES_DIR_NAME,
    LEARN_SIDECAR_NAME,
    _kind_of,
    _structural_focal_lines,
    build_learn_data,
    load_learn_sidecar,
    run_learn,
)


def _make_graph():
    """graphify 形状的小图：入口文件 + 工具文件 + 符号 + 调用边 + 端点。"""
    G = nx.Graph()
    G.add_node("ep_login", label="POST:/rest/auth/login", file_type="code",
               source_file="src/api/user-api.yaml", source_location="L404",
               node_kind="endpoint", desc="Login and receive a JWT token.")
    G.add_node("src_main_py", label="main.py", file_type="code",
               source_file="src/main.py", source_location="L1",
               desc="程序入口。")
    G.add_node("src_main_run", label="run", file_type="code",
               source_file="src/main.py", source_location="L2",
               desc="启动服务。")
    G.add_node("src_util_py", label="util.py", file_type="code",
               source_file="src/util.py", source_location="L1",
               desc="工具函数库。")
    G.add_node("src_util_parse", label="parse_config", file_type="code",
               source_file="src/util.py", source_location="L2")
    G.add_node("src_util_big", label="big_algorithm", file_type="code",
               source_file="src/util.py", source_location="L4",
               desc="核心数据变换算法。")
    G.add_edge("ep_login", "src_main_run",
               relation="uses", _src="ep_login", _tgt="src_main_run")
    G.add_edge("src_main_py", "src_util_py",
               relation="imports", _src="src_main_py", _tgt="src_util_py")
    G.add_edge("src_main_run", "src_util_parse",
               relation="calls", _src="src_main_run", _tgt="src_util_parse")
    G.add_edge("src_main_run", "src_util_big",
               relation="calls", _src="src_main_run", _tgt="src_util_big")
    G.add_edge("src_util_py", "src_util_parse",
               relation="contains", _src="src_util_py", _tgt="src_util_parse")
    G.add_edge("src_util_py", "src_util_big",
               relation="contains", _src="src_util_py", _tgt="src_util_big")
    return G


def _make_root(tmp: Path) -> Path:
    """真实源码树：main.py 短；util.py 里 big_algorithm（L5 起）跨度大、含抛错。"""
    root = tmp / "proj"
    (root / "src" / "api").mkdir(parents=True)
    (root / "src" / "main.py").write_text(
        '"""程序入口。"""\n'
        "def run():\n"
        "    parse_config()\n"
        "    big_algorithm()\n",
        encoding="utf-8",
    )
    lines = ["'''工具库。'''"]
    lines.append("def parse_config():")
    lines.append("    return {}")
    lines.append("def big_algorithm():")
    lines.append("    # WHY: 核心数据变换，性能敏感")
    lines.append("    total = 0")
    lines.extend([f"    total += {i}  # 累加" for i in range(20)])
    lines.append("    if total < 0:")
    lines.append("        raise ValueError('negative')")
    lines.extend([f"    total += {i}" for i in range(30)])
    lines.append("    # TODO: 换成并行实现")
    lines.append("    return total")
    (root / "src" / "util.py").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return root


def _communities(G):
    return {0: ["src_main_py", "src_main_run", "ep_login"], 1: ["src_util_py", "src_util_parse", "src_util_big"]}


# ---------------------------------------------------------------------------
# 基础
# ---------------------------------------------------------------------------

class TestKindOf:
    def test_file_by_extension(self):
        assert _kind_of({"label": "main.py", "file_type": "code"}) == "file"

    def test_function_vs_class(self):
        assert _kind_of({"label": "parse_config", "file_type": "code"}) == "function"
        assert _kind_of({"label": "UserService", "file_type": "code"}) == "class"

    def test_concept(self):
        assert _kind_of({"label": "anything", "file_type": "concept"}) == "concept"


class TestFocalLines:
    def test_why_comment_and_branch_selected(self, tmp_path):
        root = _make_root(tmp_path)
        fl = _structural_focal_lines(root, "src/util.py", 4, 56)
        notes = " ".join(f["note"] for f in fl)
        assert any(f["line"] == 5 for f in fl)  # WHY 注释行入选（L5，得分 10）
        assert "total < 0" in notes  # 分支行入选

    def test_missing_file(self, tmp_path):
        assert _structural_focal_lines(tmp_path, "nope.py", 1, 10) == []


# ---------------------------------------------------------------------------
# 确定性生成（--no-llm 等效）
# ---------------------------------------------------------------------------

class TestStructural:
    def test_v3_schema_shape(self, tmp_path):
        root = _make_root(tmp_path)
        data = build_learn_data(_make_graph(), _communities(None), root=root)
        assert data["version"] == 3
        assert data["backend"] == "none"
        assert data["project_summary"]
        # v3 新字段
        assert "project_overview" in data
        assert "tour" in data and isinstance(data["tour"], list)
        assert "domains" in data and isinstance(data["domains"], list)
        assert "node_notes" in data and isinstance(data["node_notes"], dict)
        # 既有字段
        assert isinstance(data["flows"], list) and data["flows"]
        assert isinstance(data["architecture"], dict)
        assert isinstance(data["features"], list) and data["features"]
        # 每个 feature 有难度和 UML 选型
        for feat in data["features"]:
            assert "difficulty" in feat
            assert feat["difficulty"] in ("simple", "standard", "complex")
            assert "uml_needed" in feat

    def test_flow_from_endpoint(self, tmp_path):
        """端点节点应成为业务流种子：时序图 + 步骤 + 上下文齐全。"""
        root = _make_root(tmp_path)
        data = build_learn_data(_make_graph(), _communities(None), root=root)
        flow = data["flows"][0]
        assert "POST /rest/auth/login" in flow["entry"]
        assert flow["mermaid"].startswith("sequenceDiagram")
        assert "autonumber" in flow["mermaid"]
        assert "Client ->> P1" in flow["mermaid"]
        assert flow["participants"]
        assert flow["steps"]
        for s in flow["steps"]:
            assert s["msg"] and s["desc"] and s["cite"]
        assert flow["context"]["node"]
        assert flow["context"]["anchors"]
        # 内部字段不泄漏到 sidecar。
        assert "path" not in flow

    def test_architecture_tree_and_features(self, tmp_path):
        root = _make_root(tmp_path)
        data = build_learn_data(_make_graph(), _communities(None), root=root)
        arch = data["architecture"]
        labels = [r["label"] for r in arch["tree"]]
        assert any("src/" in l for l in labels)
        assert any("util.py" in l for l in labels)
        for r in arch["tree"]:
            assert r["kind"] in ("dir", "file")
        assert arch["features"]
        for c in arch["features"]:
            assert c["name"] and c["flow_id"]

    def test_feature_doc_sections(self, tmp_path):
        """特性下钻：按难度分层生成章节。零 LLM 时小图 fixture 落在 simple 档。
        simple=01+06，standard=01+02+03+06，complex=01-06+UML。
        """
        root = _make_root(tmp_path)
        data = build_learn_data(_make_graph(), _communities(None), root=root)
        feat = data["features"][0]
        nos = [s["no"] for s in feat["sections"]]
        # 难度字段存在
        assert feat["difficulty"] in ("simple", "standard", "complex")
        assert isinstance(feat["uml_needed"], list)
        # 章节按难度分层：至少有 01 和 06
        assert "01" in nos
        assert "06" in nos
        # 01 概览有内容
        sec1 = next(s for s in feat["sections"] if s["no"] == "01")
        assert sec1["blocks"]
        # 06 限制有内容
        sec6 = next(s for s in feat["sections"] if s["no"] == "06")
        assert sec6["blocks"]
        # doc_md 与 outline 一致
        assert feat["doc_md"].startswith("# ")
        assert len(feat["outline"]) == len(feat["sections"])
        assert feat["anchors"]
        assert "involved_files" not in feat


# ---------------------------------------------------------------------------
# LLM 增强
# ---------------------------------------------------------------------------

class TestLLM:
    @staticmethod
    def _mock(prompt, **kw):
        """按 prompt 类型返回卡片/流程/概览增强。"""
        if "业务流" in prompt[:80]:
            import re as _re
            n = len(_re.findall(r"^第 \d+ 步", prompt, _re.M))
            return json.dumps({
                "name": "登录流（增强）",
                "context_intent": "增强后的主符号说明。",
                "steps": [{"desc": f"第 {i + 1} 步的增强讲解。"} for i in range(n)],
            }, ensure_ascii=False)
        if "深度分析文档" in prompt[:80]:
            return json.dumps({
                "overview": "增强概览段落。",
                "tech_points": [{"name": "增强技术点", "why": "增强理由"}],
                "perf": ["增强性能分析"],
                "reliability": ["增强可靠性分析"],
                "focal_notes": {},
            }, ensure_ascii=False)
        return json.dumps({"summary": "增强版项目概览。"}, ensure_ascii=False)

    def test_llm_enhancement_merges(self, tmp_path, monkeypatch):
        root = _make_root(tmp_path)
        G = _make_graph()
        monkeypatch.setattr("graphify.learn._llm_call", self._mock)
        data = build_learn_data(G, _communities(None), root=root, backend="claude")
        assert data["backend"] == "claude"
        assert data["project_summary"] == "增强版项目概览。"
        flow = data["flows"][0]
        assert flow["name"] == "登录流（增强）"
        assert flow["context"]["intent"] == "增强后的主符号说明。"
        assert any("增强讲解" in s["desc"] for s in flow["steps"])
        feat = data["features"][0]
        sec1 = next(s for s in feat["sections"] if s["no"] == "01")
        assert sec1["blocks"][0]["text"] == "增强概览段落。"
        assert "增强技术点" in json.dumps(feat, ensure_ascii=False)
        # 架构特性卡跟随 LLM 化的流程名。
        assert data["architecture"]["features"][0]["name"] == "登录流（增强）"

    def test_llm_failure_falls_back(self, tmp_path, monkeypatch):
        root = _make_root(tmp_path)

        def boom(prompt, **kw):
            raise RuntimeError("down")

        monkeypatch.setattr("graphify.learn._llm_call", boom)
        data = build_learn_data(_make_graph(), _communities(None), root=root, backend="claude")
        assert data["flows"][0]["steps"][0]["desc"]  # 结构化内容仍在

    def test_incremental_cache(self, tmp_path, monkeypatch):
        root = _make_root(tmp_path)
        calls = []
        monkeypatch.setattr("graphify.learn._llm_call",
                            lambda p, **kw: (calls.append(p), self._mock(p))[1])
        first = build_learn_data(_make_graph(), _communities(None), root=root, backend="claude")
        n1 = len(calls)
        assert n1 > 0
        # 第二次：源码未变 + previous → 全部命中缓存，零 LLM 调用。
        calls.clear()
        second = build_learn_data(_make_graph(), _communities(None), root=root, backend="claude", previous=first)
        assert calls == []
        assert second["flows"][0]["name"] == "登录流（增强）"
        assert second["features"][0]["doc_md"] == first["features"][0]["doc_md"]
        # 源码变更 → 相关流程重新生成。
        (root / "src" / "util.py").write_text("'''改了。'''\ndef big_algorithm():\n    return 1\n", encoding="utf-8")
        calls.clear()
        third = build_learn_data(_make_graph(), _communities(None), root=root, backend="claude", previous=second)
        assert calls, "变更文件相关内容应重新生成"


# ---------------------------------------------------------------------------
# Sidecar 与 CLI
# ---------------------------------------------------------------------------

class TestSidecar:
    def test_load_missing(self, tmp_path):
        assert load_learn_sidecar(tmp_path / "graph.html") == {}

    def test_load_garbage(self, tmp_path):
        (tmp_path / "learn.json").write_text("not json", encoding="utf-8")
        assert load_learn_sidecar(tmp_path / "graph.html") == {}

    def test_v1_rejected_as_empty(self, tmp_path):
        """v1（卡片+漫游）sidecar 视为空 —— 前端提示重新生成。"""
        (tmp_path / LEARN_SIDECAR_NAME).write_text(
            json.dumps({"version": 1, "nodes": {"a": {}}}), encoding="utf-8")
        assert load_learn_sidecar(tmp_path / "graph.html") == {}

    def test_v2_rejected_as_stale(self, tmp_path):
        """v2 sidecar 视为空 —— v3 升级后前端提示重新生成。"""
        (tmp_path / LEARN_SIDECAR_NAME).write_text(
            json.dumps({"version": 2, "flows": [], "features": []}), encoding="utf-8")
        assert load_learn_sidecar(tmp_path / "graph.html") == {}

    def test_v3_loaded(self, tmp_path):
        (tmp_path / LEARN_SIDECAR_NAME).write_text(
            json.dumps({"version": 3, "flows": [], "features": []}), encoding="utf-8")
        data = load_learn_sidecar(tmp_path / "graph.html")
        assert data["version"] == 3


class TestRunLearnCLI:
    def test_no_llm_end_to_end(self, tmp_path, capsys):
        """--no-llm：learn.json + features/*.md + graph.html 全链路。"""
        from graphify.cluster import cluster
        from graphify.export import to_json

        root = _make_root(tmp_path)
        G = _make_graph()
        communities = cluster(G)
        graph_dir = root / ".graph"
        graph_dir.mkdir()
        to_json(G, communities, str(graph_dir / "graph.json"))

        run_learn([str(root), "--no-llm"])

        data = json.loads((graph_dir / LEARN_SIDECAR_NAME).read_text(encoding="utf-8"))
        assert data["version"] == 3 and data["backend"] == "none"
        assert data["flows"] and data["features"]
        # v3 新字段
        assert "project_overview" in data
        assert "tour" in data
        assert "domains" in data
        assert "node_notes" in data
        md_files = list((graph_dir / FEATURES_DIR_NAME).glob("*.md"))
        assert md_files
        for f in md_files:
            assert f.read_text(encoding="utf-8").startswith("# ")
        html = (graph_dir / "graph.html").read_text(encoding="utf-8")
        assert "const LEARN = {" in html
        assert "initLearn" in html
        out = capsys.readouterr().out
        assert "learn.json 写入完成" in out
        assert "features" in out

    def test_help(self, capsys):
        run_learn(["--help"])
        assert "Usage: graphify learn" in capsys.readouterr().out

    def test_missing_graph_exits(self, tmp_path):
        with pytest.raises(SystemExit):
            run_learn([str(tmp_path / "nowhere")])


# ---------------------------------------------------------------------------
# HTML 注入
# ---------------------------------------------------------------------------

class TestHtmlInjection:
    def _learn(self):
        return {
            "version": 3, "backend": "none", "project_summary": "测试概览",
            "project_overview": {
                "dir_structure": [{"label": "src/", "kind": "dir", "note": "2 文件"}],
                "feature_intro": "测试概览",
                "entry_points": [{"type": "http", "path": "src/api.py L1", "handler": "login()"}],
                "tech_stack": ["Python"],
            },
            "tour": [{"order": 1, "title": "入口", "desc": "从这开始", "nodeIds": ["n1"], "community_id": 0}],
            "domains": [{"id": "domain_0", "name": "核心域", "community_id": 0, "node_count": 5,
                         "key_files": ["src/api.py"], "key_symbols": ["login()"],
                         "flows": [], "cross_domain": [], "desc": "", "source": "cluster"}],
            "node_notes": {},
            "flows": [{
                "id": "flow_login", "name": "登录流", "entry": "POST /x",
                "meta": "2 参与者", "provenance": "3 条调用边",
                "participants": ["auth", "util"],
                "mermaid": "sequenceDiagram\n    autonumber\n    Client ->> P1: go",
                "steps": [{"msg": "a → b", "desc": "d", "cite": "c"}],
                "context": {"node": ".run()", "intent": "i", "anchors": ["a.py L1"]},
            }],
            "architecture": {"tree": [{"label": "src/", "kind": "dir", "note": "2 文件"}],
                             "features": [{"name": "登录流", "desc": "d", "modules": "m", "flow_id": "flow_login"}],
                             "class_diagram": "classDiagram\n    class A {}"},
            "features": [{
                "id": "feat_login", "name": "登录认证", "flow_id": "flow_login",
                "difficulty": "standard", "uml_needed": ["sequence"],
                "sections": [{"no": "01", "title": "特性概览", "blocks": [{"type": "p", "text": "概览文本"}]}],
                "outline": [{"no": "01", "title": "特性概览"}],
                "anchors": ["a.py L1"], "doc_md": "# 登录认证",
            }],
        }

    def _render(self, tmp_path, **kw):
        from graphify.cluster import cluster
        from graphify.export import to_html

        G = _make_graph()
        out = tmp_path / "graph.html"
        to_html(G, cluster(G), str(out), **kw)
        return out.read_text(encoding="utf-8")

    def test_v3_data_renders(self, tmp_path):
        html = self._render(tmp_path, learn_data=self._learn())
        assert "const LEARN = {" in html
        assert "initLearn" in html and "switchLearn" in html
        # sidecar 自动拾取。
        sidecar = tmp_path / LEARN_SIDECAR_NAME
        sidecar.write_text(json.dumps(self._learn(), ensure_ascii=False), encoding="utf-8")
        html2 = self._render(tmp_path)
        assert "const LEARN = {" in html2

    def test_empty_state_hint(self, tmp_path):
        html = self._render(tmp_path)
        assert "/graphify learn" in html
        assert "const LEARN = null;" in html

    def test_no_learn_data_byte_identical(self, tmp_path):
        from graphify.cluster import cluster
        from graphify.export import to_html

        G = _make_graph()
        a = tmp_path / "a.html"
        b = tmp_path / "b.html"
        to_html(G, cluster(G), str(a))
        to_html(G, cluster(G), str(b), learn_data={})
        ca = a.read_text(encoding="utf-8").replace("a.html", "X.html")
        cb = b.read_text(encoding="utf-8").replace("b.html", "X.html")
        assert ca == cb

    def test_mermaid_cdn_pinned_with_sri(self, tmp_path):
        html = self._render(tmp_path)
        assert "cdn.jsdelivr.net/npm/mermaid@10.9.1" in html
        assert 'integrity="sha384-WmdflGW9aGfoBdHc4rRyWzYuAjEmDwMdGdiPNacbwfGKxBW/SO6guzuQ76qjnSlr"' in html
