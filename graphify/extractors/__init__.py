"""Per-language extractors, incrementally migrated out of graphify/extract.py.

Dispatch still flows through graphify.extract (the facade re-exports every
moved name), so importing from graphify.extract keeps working unchanged.
LANGUAGE_EXTRACTORS is the registry seed; wiring dispatch through it is a
later, separate step. See MIGRATION.md for how to port another language.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from graphify.extractors.apex import extract_apex
from graphify.extractors.bash import extract_bash
from graphify.extractors.blade import extract_blade
from graphify.extractors.commonlisp import extract_commonlisp
from graphify.extractors.dart import extract_dart
from graphify.extractors.dm import extract_dm, extract_dmf, extract_dmi, extract_dmm
from graphify.extractors.elixir import extract_elixir
from graphify.extractors.fortran import extract_fortran
from graphify.extractors.go import extract_go
from graphify.extractors.json_config import extract_json
from graphify.extractors.julia import extract_julia
from graphify.extractors.markdown import extract_markdown
from graphify.extractors.objc import extract_objc
from graphify.extractors.pascal import extract_pascal
from graphify.extractors.pascal_forms import extract_delphi_form, extract_lazarus_form
from graphify.extractors.powershell import extract_powershell, extract_powershell_manifest
from graphify.extractors.razor import extract_razor
from graphify.extractors.rust import extract_rust
from graphify.extractors.sln import extract_sln
from graphify.extractors.sql import extract_sql
from graphify.extractors.terraform import extract_terraform
from graphify.extractors.verilog import extract_verilog
from graphify.extractors.zig import extract_zig

LANGUAGE_EXTRACTORS: dict[str, Callable[[Path], dict]] = {
    "apex": extract_apex,
    "bash": extract_bash,
    "blade": extract_blade,
    "commonlisp": extract_commonlisp,
    "dart": extract_dart,
    "delphi_form": extract_delphi_form,
    "dm": extract_dm,
    "dmf": extract_dmf,
    "dmi": extract_dmi,
    "dmm": extract_dmm,
    "elixir": extract_elixir,
    "fortran": extract_fortran,
    "go": extract_go,
    "json": extract_json,
    "julia": extract_julia,
    "lazarus_form": extract_lazarus_form,
    "markdown": extract_markdown,
    "objc": extract_objc,
    "pascal": extract_pascal,
    "powershell": extract_powershell,
    "powershell_manifest": extract_powershell_manifest,
    "razor": extract_razor,
    "rust": extract_rust,
    "sln": extract_sln,
    "sql": extract_sql,
    "terraform": extract_terraform,
    "verilog": extract_verilog,
    "zig": extract_zig,
}


# ---------------------------------------------------------------------------
# Gap-2: auto-scan graphify/extractors/custom/ for built-in custom extractors.
# Gap-3: auto-scan .graph/extension/extractors/ for project-level extractors
#        (prepended to registry so they override built-in same-name extractors).
#
# Each module is imported in a try/except — a single failing import prints a
# warning but does not abort startup. Modules register themselves via the
# ``@register_doc_extractor`` decorator (priority="append" for built-in,
# priority="prepend" for project-level so the project wins on name clash).
# ---------------------------------------------------------------------------

def _scan_builtin_custom_extractors() -> None:
    """Auto-scan graphify/extractors/custom/ for .py modules, triggering
    ``@register_doc_extractor``. Each module is independently try/except'd."""
    import importlib
    import pkgutil
    import sys

    _custom_dir = Path(__file__).parent / "custom"
    if not _custom_dir.is_dir():
        return
    for module_info in pkgutil.iter_modules([str(_custom_dir)]):
        if module_info.name.startswith("_"):
            continue  # skip __init__ etc.
        try:
            importlib.import_module(f"graphify.extractors.custom.{module_info.name}")
        except Exception as e:
            print(f"  warning: custom extractor '{module_info.name}' failed to load: {e}", file=sys.stderr)


def _scan_project_custom_extractors() -> None:
    """Auto-scan .graph/extension/extractors/ (relative to CWD) for project-level
    extractors. Project-level extractors are prepended to the registry so they
    take priority over built-in same-name extractors."""
    import importlib
    import pkgutil
    import sys

    _project_dir = Path.cwd() / ".graph" / "extension" / "extractors"
    if not _project_dir.is_dir():
        return
    if str(_project_dir) not in sys.path:
        sys.path.insert(0, str(_project_dir))
    from graphify.extractors.registry import _REGISTRY
    for module_info in pkgutil.iter_modules([str(_project_dir)]):
        if module_info.name.startswith("_"):
            continue
        _before = {id(fn) for fn in _REGISTRY}
        try:
            importlib.import_module(module_info.name)
        except Exception as e:
            print(f"  warning: project extractor '{module_info.name}' failed to load: {e}", file=sys.stderr)
            continue
        # Move newly-registered extractors to the front (project-level priority)
        _new = [fn for fn in _REGISTRY if id(fn) not in _before]
        for fn in _new:
            _REGISTRY.remove(fn)
            _REGISTRY.insert(0, fn)


_scan_builtin_custom_extractors()
_scan_project_custom_extractors()
