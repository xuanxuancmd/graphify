# Plan: 解析器扩展机制差异修复

> 关联:`spec.md`(同目录)是完整设计。本文只体现**已实现 vs 待实现**的差异(gap),每步是可独立执行、可验证的原子改动。
>
> 执行顺序:Gap-1 → Gap-2 → Gap-3 → Gap-4。前三个 Gap 有依赖关系(自动扫描需要先解除硬编码范围),Gap-4 独立。

---

## Gap-1: 解除 Tier 1 扫描范围硬编码,支持任意文件类型

### 现状

`graphify/extract.py:5827`:

```python
_DOC_EXTS_FOR_EXTERNAL = {".md", ".mdx", ".qmd", ".skill"}
```

只对这 4 种扩展名调 `try_external_extractors`。YAML/JSON/CSV 等文件不经过外部解析器,直接走默认 dispatch。

### 目标

对**任意扩展名**的文件都先调 `try_external_extractors`,解析器自己 `return None` decline 的回退默认 dispatch。

### 改动

**文件**: `graphify/extract.py`

**位置**: `extract.py:5827-5873`(外部解析器预处理块)

**改动内容**:

1. 删除 `_DOC_EXTS_FOR_EXTERNAL` 硬编码集合
2. 把 `if _path.suffix not in _DOC_EXTS_FOR_EXTERNAL: continue` 改为:对所有文件都调 `try_external_extractors`(不按扩展名过滤)
3. 保留现有的 `merge_mode` 分流逻辑(merge/replace/supplement_only)不变
4. 对于非 doc 扩展名的文件,`merge` 模式下的"默认 markdown"分支需要跳过(因为 `extract_markdown` 只处理 doc 文件)— 加判断:如果文件扩展名不在 markdown 范围内,`merge` 模式退化为 `replace`(只用外部结果)

**伪代码**:

```python
# extract.py — 替换 _DOC_EXTS_FOR_EXTERNAL 硬编码
suppress_llm_files: set[str] = set()
if code_index is not None:
    from graphify.extractors.registry import try_external_extractors
    _DOC_EXTS = {".md", ".mdx", ".qmd", ".skill"}  # 仅用于 merge 模式判断是否跑 extract_markdown
    _external_handled: set[int] = set()
    for _i, _path in enumerate(paths):
        # 不再按扩展名过滤, 所有文件都尝试外部解析器
        try:
            _ext = try_external_extractors(_path, root=root, code_index=code_index)
        except Exception:
            _ext = None
        if _ext is None:
            continue
        _external_handled.add(_i)
        if _ext.suppress_llm:
            suppress_llm_files.add(str(_path))
        if _ext.merge_mode == "merge" and _path.suffix in _DOC_EXTS:
            # merge 模式 + doc 文件: 外部 + 默认 extract_markdown 合并
            # (现有逻辑不变)
            ...
        else:
            # replace / supplement_only / 非doc文件的merge退化:
            # 只用外部结果
            per_file[_i] = {
                "nodes": list(_ext.nodes), "edges": list(_ext.edges),
                "hyperedges": list(_ext.hyperedges),
                "pending_edges": list(_ext.pending_edges),
                "input_tokens": 0, "output_tokens": 0,
            }
            if _ext.unmatched:
                _write_ddd_unmatched(cache_location, _ext.unmatched)
```

### 验证

```bash
# 写一个 YAML 解析器 (graphify/extractors/yaml_config.py), 注册后跑:
uv run graphify extract tests/fixtures/yaml/sample.yaml
# 验证 graph.json 含 YAML 解析器产出的节点
uv run python -c "
import json
g = json.load(open('graphify-out/graph.json'))
yaml_nodes = [n for n in g['nodes'] if 'yaml_config' in n.get('tags', [])]
assert len(yaml_nodes) > 0, 'YAML parser nodes missing'
print(f'OK: {len(yaml_nodes)} YAML nodes')
"
```

### 测试

新建 `tests/test_extractor_arbitrary_types.py`:

```python
def test_yaml_file_routed_to_external_extractor(tmp_path):
    """非 doc 扩展名文件也能被外部解析器处理。"""
    # 注册一个处理 .yaml 的解析器
    # 写 sample.yaml
    # 调 extract()
    # 断言 graph.json 含该解析器产出的节点
```

---

## Gap-2: 内置自动扫描目录

### 现状

注册靠手动在 `graphify/extractors/__init__.py:18` 加 import 行:

```python
from graphify.extractors import ddd  # noqa: F401  — triggers @register_doc_extractor
```

新增解析器需改 graphify 源码。

### 目标

内置目录 `graphify/extractors/custom/` 自动扫描,放入 `.py` 文件自动注册,不需手动 import。单个解析器 import 失败不拖垮启动。

### 改动

**新建目录**: `graphify/extractors/custom/`

**新建文件**: `graphify/extractors/custom/__init__.py`(空文件,标记为 package)

**移动**: `graphify/extractors/ddd.py` → `graphify/extractors/custom/ddd.py`

**修改**: `graphify/extractors/__init__.py`

- 删除 `from graphify.extractors import ddd  # noqa: F401`(手动注册行)
- 末尾追加自动扫描逻辑:

```python
# graphify/extractors/__init__.py 末尾追加
import importlib
import pkgutil

def _scan_builtin_custom_extractors():
    """自动扫描 graphify/extractors/custom/ 下的 .py 模块, 触发 @register_doc_extractor。

    每个模块独立 try/except ImportError, 单个失败不拖垮启动。
    """
    _custom_dir = Path(__file__).parent / "custom"
    if not _custom_dir.is_dir():
        return
    for module_info in pkgutil.iter_modules([str(_custom_dir)]):
        if module_info.name.startswith("_"):
            continue  # 跳过 __init__ 等私有模块
        try:
            importlib.import_module(f"graphify.extractors.custom.{module_info.name}")
        except ImportError as e:
            import sys
            print(f"  warning: custom extractor '{module_info.name}' failed to load: {e}", file=sys.stderr)

_scan_builtin_custom_extractors()
```

**更新 import 路径**: 所有引用 `graphify.extractors.ddd` 的地方改为 `graphify.extractors.custom.ddd`:
- `tests/test_ddd_extractor.py:9-16` 的 import
- `docs/extending-doc-extractors/spec.md`(历史文档,可选更新)

### 验证

```bash
# 1. 确认 ddd.py 移到 custom/ 后仍自动注册
uv run python -c "
from graphify.extractors.registry import _REGISTRY
import graphify.extractors  # 触发自动扫描
print(f'registered: {len(_REGISTRY)} extractors')
assert any('extract_ddd' in fn.__name__ for fn in _REGISTRY), 'DDD not auto-registered'
print('OK: DDD auto-registered via custom/ scan')
"

# 2. 确认 import 失败不拖垮启动
# 在 custom/ 下放一个 import 失败的 .py
uv run python -c "import graphify.extractors"  # 应正常退出, stderr 有 warning
```

### 测试

新建 `tests/test_custom_dir_scan.py`:

```python
def test_builtin_custom_dir_auto_scan():
    """graphify/extractors/custom/ 下的模块自动注册。"""
    from graphify.extractors.registry import _REGISTRY
    import graphify.extractors
    assert any(fn.__name__ == "extract_ddd" for fn in _REGISTRY)

def test_failed_import_does_not_crash(tmp_path, monkeypatch):
    """单个解析器 import 失败不拖垮启动。"""
    # 在 custom/ 下放一个 import 失败的 .py, 验证 graphify 正常 import
```

---

## Gap-3: 项目级目录 + 优先级

### 现状

无项目级目录。解析器和内置语言解析器混在 `graphify/extractors/` 同一目录,合并 upstream 时 diff 不干净。

### 目标

项目级目录 `.graph/extension/extractors/` 自动扫描,项目级优先级高于内置(同名解析器项目级覆盖内置)。

### 改动

#### 3.1 `registry.py` 加 priority 参数

**文件**: `graphify/extractors/registry.py`

**修改** `register_doc_extractor` 函数:

```python
def register_doc_extractor(
    fn: Callable[..., "ExtractionResult | None"],
    *,
    priority: str = "append",  # "append" (内置默认) | "prepend" (项目级, 优先)
) -> Callable[..., "ExtractionResult | None"]:
    """Register an external doc extractor.

    priority:
        "append"  — 追加到尾部(内置默认)
        "prepend" — 插入头部(项目级, 优先于内置)
    """
    if fn not in _REGISTRY:
        if priority == "prepend":
            _REGISTRY.insert(0, fn)
        else:
            _REGISTRY.append(fn)
    return fn
```

**向后兼容**: 现有 `@register_doc_extractor` 调用不带 `priority` 参数,默认 `"append"`,行为不变。

#### 3.2 `__init__.py` 加项目级目录扫描

**文件**: `graphify/extractors/__init__.py`

在 `_scan_builtin_custom_extractors()` 之后追加:

```python
def _scan_project_custom_extractors():
    """自动扫描 .graph/extension/extractors/ (相对于 CWD) 下的 .py 模块。

    项目级优先级高于内置: 注册时 prepend 到 _REGISTRY 头部。
    """
    _project_dir = Path.cwd() / ".graph" / "extension" / "extractors"
    if not _project_dir.is_dir():
        return
    import sys
    if str(_project_dir) not in sys.path:
        sys.path.insert(0, str(_project_dir))
    for module_info in pkgutil.iter_modules([str(_project_dir)]):
        if module_info.name.startswith("_"):
            continue
        try:
            mod = importlib.import_module(module_info.name)
            # 项目级模块用 @register_doc_extractor(priority="prepend") 自注册
            # 但模块内部已经用了 @register_doc_extractor 装饰器,
            # 我们需要在模块加载后把它的解析器从 _REGISTRY 尾部移到头部
            # (除非模块内部已经用了 priority="prepend")
            # 简单方案: 模块加载后, 检查 _REGISTRY 尾部是否有该模块的解析器, 移到头部
        except ImportError as e:
            import sys
            print(f"  warning: project extractor '{module_info.name}' failed to load: {e}", file=sys.stderr)

_scan_project_custom_extractors()
```

**替代方案(更简洁)**: 让项目级解析器在 `@register_doc_extractor` 装饰器调用时检测自身是否在项目级目录,自动用 `priority="prepend"`。但这需要解析器知道自己的文件路径,增加复杂度。

**推荐方案**: 项目级解析器在模块加载后,graphify 把该模块注册的所有解析器从 `_REGISTRY` 尾部移到头部。实现:

```python
def _scan_project_custom_extractors():
    _project_dir = Path.cwd() / ".graph" / "extension" / "extractors"
    if not _project_dir.is_dir():
        return
    import sys
    if str(_project_dir) not in sys.path:
        sys.path.insert(0, str(_project_dir))
    from graphify.extractors.registry import _REGISTRY
    for module_info in pkgutil.iter_modules([str(_project_dir)]):
        if module_info.name.startswith("_"):
            continue
        _before = set(id(fn) for fn in _REGISTRY)
        try:
            importlib.import_module(module_info.name)
        except ImportError as e:
            print(f"  warning: project extractor '{module_info.name}' failed to load: {e}", file=sys.stderr)
            continue
        _after = _REGISTRY
        # 把新注册的解析器从尾部移到头部 (项目级优先)
        _new = [fn for fn in _after if id(fn) not in _before]
        for fn in _new:
            _REGISTRY.remove(fn)
            _REGISTRY.insert(0, fn)
```

#### 3.3 目录结构

```
graphify/extractors/custom/        # 内置扩展(随包发布, Gap-2 创建)
    ├── __init__.py
    └── ddd.py                     # DDD 解析器

<project>/.graph/extension/extractors/   # 项目级扩展(用户/团队自定义)
    ├── __init__.py                # 空文件
    └── my_yaml_parser.py          # 用户自定义
```

### 验证

```bash
# 1. 项目级目录自动扫描
mkdir -p .graph/extension/extractors
echo 'from graphify.extractors.registry import register_doc_extractor, ExtractionResult
@register_doc_extractor
def extract_my_yaml(path, *, root, code_index=None):
    if path.suffix not in (".yaml", ".yml"):
        return None
    return ExtractionResult(nodes=[{"id": "my_yaml_node", "label": "MyYAML", "file_type": "concept", "source_file": str(path)}], edges=[])
' > .graph/extension/extractors/my_yaml_parser.py
touch .graph/extension/extractors/__init__.py

uv run python -c "
import graphify.extractors
from graphify.extractors.registry import _REGISTRY
assert any(fn.__name__ == 'extract_my_yaml' for fn in _REGISTRY), 'project extractor not registered'
print('OK: project-level extractor auto-registered')
"

# 2. 项目级优先级 > 内置
# 在项目级放一个和内置同名的解析器, 验证项目级赢
uv run python -c "
import graphify.extractors
from graphify.extractors.registry import _REGISTRY, try_external_extractors
# 项目级应在 _REGISTRY 头部
print('registry order:', [fn.__name__ for fn in _REGISTRY[:3]])
"
```

### 测试

新建 `tests/test_project_extractors.py`:

```python
def test_project_dir_auto_scan(tmp_path, monkeypatch):
    """项目级目录 .graph/extension/extractors/ 自动扫描。"""
    monkeypatch.chdir(tmp_path)
    _create_project_extractor(tmp_path, "my_test.py")
    import graphify.extractors
    from graphify.extractors.registry import _REGISTRY
    assert any(fn.__name__ == "extract_my_test" for fn in _REGISTRY)

def test_project_priority_overrides_builtin(tmp_path, monkeypatch):
    """项目级解析器优先于内置同名解析器。"""
    # 内置 + 项目级同名, 验证项目级赢
```

---

## Gap-4: Tier 2 prompt registry

### 现状

Tier 2 无扩展点。`llm.py` 的 `_EXTRACTION_SYSTEM` 是全局单一通用 prompt,所有 doc 走同一个 prompt。

### 目标

提示词型"解析器"以 YAML 声明文件定义自定义 prompt + output schema,放 `.graph/extension/prompts/`,被 Tier 2 加载,按 per-file 路由。

### 改动

#### 4.1 新建 `graphify/prompt_registry.py`

```python
"""Tier 2 prompt registry — 提示词型解析器扩展点。

声明文件放 .graph/extension/prompts/*.yaml, 自动扫描加载。
Tier 2 对每个文件先查 registry, 命中则用自定义 prompt, 未命中用默认。
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import fnmatch


@dataclass
class PromptSpec:
    name: str
    description: str
    match: dict                    # {extensions, filenames, path_patterns, content_contains}
    prompt: str                    # prompt 模板, {content} 占位符替换文件内容
    suppress_default_prompt: bool = True
    output_schema: dict | None = None


_REGISTRY: list[PromptSpec] = []


def load_prompts_from_dir(prompt_dir: Path) -> None:
    """扫描目录加载所有 .yaml 声明文件。"""
    import yaml
    if not prompt_dir.is_dir():
        return
    for yaml_file in sorted(prompt_dir.glob("*.yaml")):
        try:
            data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
            spec = _parse_prompt_spec(data)
            if spec:
                _REGISTRY.append(spec)
        except Exception as e:
            import sys
            print(f"  warning: prompt spec '{yaml_file.name}' failed to load: {e}", file=sys.stderr)


def find_prompt(path: Path, root: Path) -> PromptSpec | None:
    """查找匹配文件的 prompt spec, 按注册顺序第一个命中赢。"""
    try:
        rel_path = path.resolve().relative_to(root.resolve()).as_posix() if root else str(path)
    except Exception:
        rel_path = str(path)
    for spec in _REGISTRY:
        if _matches(spec, path, rel_path):
            return spec
    return None


def _matches(spec: PromptSpec, path: Path, rel_path: str) -> bool:
    match = spec.match
    exts = match.get("extensions", [])
    names = match.get("filenames", [])
    patterns = match.get("path_patterns", [])
    contains = match.get("content_contains", [])

    has_rule = bool(exts or names or patterns or contains)
    if not has_rule:
        return False

    if exts and path.suffix.lower() in [e.lower() for e in exts]:
        return True
    if names and path.name.lower() in [n.lower() for n in names]:
        return True
    if patterns and any(fnmatch.fnmatch(rel_path, p) for p in patterns):
        return True
    if contains:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")[:4096]
            if any(c in content for c in contains):
                return True
        except Exception:
            pass
    return False


def _parse_prompt_spec(data: dict) -> PromptSpec | None:
    if not data:
        return None
    return PromptSpec(
        name=data.get("name", "unnamed"),
        description=data.get("description", ""),
        match=data.get("match", {}),
        prompt=data.get("prompt", ""),
        suppress_default_prompt=data.get("suppress_default_prompt", True),
        output_schema=data.get("output_schema"),
    )


def clear_registry() -> None:
    _REGISTRY.clear()
```

#### 4.2 `cli.py` 集成 prompt registry

**文件**: `graphify/cli.py`

**位置**: `cli.py:3809` 附近(`from graphify.llm import _extraction_system` 之后)

**改动**: 加载 prompt registry,对每个 semantic_file 查 registry:

```python
# cli.py — 在 semantic extraction 循环之前加
from graphify.prompt_registry import find_prompt, load_prompts_from_dir

# 启动时加载 prompt registry (一次)
load_prompts_from_dir(Path.cwd() / ".graph" / "extension" / "prompts")

# 对每个 semantic_file 分流: 自定义 prompt vs 默认 prompt
_custom_prompt_files: dict[str, PromptSpec] = {}
_default_prompt_files: list[str] = []
for _p in semantic_files:
    _spec = find_prompt(_p, target)
    if _spec and _spec.suppress_default_prompt:
        _custom_prompt_files[str(_p)] = _spec
    else:
        _default_prompt_files.append(str(_p))

# _default_prompt_files 走现有逻辑 (sem_prompt + extract_files_direct)
# _custom_prompt_files 单独调 LLM, 用 spec.prompt 替换 {content}
```

**headless CLI 路径**: `_custom_prompt_files` 的文件用 `llm.py` 的 `_call_llm` 调 LLM,prompt 是 `spec.prompt.replace("{content}", content)`,产出 JSON 后校验 `spec.output_schema`。

**IDE 会话内路径**: skill 指令识别 `.graph/extension/prompts/` 目录(需要更新 skill 文件,但这是 skillgen 的事,不在本 plan 范围)。

#### 4.3 声明文件目录

```
<project>/.graph/extension/prompts/
    └── api-spec.yaml    # 示例声明文件
```

### 验证

```bash
# 1. prompt registry 加载
mkdir -p .graph/extension/prompts
cat > .graph/extension/prompts/test.yaml << 'EOF'
name: "test-prompt"
description: "test"
match:
  extensions: [".yaml"]
prompt: |
  Extract from: {content}
EOF

uv run python -c "
from graphify.prompt_registry import load_prompts_from_dir, find_prompt, clear_registry
from pathlib import Path
clear_registry()
load_prompts_from_dir(Path.cwd() / '.graph' / 'extension' / 'prompts')
spec = find_prompt(Path('test.yaml'), Path('.'))
assert spec is not None
assert spec.name == 'test-prompt'
print('OK: prompt registry loads and matches')
"

# 2. headless CLI 用自定义 prompt
uv run graphify extract .graph/extension/prompts/test.yaml --backend claude-cli
# 验证 LLM 收到的 prompt 是自定义的 (mock 或日志验证)
```

### 测试

新建 `tests/test_prompt_registry.py`:

```python
def test_prompt_spec_loading(tmp_path):
    """YAML 声明文件正确加载为 PromptSpec。"""
    # 写 yaml, load_prompts_from_dir, 断言 _REGISTRY 含 PromptSpec

def test_find_prompt_by_extension(tmp_path):
    """按扩展名匹配文件。"""
    # spec match.extensions=[".yaml"], find_prompt(yaml_file) 返回 spec

def test_find_prompt_by_filename(tmp_path):
    """按文件名匹配。"""

def test_find_prompt_by_path_pattern(tmp_path):
    """按 glob 路径匹配。"""

def test_find_prompt_by_content_contains(tmp_path):
    """按内容包含匹配。"""

def test_no_match_returns_none(tmp_path):
    """不匹配的文件返回 None。"""

def test_failed_yaml_load_does_not_crash(tmp_path):
    """YAML 解析失败不拖垮启动。"""

def test_custom_prompt_replaces_content_placeholder(tmp_path):
    """prompt 模板的 {content} 占位符被文件内容替换。"""
```

---

## Gap-5: 三阶段提取顺序(代码 → 配置文件 → 文档)

### 现状

当前是**两阶段**(`cli.py:3725-3758`):

```
阶段 1: _ast_extract(code_files)
  → code(.py/.ts/.go...) + 配置 JSON(.json) + 包清单(pyproject.toml/Cargo.toml/apm.yml)
  → 配置 JSON 和代码混合在同一批次

阶段 2: _doc_extract(doc_files, code_index=...)
  → .md + .yaml + .txt + .rst + .html
```

`detect.py:503-518` `classify_file()` 把 `.json` 归入 `CODE_EXTENSIONS`(`detect.py:44`),包清单通过 `is_package_manifest_path()` 也归入 CODE。所以配置 JSON 和包清单跟代码一起在阶段 1 处理。

### 目标

三阶段(包清单除外,跟代码一起在阶段 1):

```
阶段 1: code AST 提取
  → code(.py/.ts/.go...) + 包清单(pyproject.toml/Cargo.toml/apm.yml/go.mod/pom.xml)
  → 产出 code 节点 + 包清单 canonical package 节点

阶段 2: 配置文件提取 (新阶段)
  → 配置 JSON(package.json/tsconfig.json/composer.json/...) — 非 .md 类
  → 传入阶段 1 的 code_index
  → 外部解析器可引用 code 节点
  → json_config.py 产出的 key/ref 节点可关联到 code

阶段 3: 文档提取
  → .md + .yaml + .txt + .rst + .html
  → 传入阶段 1+2 的 code_index + config_index
  → 外部解析器(如 DDD)可引用 code 节点 + 配置节点
  → LLM Tier 2 对 semantic_files 跑
```

### 为什么这样分

| 阶段 | 产出 | 被谁引用 |
|---|---|---|
| 阶段 1 (code + 包清单) | code 节点 + package 节点 | 阶段 2 配置解析器 + 阶段 3 文档解析器 |
| 阶段 2 (配置文件) | config key/ref 节点 + depends_on 边 | 阶段 3 文档解析器 |
| 阶段 3 (文档) | doc-anchor 节点 + describes/references 边 | LLM Tier 2 |

配置文件的 key/ref 节点描述的是代码依赖关系(`package.json` 的 `dependencies` → code 节点),应该在代码之后、文档之前处理,这样文档解析器能同时引用 code 节点和 config 节点。

### 改动

**文件**: `graphify/cli.py`

**位置**: `cli.py:3436-3758`(两阶段调用块)

**改动内容**:

1. `detect()` 分类后,从 `code_files` 中分离配置 JSON:
   ```python
   # cli.py — 分类后
   code_files = [Path(p) for p in files_by_type.get("code", [])]
   doc_files = [Path(p) for p in files_by_type.get("document", [])]

   # 从 code_files 分离配置 JSON (非包清单)
   from graphify.manifest_ingest import is_package_manifest_path
   config_json_files = []
   pure_code_files = []
   for f in code_files:
       if f.suffix == ".json" and not is_package_manifest_path(f):
           config_json_files.append(f)
       else:
           pure_code_files.append(f)
   # pure_code_files 含: code + 包清单 (pyproject.toml/Cargo.toml/go.mod/pom.xml/apm.yml 等)
   # config_json_files 含: package.json/tsconfig.json/composer.json 等
   #
   # 注意: is_package_manifest_path() 白名单不含 package.json
   # (PACKAGE_MANIFEST_NAMES 只有 pyproject.toml/cargo.toml/go.mod/pom.xml/apm.yml)。
   # 所以 package.json 走 config_json_files (阶段 2), 由 json_config.py 处理。
   # 这在逻辑上正确: graphify 用 json_config.py 从 package.json 提取
   # dependencies→depends_on 边, 而非 canonical package hub 节点。
   ```

2. 三阶段调用:
   ```python
   # 阶段 1: code + 包清单
   print(f"[graphify extract] AST extraction on {len(pure_code_files)} code files...")
   ast_result = _ast_extract(pure_code_files, **ast_kwargs)
   stages.mark("AST extract")

   # 阶段 2: 配置文件 (新)
   _combined_index = {"nodes": ast_result.get("nodes", []),
                      "edges": ast_result.get("edges", [])}
   if config_json_files:
       print(f"[graphify extract] config extraction on {len(config_json_files)} file(s)...")
       config_result = _ast_extract(config_json_files, **ast_kwargs)
       # 合并进 ast_result
       ast_result["nodes"] = list(ast_result["nodes"]) + list(config_result.get("nodes", []))
       ast_result["edges"] = list(ast_result["edges"]) + list(config_result.get("edges", []))
       _combined_index = {"nodes": ast_result["nodes"], "edges": ast_result["edges"]}
   stages.mark("Config extract")

   # 阶段 3: 文档
   if doc_files:
       doc_kwargs = {..., "code_index": _combined_index}
       doc_result = _doc_extract(doc_files, **doc_kwargs)
   stages.mark("Doc extract")
   ```

3. `semantic_files` 构造不变(`doc_files + paper_files + image_files`),配置 JSON 不进 LLM Tier 2。

### 验证

```bash
# 验证三阶段执行顺序 (日志输出)
uv run graphify extract . 2>&1 | grep "extraction on"
# 应看到三行:
# AST extraction on N code files...
# config extraction on M file(s)...
# doc extraction on K doc file(s)...

# 验证配置 JSON 节点在阶段 2 产出, 能被阶段 3 的 DDD 解析器引用
uv run graphify extract . --force
uv run graphify query "package.json"
```

### 测试

```python
def test_three_phase_extraction_order(tmp_path):
    """代码 → 配置文件 → 文档 三阶段顺序。"""
    # 写 code + package.json + .md 文件
    # 跑 extract, 验证日志顺序: AST → config → doc
    # 验证 doc 解析器的 code_index 含 code + config 节点
```

---

## Gap-6: DDD 代码锚点匹配增强(全限定名 + 多匹配 + 置信度标注)

### 现状

`graphify/extractors/ddd.py:153-241` `_match_code_anchor` 的限制:

| 限制 | 影响 |
|---|---|
| 全限定名 `com.example.OrderService` 不匹配 | 带 `.` 且非 PascalCase.method 格式,不匹配任何分支 |
| 部分路径 `module.OrderService` 不匹配 | 同上 |
| 多匹配只取第一个(`next(...)`) | 同名类不消歧,可能关联到错误的节点 |
| 无置信度区分 | 匹配成功全是 EXTRACTED 1.0,多匹配/同名歧义没有标 AMBIGUOUS |
| 大小写: 已敏感 | ✅ name_index key 保留原始大小写,精确匹配 |

### 目标

| 锚点格式 | 匹配方式 | 唯一匹配 | 多匹配 |
|---|---|---|---|
| `OrderService`(SimpleName) | name_index 精确匹配 | EXTRACTED 1.0 | 全部建边,AMBIGUOUS 0.3 |
| `OrderService.create`(类.方法) | name_index 查 class + 同 source_file 找 method | EXTRACTED 1.0 | 全部建边,AMBIGUOUS 0.3 |
| `com.example.OrderService`(全限定名) | 拆分: 取最后段查 name_index + 路径段跟 source_file 匹配 | 路径匹配: EXTRACTED 1.0;路径不匹配: AMBIGUOUS 0.3 | 全部建边 |
| `module.OrderService`(部分路径) | 同全限定名 | 同上 | 全部建边 |
| `POST:/rest/`(URL) | 见 Gap-7 | — | — |

### 改动

**文件**: `graphify/extractors/ddd.py`

#### 6.1 修改 `_match_code_anchor` 返回所有候选 + 置信度

**当前签名**:
```python
def _match_code_anchor(anchor: str, indices: dict) -> dict | None:
```

**改为**:
```python
def _match_code_anchor(anchor: str, indices: dict) -> list[tuple[dict, str, float]]:
    """返回 [(node, confidence, score), ...] 所有候选。

    confidence: "EXTRACTED" (唯一匹配) | "AMBIGUOUS" (多匹配)
    score: 1.0 (唯一) | 0.3 (多匹配, AMBIGUOUS 区间 0.1-0.3)
    """
```

#### 6.2 各分支匹配逻辑

**分支 3 改造: PascalCase 类名(SimpleName)**

```python
# 3. PascalCase class name (SimpleName)
if PASCAL_CASE_REGEX.match(anchor):
    candidates = indices["nameIndex"].get(anchor, [])
    class_candidates = [n for n in candidates if _is_class_node(n)]
    if len(class_candidates) == 1:
        return [(class_candidates[0], "EXTRACTED", 1.0)]
    elif len(class_candidates) > 1:
        return [(n, "AMBIGUOUS", 0.3) for n in class_candidates]
    # fallback: 同名非 class 节点
    if len(candidates) == 1:
        return [(candidates[0], "EXTRACTED", 1.0)]
    elif len(candidates) > 1:
        return [(n, "AMBIGUOUS", 0.3) for n in candidates]
    return []
```

**新增分支: 全限定名 / 部分路径**

```python
# 3.5 全限定名或部分路径: com.example.OrderService / module.OrderService
#    (带 . 但不是 PascalCase.method 格式)
if "." in anchor and not SNAKE_DOT_METHOD_REGEX.match(anchor) and not PASCAL_DOT_METHOD_REGEX.match(anchor):
    parts = anchor.split(".")
    simple_name = parts[-1]           # "OrderService"
    path_hints = parts[:-1]           # ["com", "example"] 或 ["module"]

    # 按 simple_name 查 name_index
    candidates = indices["nameIndex"].get(simple_name, [])
    if not candidates:
        # 也试 PascalCase 匹配 (simple_name 可能不是 PascalCase, 但仍按 label 查)
        candidates = indices["nameIndex"].get(simple_name, [])
    if not candidates:
        return []

    # 按 source_file 路径段消歧
    path_str = "/".join(p.lower() for p in path_hints)  # "com/example"
    matched_exact = []
    matched_ambiguous = []
    for n in candidates:
        sf = (n.get("source_file") or "").lower().replace("\\", "/")
        if path_str in sf:
            matched_exact.append(n)
        else:
            matched_ambiguous.append(n)

    if matched_exact:
        if len(matched_exact) == 1:
            return [(matched_exact[0], "EXTRACTED", 1.0)]
        return [(n, "AMBIGUOUS", 0.3) for n in matched_exact]
    # 路径不匹配但类名匹配: 全部 AMBIGUOUS
    if matched_ambiguous:
        return [(n, "AMBIGUOUS", 0.3) for n in matched_ambiguous]
    return []
```

**分支 2 改造: PascalCase.method**

```python
# 2. PascalCase.method (如 OrderService.create)
m = PASCAL_DOT_METHOD_REGEX.match(anchor)
if m:
    class_name, method_name = m.group(1), m.group(2)
    class_candidates = indices["nameIndex"].get(class_name, [])
    class_nodes = [n for n in class_candidates if _is_class_node(n)]
    if not class_nodes:
        class_nodes = class_candidates[:]  # fallback: 同名非 class 节点

    results: list[tuple[dict, str, float]] = []
    for cls in class_nodes:
        # 在同 source_file 找方法
        fn_candidates = indices["nameIndex"].get(method_name, [])
        fns = [n for n in fn_candidates
               if _is_function_node(n)
               and n.get("source_file") == cls.get("source_file")]
        if fns:
            for fn in fns:
                results.append((fn, "EXTRACTED", 1.0))
        else:
            # Fallback: 类节点 (部分匹配)
            results.append((cls, "AMBIGUOUS", 0.3))

    # 去重 (同一个 node 可能被多个 cls 匹配)
    seen_ids = set()
    deduped = []
    for node, conf, score in results:
        if node["id"] not in seen_ids:
            seen_ids.add(node["id"])
            deduped.append((node, conf, score))

    # 唯一匹配 → EXTRACTED 1.0; 多匹配 → 全部 AMBIGUOUS 0.3
    if len(deduped) == 1:
        return [(deduped[0][0], "EXTRACTED", 1.0)]
    elif len(deduped) > 1:
        return [(n, "AMBIGUOUS", 0.3) for n, _, _ in deduped]
    return []
```

**分支 1 改造: snake_case.method** — 同理返回所有候选。

#### 6.3 调用方改造

`_parse_tagged_file` 和 `_parse_technical_constraints` 中调用 `_match_code_anchor` 的地方:

```python
# 当前 (ddd.py:535-550)
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
    unmatched.append({...})

# 改为
candidates = _match_code_anchor(clean_anchor, indices)
if candidates:
    for matched, conf, score in candidates:
        pending_edges.append({
            "type": "describes",
            "sourceNodeId": node["id"],
            "targetNodeId": matched["id"],
            "confidence": conf,          # "EXTRACTED" 或 "AMBIGUOUS"
            "confidence_score": score,   # 1.0 或 0.3
            "weight": 0.8 if conf == "EXTRACTED" else 0.3,
            "source_file": doc_path,
        })
else:
    unmatched.append({...})
```

#### 6.4 `_resolve_pending_edges` 透传置信度

`ddd.py:776-826` `_resolve_pending_edges` 的 `_make_edge` 调用需要透传 `confidence` + `confidence_score`:

```python
# ddd.py:818-824 改为
edges.append(_make_edge(
    source=source_node["id"],
    target=target_node["id"],
    relation=relation_map.get(pe["type"], "references"),
    source_file=pe.get("source_file", ""),
    weight=pe.get("weight", 0.5),
    confidence=pe.get("confidence", "EXTRACTED"),        # 新增
    confidence_score=pe.get("confidence_score", 1.0),    # 新增
))
```

`_make_edge` 函数(`ddd.py:380-391`)加 `confidence` + `confidence_score` 参数。

### 验证

```bash
# 1. SimpleName 唯一匹配 → EXTRACTED 1.0
# 2. SimpleName 多匹配 → 全部建边 AMBIGUOUS 0.3
# 3. 全限定名 com.example.OrderService → 路径匹配的 EXTRACTED 1.0, 不匹配的 AMBIGUOUS 0.3
# 4. PascalCase.method → 方法找到 EXTRACTED 1.0, 方法没找到 fallback 类 AMBIGUOUS 0.3
uv run pytest tests/test_ddd_code_anchor_matching.py -q
```

### 测试

新建 `tests/test_ddd_code_anchor_matching.py`:

```python
def test_simple_name_unique_match():
    """SimpleName 唯一匹配 → EXTRACTED 1.0。"""

def test_simple_name_multiple_match_all_ambiguous():
    """SimpleName 多匹配 → 全部建边 AMBIGUOUS 0.3。"""

def test_qualified_name_path_match_extracted():
    """全限定名 com.example.OrderService, source_file 含 com/example → EXTRACTED 1.0。"""

def test_qualified_name_path_mismatch_ambiguous():
    """全限定名 com.example.OrderService, source_file 不含 com/example → AMBIGUOUS 0.3。"""

def test_pascal_method_found_extracted():
    """OrderService.create, 方法找到 → EXTRACTED 1.0。"""

def test_pascal_method_not_found_fallback_class_ambiguous():
    """OrderService.create, 方法没找到 → fallback 类节点 AMBIGUOUS 0.3。"""

def test_case_sensitive_matching():
    """大小写敏感: OrderService ≠ orderservice。"""

def test_file_anchor_multiple_match_all_ambiguous():
    """文件名锚点 (如 register_plugin.rs) 多匹配 → 全部建边 AMBIGUOUS 0.3。"""

def test_snake_dot_method_multiple_match_all_ambiguous():
    """snake_case.file.method 多匹配 → 全部建边 AMBIGUOUS 0.3。"""

def test_confidence_fields_on_final_edge():
    """端到端: _match_code_anchor → pending_edge → _resolve_pending_edges → _make_edge
    验证 confidence/confidence_score 字段值正确透传到最终 edge (三处断链全修复)。"""

def test_resolve_pending_edges_preserves_confidence():
    """_resolve_pending_edges 从 pending_edge 读取 confidence/confidence_score 传给 _make_edge,
    不走默认值 EXTRACTED/1.0。"""
```

---

## Gap-7: URL 锚点匹配修复(endpoint 节点产出 + 路径规范化)

### 现状

`ddd.py:225-239` 的 URL 匹配依赖 `endpoint_index`,但 `endpoint_index` (`ddd.py:144-148`) 只索引 `label.startswith("/")` 的节点:

```python
if label and label.startswith("/"):
    endpoint_index[label] = node
```

**问题**: graphify AST extractor 产出的 code 节点 label 是裸类名/函数名(如 `OrderService`/`create`),**不以 `/` 开头**。`endpoint_index` **几乎总是空的**。

### 目标

让 `POST:/rest/` 等 URL 锚点能匹配到代码节点。两种方案:

### 方案 A: 路由解析器产出 endpoint 节点(推荐)

写一个自定义解析器(工具型,放 `graphify/extractors/custom/` 或 `.graph/extension/extractors/`),从路由定义文件提取 endpoint 节点:

| 路由定义方式 | 语言/框架 | 提取方式 |
|---|---|---|
| `@app.route("/rest")` / `@router.get("/users/{id}")` | Python(Flask/FastAPI) | 正则扫描装饰器 |
| `app.get("/rest", handler)` | Node(Express/Fastify) | AST walk |
| `@GetMapping("/rest")` / `@RequestMapping` | Java(Spring) | AST walk |
| `@Get("/rest")` | TS(NestJS) | AST walk |
| `router.GET("/rest", ...)` | Go(gin/echo) | AST walk |

产出的 endpoint 节点:
```python
{
    "id": "endpoint_rest_users_id",
    "label": "/rest/users/{id}",     # 路由路径, 以 / 开头
    "file_type": "concept",
    "source_file": "src/api/users.py",
    "source_location": "L42",
    "node_kind": "endpoint",
    "tags": ["endpoint", "rest", "GET"],
}
```

label 以 `/` 开头 → 被 `endpoint_index` 索引 → DDD 的 URL 锚点能匹配。

### 方案 B: 路径规范化 + 前缀匹配(兜底)

如果不想写路由解析器,改 `_match_code_anchor` 的 URL 分支,做路径前缀/包含匹配:

```python
# 5. URL — HTTP method + colon + path (POST:/rest/)
m = HTTP_COLON_URL_REGEX.match(anchor)
if m:
    raw_path = "/" + m.group(2)       # "/rest/" (保留末尾斜杠)
    # 规范化: 去末尾斜杠 (除非是根路径)
    norm_path = raw_path.rstrip("/") if len(raw_path) > 1 else raw_path  # "/rest"
    # 精确匹配
    node = indices["endpointIndex"].get(norm_path)
    if node:
        return [(node, "EXTRACTED", 1.0)]
    # 前缀匹配 (anchor 是 /rest, endpoint 是 /rest/users/{id})
    prefix_matches = [(n, "AMBIGUOUS", 0.3)
                      for path, n in indices["endpointIndex"].items()
                      if path.startswith(norm_path)]
    if prefix_matches:
        return prefix_matches
    return []
```

### 改动

**Gap-7 分两步**:

**Step 1 (方案 B)**: 修改 `_match_code_anchor` 的 URL 分支,加路径规范化 + 前缀匹配 + 返回候选列表(跟 Gap-6 的返回格式一致)。

**Step 2 (方案 A, 可选)**: 写一个路由解析器,产出 endpoint 节点。这是独立解析器,可后续做。

### 验证

```bash
# Step 1: URL 路径规范化
uv run pytest tests/test_ddd_url_matching.py -q

# Step 2 (如果有路由解析器): endpoint 节点被索引
uv run graphify extract . --force
uv run graphify query "/rest"
```

### 测试

新建 `tests/test_ddd_url_matching.py`:

```python
def test_post_colon_path_normalized():
    """POST:/rest/ → 规范化为 /rest → 匹配 endpoint_index["/rest"]。"""

def test_url_prefix_match_ambiguous():
    """POST:/rest 匹配 /rest/users/{id} (前缀匹配) → AMBIGUOUS 0.3。"""

def test_url_no_match_returns_empty():
    """URL 锚点无匹配 → 返回空列表 (非 None)。"""
```

---

## E2E 测试体系（双重保障）

> UT 验证每个分支的精确行为;E2E 验证真实 `graphify extract` → `graph.json` 的端到端集成。
> 已有 fixture: `tests/e2e/resources/user-management/`(TS 项目 + 7 类 DDD 文档 + 配置文件)。
> 已有 E2E 测试: `tests/e2e/test_user_management_e2e.py`(396 LOC, 9 个测试类)。

### Fixture 数据补充

现有 fixture 无法覆盖 Gap-6 多匹配场景(所有类名唯一),需补充:

| 补充 | 位置 | 验证什么 |
|------|------|----------|
| **加同名类** | `src/middleware/` 加一个同名 `Logger` 类(与 `src/utils/logger.ts` 的 `Logger` 重名) | Gap-6: 多匹配 → AMBIGUOUS 0.3 真实触发 |
| **加全限定名锚点** | 某个 DDD 文档的 `<anchor:code>` 列加 `com.example.User` | Gap-6: 全限定名路径消歧匹配 |
| **清理 stale 文件** | 删 fixture 根目录的 `ddd-unmatched.json`(.mjs 工具链遗留) | 避免 `_write_ddd_unmatched` append 到旧记录污染数据 |

### conftest.py force-rebuild 支持

`tests/e2e/conftest.py:56` 只在 `GRAPH_JSON.exists()` 为 False 时跑提取。实现 Gap 后跑 E2E,如果不手动删 `graphify-out/`,E2E 跑的是**旧 graph**。改进:

```python
# tests/e2e/conftest.py — 加 force-rebuild 支持
@pytest.fixture(scope="session", autouse=True)
def ensure_graph_json():
    force = os.environ.get("GRAPHIFY_E2E_FORCE", "") == "1"
    if GRAPH_JSON.exists() and not force:
        print("[e2e] graph.json already exists, skipping extraction")
        yield
        return
    if GRAPH_JSON.exists():
        shutil.rmtree(GRAPH_JSON.parent)
    # 也清理根目录的 stale ddd-unmatched.json
    stale = PROJECT_ROOT / "ddd-unmatched.json"
    if stale.exists():
        stale.unlink()
    print("\n[e2e] Building graph.json for user-management project...")
    _run_extraction()
    ...
```

### E2E 新增/修改测试类

| 测试类 | 验证的 Gap | 测试点 |
|--------|-----------|--------|
| `TestThreePhaseExtraction`(新增) | Gap-5 | ①日志输出三行 "AST/config/doc extraction";②graph.json 含 package.json 的 config 节点;③doc 阶段 code_index 含 config 节点 |
| `TestCodeAnchorConfidence`(新增) | Gap-6 | ①唯一匹配 describes 边 `confidence=="EXTRACTED"` + `confidence_score==1.0`;②多匹配边 `confidence=="AMBIGUOUS"` + `confidence_score==0.3`(依赖 fixture 同名类);③全限定名路径匹配/不匹配的置信度区分 |
| `TestCodeAnchorMatching`(修改现有) | Gap-6 | `test_authservice_anchored` 修复后验证 `AuthService.register` 锚点匹配到 AuthService 类(method 找不到 fallback)+ edge confidence |
| `TestUnmatchedAnchors`(修改现有) | Gap-7 | 修复方案B后 `POST:/auth/register` 仍 unmatched(endpoint_index 空)→ 验证 unmatched 记录的 reason 字段 |

### E2E 验证命令

每个 Gap 完成后(或全部完成后):

```bash
# 删旧 graph, 强制重建, 跑 E2E
$env:GRAPHIFY_E2E_FORCE="1"
uv run pytest tests/e2e/ -q
# 或 Linux/macOS:
GRAPHIFY_E2E_FORCE=1 uv run pytest tests/e2e/ -q
```

---

## 执行顺序与依赖

```
Gap-1 (解除硬编码) ──→ Gap-2 (内置自动扫描) ──→ Gap-3 (项目级目录 + 优先级)
                                                        │
                                                        │ (独立)
Gap-4 (Tier 2 prompt registry) ←─────────────────────────┘

Gap-5 (三阶段顺序) ←── 独立, 但建议在 Gap-1 之后做 (Gap-1 解除扩展名限制后, 配置 JSON 可走外部解析器)

Gap-6 (锚点匹配增强) ←── 独立, 改 ddd.py 的 _match_code_anchor

Gap-7 (URL 匹配修复) ←── 依赖 Gap-6 (返回格式一致: list[tuple[node, conf, score]])
```

| Gap | 依赖 | 预估改动量 | 风险 |
|---|---|---|---|
| Gap-1 | 无 | ~30 LOC (extract.py) | 低: 只放宽扫描范围,不改变 merge_mode 逻辑 |
| Gap-2 | Gap-1 | ~40 LOC (__init__.py) + 移动 ddd.py | 中: 移动 ddd.py 需更新所有 import 引用 |
| Gap-3 | Gap-2 | ~50 LOC (registry.py + __init__.py) | 中: 优先级 prepend 逻辑需仔细测试 |
| Gap-4 | 无(独立) | ~150 LOC (prompt_registry.py + cli.py 集成) | 高: 涉及 LLM 调用路径,需 mock 测试 |
| Gap-5 | 无(建议 Gap-1 后) | ~60 LOC (cli.py 三阶段调用) | 中: 改变提取顺序,需验证 code_index 传递 |
| Gap-6 | 无 | ~120 LOC (ddd.py _match_code_anchor + 调用方) | 中: 返回类型从 dict 改为 list,需更新所有调用方 |
| Gap-7 | Gap-6 | ~40 LOC (ddd.py URL 分支) | 低: 只改 URL 分支,路径规范化逻辑清晰 |

---

## 回归测试

每个 Gap 完成后跑:

```bash
# 1. 既有测试不回归
uv run pytest tests/ -q

# 2. DDD 解析器仍工作(Gap-2 移动 ddd.py 后 / Gap-6/7 改 _match_code_anchor 后)
uv run pytest tests/test_ddd_extractor.py -q
uv run pytest tests/test_ddd_code_anchor_matching.py -q  # Gap-6 新增
uv run pytest tests/test_ddd_url_matching.py -q          # Gap-7 新增

# 3. tags 检索仍工作
uv run graphify query "aggregate_root"

# 4. 端到端
uv run graphify extract . --force
uv run graphify query "auth"

# 5. 三阶段顺序 (Gap-5)
uv run graphify extract . 2>&1 | grep "extraction on"
# 应看到: AST → config → doc

# 6. E2E 集成测试 (删旧 graph, 强制重建)
$env:GRAPHIFY_E2E_FORCE="1"
uv run pytest tests/e2e/ -q
# 或 Linux/macOS:
GRAPHIFY_E2E_FORCE=1 uv run pytest tests/e2e/ -q
```

> **双重保障**: UT (`tests/test_*.py`) 验证每个分支的精确行为;
> E2E (`tests/e2e/`) 验证真实 `graphify extract` → `graph.json` 的端到端集成。
> 详见上方 "E2E 测试体系" 章节。
