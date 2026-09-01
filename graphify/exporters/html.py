"""html — moved verbatim from graphify/export.py."""
from __future__ import annotations

from graphify.exporters.base import COMMUNITY_COLORS  # noqa: E402,F401
from pathlib import Path
import html as _html
from graphify.analyze import _node_community_map
from graphify.paths import write_text_atomic
import json
import networkx as nx
from graphify.security import sanitize_label


MAX_NODES_FOR_VIZ = 5_000
_HTML_STALE_MARKER = ".graph.html.stale"

# Tag normalization — merge duplicate tag variants produced by different
# DDD fixture sets (e.g. "domain-events" vs "domain_event") into one
# canonical form for display and filtering.
_TAG_NORMALIZE: dict[str, str] = {
    "domain-events": "domain_event",
    "invariants": "invariant",
    "technical-constraints": "tech_constraint",
    "contracts": "contract",
}

def _normalize_tag(t: str) -> str:
    return _TAG_NORMALIZE.get(t, t)

def _viz_node_limit() -> int:
    """Return the effective viz node limit, honoring GRAPHIFY_VIZ_NODE_LIMIT env var.

    Falls back to MAX_NODES_FOR_VIZ when the env var is unset, empty, or non-integer.
    Set to 0 to disable HTML viz unconditionally (useful for CI runners).
    """
    import os
    raw = os.environ.get("GRAPHIFY_VIZ_NODE_LIMIT")
    if raw is None or not raw.strip():
        return MAX_NODES_FOR_VIZ
    try:
        return int(raw)
    except ValueError:
        return MAX_NODES_FOR_VIZ

def _html_styles() -> str:
    return """<style>
  /* == Light theme tokens == */
  :root {
    --gf-root: #eef0f5; --gf-surface: #ffffff; --gf-elevated: #f4f6fa; --gf-panel: #e8ebf1;
    --gf-accent: #4E79A7; --gf-accent-bright: #3d6491; --gf-accent-dim: #6b94c0;
    --gf-accent-glow: rgba(78,121,167,0.12);
    --gf-text-primary: #1a1d2e; --gf-text-secondary: #4a4e64; --gf-text-muted: #7a7f96; --gf-text-faint: #a8adbf;
    --gf-border-subtle: rgba(78,121,167,0.08); --gf-border-medium: rgba(78,121,167,0.16); --gf-border-strong: #d4d8e2;
    --gf-status-island: #dc4444; --gf-status-ambiguous: #d97706; --gf-status-inferred: #2563eb; --gf-status-gap: #6b7280; --gf-status-extracted: #16a34a;
    --gf-status-island-bg: rgba(220,68,68,0.08); --gf-status-ambiguous-bg: rgba(217,119,6,0.08); --gf-status-inferred-bg: rgba(37,99,235,0.08); --gf-status-gap-bg: rgba(107,114,128,0.08); --gf-status-extracted-bg: rgba(22,163,74,0.08);
    --gf-glass-bg: rgba(255,255,255,0.88); --gf-glass-border: rgba(78,121,167,0.10); --gf-glass-blur: 16px;
    --gf-shadow-sm: 0 1px 3px rgba(26,29,46,0.08); --gf-shadow-md: 0 4px 12px rgba(26,29,46,0.10); --gf-shadow-lg: 0 8px 28px rgba(26,29,46,0.12);
    --gf-topbar-h: 48px; --gf-bottombar-h: 44px; --gf-sidebar-w: 380px; --gf-detail-w: 320px;
    --gf-font-heading: 'Space Grotesk','Segoe UI',sans-serif; --gf-font-body: 'IBM Plex Sans',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; --gf-font-mono: 'JetBrains Mono','Cascadia Code',Consolas,monospace;
    --gf-transition: 120ms ease-out;
  }
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=IBM+Plex+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap');
  *,*::before,*::after { box-sizing:border-box; margin:0; padding:0; }
  html { font-size:16px; -webkit-font-smoothing:antialiased; }
  body { font-family:var(--gf-font-body); background:var(--gf-root); color:var(--gf-text-primary); font-size:0.8125rem; overflow:hidden; height:100vh; display:flex; flex-direction:column; }
  .font-heading { font-family:var(--gf-font-heading); }
  .font-mono { font-family:var(--gf-font-mono); }

  /* == Topbar == */
  .topbar { height:var(--gf-topbar-h); background:var(--gf-surface); border-bottom:1px solid var(--gf-border-subtle); display:flex; align-items:center; padding:0 20px; gap:16px; flex-shrink:0; z-index:100; box-shadow:var(--gf-shadow-sm); }
  .brand { display:flex; align-items:center; gap:8px; font-family:var(--gf-font-heading); font-size:0.875rem; font-weight:600; color:var(--gf-text-primary); }
  .brand-mark { width:20px; height:20px; border-radius:4px; background:var(--gf-accent); display:flex; align-items:center; justify-content:center; font-family:var(--gf-font-mono); font-size:11px; font-weight:700; color:#fff; }
  .brand-sub { font-size:0.75rem; color:var(--gf-text-muted); font-weight:400; }
  .divider-v { width:1px; height:22px; background:var(--gf-border-subtle); }
  .mode-tabs { display:flex; gap:2px; }
  .mode-tab { display:flex; align-items:center; gap:4px; padding:6px 12px; border:none; background:transparent; color:var(--gf-text-muted); font-size:0.75rem; font-weight:500; border-radius:6px; cursor:pointer; transition:all var(--gf-transition); }
  .mode-tab:hover { background:var(--gf-elevated); color:var(--gf-text-secondary); }
  .mode-tab.active { color:var(--gf-accent-bright); background:rgba(78,121,167,0.08); }
  .mode-tab .badge { font-size:9px; font-weight:700; padding:1px 5px; border-radius:10px; background:var(--gf-status-ambiguous-bg); color:var(--gf-status-ambiguous); min-width:16px; text-align:center; }
  .search-box { flex:1; max-width:320px; display:flex; align-items:center; gap:8px; background:var(--gf-panel); border:1px solid var(--gf-border-medium); border-radius:8px; padding:5px 12px; }
  .search-box:focus-within { border-color:var(--gf-accent); box-shadow:0 0 0 2px var(--gf-accent-glow); }
  .search-box svg { width:14px; height:14px; color:var(--gf-text-muted); flex-shrink:0; }
  #search { flex:1; border:none; background:transparent; color:var(--gf-text-primary); font-size:0.75rem; outline:none; font-family:var(--gf-font-body); }
  #search::placeholder { color:var(--gf-text-faint); }
  .report-link { display:flex; align-items:center; gap:4px; padding:5px 8px; border:1px solid var(--gf-border-medium); border-radius:8px; font-size:0.6875rem; color:var(--gf-text-muted); cursor:pointer; font-weight:500; }
  .report-link:hover { border-color:var(--gf-accent); color:var(--gf-accent-bright); }
  .report-link svg { width:12px; height:12px; }
  .persona-switch { display:flex; align-items:center; background:var(--gf-panel); border-radius:8px; padding:2px; }
  .persona-btn { padding:4px 8px; border:none; background:transparent; color:var(--gf-text-muted); font-size:0.6875rem; font-weight:500; border-radius:6px; cursor:pointer; text-transform:uppercase; letter-spacing:0.04em; }
  .persona-btn.active { background:var(--gf-surface); color:var(--gf-accent-bright); box-shadow:var(--gf-shadow-sm); }

  /* == Workspace (three columns) == */
  .workspace { flex:1; display:flex; min-height:0; }

  /* Left sidebar */
  .sidebar { width:var(--gf-sidebar-w); background:var(--gf-surface); border-right:1px solid var(--gf-border-subtle); display:flex; flex-direction:column; flex-shrink:0; overflow:hidden; }
  .sidebar-header { padding:16px 16px 12px; border-bottom:1px solid var(--gf-border-subtle); flex-shrink:0; }
  .sidebar-title { font-family:var(--gf-font-heading); font-size:1.0625rem; font-weight:600; color:var(--gf-text-primary); }
  .sidebar-meta { font-size:0.6875rem; color:var(--gf-text-muted); margin-top:3px; }
  .filter-section { padding:8px 16px; border-bottom:1px solid var(--gf-border-subtle); flex-shrink:0; }
  .filter-section-label { font-size:0.6875rem; color:var(--gf-text-muted); text-transform:uppercase; letter-spacing:0.08em; font-weight:600; margin-bottom:4px; }
  .filter-chip-row { display:flex; flex-wrap:wrap; gap:4px; }
  .filter-chip { display:flex; align-items:center; gap:4px; padding:3px 7px; border-radius:12px; font-size:0.6875rem; font-weight:500; color:var(--gf-text-secondary); background:var(--gf-panel); border:1px solid var(--gf-border-medium); cursor:pointer; white-space:nowrap; user-select:none; }
  .filter-chip:hover { border-color:var(--gf-accent); }
  .filter-chip:not(.active) { opacity:0.45; text-decoration:line-through; }
  .filter-chip-dot { width:8px; height:8px; border-radius:50%; flex-shrink:0; }
  .filter-chip-count { font-size:9px; color:var(--gf-text-faint); font-family:var(--gf-font-mono); }
  .sidebar-list { flex:1; overflow-y:auto; padding:4px; }
  .node-item { padding:12px; border-radius:8px; cursor:pointer; transition:background var(--gf-transition); margin-bottom:2px; }
  .node-item:hover { background:var(--gf-elevated); }
  .node-item.selected { background:var(--gf-elevated); }
  .node-item-head { display:flex; align-items:center; gap:8px; margin-bottom:4px; }
  .node-status-dot { width:8px; height:8px; border-radius:50%; flex-shrink:0; }
  .node-type-dot { width:8px; height:8px; border-radius:50%; flex-shrink:0; }
  .node-badge { font-size:9px; font-weight:600; padding:1px 6px; border-radius:4px; text-transform:uppercase; letter-spacing:0.04em; flex-shrink:0; }
  .nb-island { background:var(--gf-status-island-bg); color:var(--gf-status-island); }
  .nb-ambiguous { background:var(--gf-status-ambiguous-bg); color:var(--gf-status-ambiguous); }
  .nb-inferred { background:var(--gf-status-inferred-bg); color:var(--gf-status-inferred); }
  .nb-gap { background:var(--gf-status-gap-bg); color:var(--gf-status-gap); }
  .node-title { font-size:0.75rem; font-weight:500; color:var(--gf-text-primary); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; flex:1; }
  .node-detail { font-size:0.6875rem; color:var(--gf-text-muted); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  .node-file { font-family:var(--gf-font-mono); font-size:10px; color:var(--gf-text-faint); margin-top:3px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }

  /* Center graph */
  .graph-area { flex:1; position:relative; overflow:hidden; background:var(--gf-root); min-width:0; }
  #graph { width:100%; height:100%; }
  .graph-stats { position:absolute; bottom:12px; left:12px; font-family:var(--gf-font-mono); font-size:0.6875rem; color:var(--gf-text-muted); }
  .graph-stats b { color:var(--gf-text-secondary); }

  /* Right detail panel */
  .detail-panel { width:var(--gf-detail-w); background:var(--gf-surface); border-left:1px solid var(--gf-border-subtle); display:flex; flex-direction:column; flex-shrink:0; overflow:hidden; }
  .detail-header { padding:16px; border-bottom:1px solid var(--gf-border-subtle); flex-shrink:0; }
  .detail-name { font-family:var(--gf-font-heading); font-size:0.875rem; font-weight:600; color:var(--gf-text-primary); margin-bottom:4px; }
  .detail-meta { display:flex; align-items:center; gap:8px; font-size:0.6875rem; color:var(--gf-text-muted); }
  .kind-badge { padding:1px 6px; border-radius:4px; font-weight:600; text-transform:uppercase; letter-spacing:0.04em; font-size:10px; }
  .kb-extracted { background:var(--gf-status-extracted-bg); color:var(--gf-status-extracted); }
  .kb-ambiguous { background:var(--gf-status-ambiguous-bg); color:var(--gf-status-ambiguous); }
  .kb-inferred { background:var(--gf-status-inferred-bg); color:var(--gf-status-inferred); }
  .kb-island { background:var(--gf-status-island-bg); color:var(--gf-status-island); }
  .detail-body { flex:1; overflow-y:auto; padding:12px 16px; }
  .detail-field { display:flex; justify-content:space-between; padding:5px 0; font-size:0.75rem; border-bottom:1px solid var(--gf-border-subtle); }
  .detail-field-label { color:var(--gf-text-muted); }
  .detail-field-value { color:var(--gf-text-secondary); font-family:var(--gf-font-mono); font-size:0.6875rem; }
  .detail-tags { display:flex; flex-wrap:wrap; gap:4px; padding:8px 0; }
  .detail-tag { font-size:10px; padding:2px 7px; border-radius:12px; background:rgba(78,121,167,0.08); color:var(--gf-accent-bright); border:1px solid rgba(78,121,167,0.15); font-family:var(--gf-font-mono); }
  .detail-nav { display:flex; gap:8px; padding:12px 16px; border-top:1px solid var(--gf-border-subtle); flex-shrink:0; }
  .detail-nav-btn { flex:1; display:flex; align-items:center; justify-content:center; gap:4px; padding:6px; border:1px solid var(--gf-border-medium); border-radius:6px; font-size:0.6875rem; font-weight:600; cursor:pointer; text-transform:uppercase; letter-spacing:0.04em; color:var(--gf-text-muted); transition:all var(--gf-transition); background:var(--gf-surface); }
  .detail-nav-btn:hover { border-color:var(--gf-accent); color:var(--gf-accent-bright); }
  .detail-nav-btn svg { width:12px; height:12px; }

  /* Edit section (only for low-confidence) */
  .edit-section { border-top:1px solid var(--gf-border-subtle); flex-shrink:0; }
  .edit-header { padding:12px 16px 8px; display:flex; align-items:center; gap:8px; font-family:var(--gf-font-heading); font-size:0.75rem; font-weight:600; color:var(--gf-text-primary); background:var(--gf-elevated); }
  .edit-header svg { width:13px; height:13px; color:var(--gf-status-ambiguous); }
  .edit-body { padding:0 16px 12px; background:var(--gf-elevated); }
  .edit-tab-row { display:flex; gap:2px; margin-bottom:12px; background:var(--gf-surface); border-radius:8px; padding:2px; }
  .edit-tab { flex:1; padding:5px; border:none; background:transparent; font-size:0.6875rem; font-weight:600; color:var(--gf-text-muted); border-radius:6px; cursor:pointer; text-transform:uppercase; letter-spacing:0.04em; }
  .edit-tab.active { background:var(--gf-accent); color:#fff; }
  .edit-field { margin-bottom:12px; }
  .edit-label { display:block; font-size:0.6875rem; color:var(--gf-text-muted); margin-bottom:4px; text-transform:uppercase; letter-spacing:0.04em; font-weight:600; }
  .edit-input, .edit-select { width:100%; background:var(--gf-surface); border:1px solid var(--gf-border-medium); color:var(--gf-text-primary); font-family:var(--gf-font-body); font-size:0.75rem; padding:6px 8px; border-radius:6px; outline:none; }
  .edit-input:focus, .edit-select:focus { border-color:var(--gf-accent); }
  .edit-input[readonly] { background:var(--gf-panel); color:var(--gf-text-muted); }
  .edit-textarea { width:100%; min-height:50px; resize:vertical; background:var(--gf-surface); border:1px solid var(--gf-border-medium); color:var(--gf-text-primary); font-family:var(--gf-font-body); font-size:0.75rem; padding:6px 8px; border-radius:6px; outline:none; line-height:1.5; }
  .edit-textarea:focus { border-color:var(--gf-accent); }
  .edit-actions { display:flex; gap:8px; }
  .btn { flex:1; padding:7px 12px; border:none; border-radius:6px; font-family:var(--gf-font-body); font-size:0.75rem; font-weight:600; cursor:pointer; }
  .btn-primary { background:var(--gf-accent); color:#fff; }
  .btn-primary:hover { background:var(--gf-accent-bright); }
  .btn-ghost { background:var(--gf-surface); color:var(--gf-text-secondary); border:1px solid var(--gf-border-medium); }
  .edit-note { font-size:0.6875rem; color:var(--gf-text-faint); margin-top:8px; font-family:var(--gf-font-mono); }

  /* No-edit hint (for high-confidence nodes) */
  .no-edit-hint { padding:16px; text-align:center; font-size:0.6875rem; color:var(--gf-text-muted); background:var(--gf-elevated); border-top:1px solid var(--gf-border-subtle); }
  .no-edit-hint svg { width:24px; height:24px; color:var(--gf-status-extracted); margin-bottom:8px; }

  /* Bottom filter bar */
  .bottom-bar { height:var(--gf-bottombar-h); background:var(--gf-surface); border-top:1px solid var(--gf-border-subtle); display:flex; align-items:center; padding:0 16px; gap:8px; flex-shrink:0; overflow-x:auto; }
  .bottom-divider { width:1px; height:18px; background:var(--gf-border-subtle); margin:0 4px; }
  .bottom-stats { margin-left:auto; font-family:var(--gf-font-mono); font-size:0.6875rem; color:var(--gf-text-muted); white-space:nowrap; }
  .bottom-stats b { color:var(--gf-text-secondary); }

  /* Legend (community filter, kept in bottom bar) */
  .legend-item { display:flex; align-items:center; gap:6px; padding:2px 0; cursor:pointer; font-size:0.6875rem; color:var(--gf-text-secondary); white-space:nowrap; user-select:none; }
  .legend-dot { width:10px; height:10px; border-radius:50%; flex-shrink:0; }
  .legend-count { color:var(--gf-text-muted); font-size:0.6875rem; font-family:var(--gf-font-mono); }
  .legend-item.dimmed { opacity:0.35; }

  /* Search results dropdown */
  #search-results { position:absolute; top:100%; left:0; right:0; background:var(--gf-surface); border:1px solid var(--gf-border-medium); border-radius:0 0 8px 8px; box-shadow:var(--gf-shadow-md); max-height:200px; overflow-y:auto; z-index:200; display:none; }
  .search-item { padding:6px 12px; cursor:pointer; font-size:0.75rem; color:var(--gf-text-secondary); display:flex; align-items:center; gap:6px; }
  .search-item:hover { background:var(--gf-elevated); }
  .search-item-dot { width:8px; height:8px; border-radius:50%; flex-shrink:0; }
  .search-wrap { position:relative; flex:1; max-width:320px; }

  /* Neighbor links (delegated click, no inline onclick - #1838) */
  .neighbor-link { display:block; padding:3px 6px; margin:2px 0; border-radius:4px; cursor:pointer; font-size:0.75rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; color:var(--gf-text-secondary); }
  .neighbor-link:hover { background:var(--gf-elevated); color:var(--gf-text-primary); }

  /* Overview tab content */
  .overview-page { flex:1; overflow-y:auto; padding:24px 32px; background:var(--gf-root); }
  .ovw-max { max-width:100%; margin:0; }
  .ovw-hero { display:flex; align-items:baseline; gap:12px; margin-bottom:4px; }
  .ovw-hero h1 { font-family:var(--gf-font-heading); font-size:1.75rem; font-weight:700; color:var(--gf-text-primary); letter-spacing:-0.01em; }
  .ovw-hero p { font-size:0.8125rem; color:var(--gf-text-muted); }
  .ovw-subtitle { font-size:0.8125rem; color:var(--gf-text-secondary); margin-bottom:24px; line-height:1.7; max-width:600px; }
  .stat-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin-bottom:32px; }
  .stat-card { background:var(--gf-surface); border:1px solid var(--gf-border-subtle); border-radius:12px; padding:20px; box-shadow:var(--gf-shadow-sm); position:relative; overflow:hidden; }
  .stat-card::before { content:''; position:absolute; top:0; left:0; right:0; height:3px; background:var(--stat-color,var(--gf-accent)); border-radius:12px 12px 0 0; }
  .stat-value { font-family:var(--gf-font-heading); font-size:2rem; font-weight:700; color:var(--gf-text-primary); line-height:1; margin-bottom:4px; }
  .stat-label { font-size:0.6875rem; color:var(--gf-text-muted); text-transform:uppercase; letter-spacing:0.08em; font-weight:600; }
  .stat-trend { font-size:0.6875rem; color:var(--gf-text-faint); margin-top:8px; font-family:var(--gf-font-mono); }
  .chart-grid { display:grid; grid-template-columns:1.4fr 1fr; gap:16px; margin-bottom:32px; }
  .chart-card { background:var(--gf-surface); border:1px solid var(--gf-border-subtle); border-radius:12px; padding:20px; box-shadow:var(--gf-shadow-sm); }
  .chart-title { font-family:var(--gf-font-heading); font-size:0.8125rem; font-weight:600; color:var(--gf-text-primary); margin-bottom:16px; }
  .bar-row { display:flex; align-items:center; gap:12px; margin-bottom:12px; }
  .bar-label { width:80px; font-size:0.75rem; color:var(--gf-text-secondary); font-family:var(--gf-font-mono); text-align:right; flex-shrink:0; display:flex; align-items:center; gap:4px; }
  .bar-track { flex:1; height:22px; background:var(--gf-panel); border-radius:4px; overflow:hidden; }
  .bar-fill { height:100%; border-radius:4px; display:flex; align-items:center; justify-content:flex-end; padding-right:8px; }
  .bar-count { font-size:0.6875rem; color:#fff; font-weight:600; font-family:var(--gf-font-mono); }
  .comm-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:16px; }
  .comm-card { background:var(--gf-surface); border:1px solid var(--gf-border-subtle); border-radius:12px; padding:16px; box-shadow:var(--gf-shadow-sm); cursor:pointer; transition:all var(--gf-transition); border-top:3px solid var(--comm-color,var(--gf-accent)); }
  .comm-card:hover { box-shadow:var(--gf-shadow-md); transform:translateY(-1px); }
  .comm-head { display:flex; align-items:center; gap:8px; margin-bottom:8px; }
  .comm-dot { width:12px; height:12px; border-radius:50%; flex-shrink:0; }
  .comm-name { font-family:var(--gf-font-heading); font-size:0.8125rem; font-weight:600; color:var(--gf-text-primary); }
  .comm-count { font-size:0.6875rem; color:var(--gf-text-muted); font-family:var(--gf-font-mono); margin-left:auto; }
  .comm-desc { font-size:0.75rem; color:var(--gf-text-secondary); line-height:1.5; margin-bottom:12px; }
  .comm-stats { display:flex; gap:16px; font-size:0.6875rem; color:var(--gf-text-muted); }
  .comm-stat b { color:var(--gf-text-secondary); font-weight:500; }

  /* Tab pages visibility */
  .tab-page { display:none; flex:1; min-height:0; }
  .tab-page.active { display:flex; }

  /* Scrollbar */
  ::-webkit-scrollbar { width:6px; height:6px; }
  ::-webkit-scrollbar-track { background:transparent; }
  ::-webkit-scrollbar-thumb { background:rgba(78,121,167,0.15); border-radius:6px; }
  ::-webkit-scrollbar-thumb:hover { background:rgba(78,121,167,0.28); }
  :focus-visible { outline:2px solid var(--gf-accent); outline-offset:2px; }
</style>"""

def _hyperedge_script(hyperedges_json: str) -> str:
    return f"""<script>
// Render hyperedges as shaded regions
const hyperedges = {hyperedges_json};
// afterDrawing passes ctx already transformed to network coordinate space.
// Draw node positions raw - no manual pan/zoom/DPR math needed.

// Andrew's monotone chain. Returns the hull in counter-clockwise order, which
// is what the perimeter must be traced in. Collinear and duplicate points
// collapse to the extremes, so degenerate member sets render as a segment
// rather than a zero-area crossed path.
function convexHull(pts) {{
    const p = pts.slice().sort((a, b) => (a.x - b.x) || (a.y - b.y));
    if (p.length < 3) return p;
    const cross = (o, a, b) => (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x);
    const build = seq => {{
        const out = [];
        for (const q of seq) {{
            while (out.length >= 2 && cross(out[out.length - 2], out[out.length - 1], q) <= 0) out.pop();
            out.push(q);
        }}
        out.pop();
        return out;
    }};
    const hull = build(p).concat(build(p.slice().reverse()));
    return hull.length >= 3 ? hull : p;
}}
network.on('afterDrawing', function(ctx) {{
    hyperedges.forEach(h => {{
        const positions = h.nodes
            .map(nid => network.getPositions([nid])[nid])
            .filter(p => p !== undefined);
        if (positions.length < 2) return;
        ctx.save();
        ctx.globalAlpha = 0.12;
        ctx.fillStyle = '#6366f1';
        ctx.strokeStyle = '#6366f1';
        ctx.lineWidth = 2;
        ctx.beginPath();
        // Centroid and expanded hull in network coordinates.
        // The perimeter must follow hull order, not h.nodes order: tracing the
        // raw member order self-intersects whenever the layout does not happen
        // to place members in angular order, filling as crossed wedges.
        const cx = positions.reduce((s, p) => s + p.x, 0) / positions.length;
        const cy = positions.reduce((s, p) => s + p.y, 0) / positions.length;
        const hull = convexHull(positions);
        const expanded = hull.map(p => ({{
            x: cx + (p.x - cx) * 1.15,
            y: cy + (p.y - cy) * 1.15
        }}));
        ctx.moveTo(expanded[0].x, expanded[0].y);
        expanded.slice(1).forEach(p => ctx.lineTo(p.x, p.y));
        ctx.closePath();
        ctx.fill();
        ctx.globalAlpha = 0.4;
        ctx.stroke();
        // Label
        ctx.globalAlpha = 0.8;
        ctx.fillStyle = '#4f46e5';
        ctx.font = 'bold 11px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(h.label, cx, cy - 5);
        ctx.restore();
    }});
}});
</script>"""

def _review_queue_script(review_json: str) -> str:
    """Retained for API compatibility but now returns empty — review logic
    is unified into _html_script which has access to all node data."""
    return ""


def _html_script(nodes_json: str, edges_json: str, legend_json: str, type_index_json: str, tag_index_json: str, review_json: str = "[]") -> str:
    return f"""<script>
const RAW_NODES = {nodes_json};
const RAW_EDGES = {edges_json};
const LEGEND = {legend_json};
const TYPE_INDEX = {type_index_json};
const TAG_INDEX = {tag_index_json};
const REVIEW = {review_json};
const COMMUNITY_COLORS = ["#4E79A7","#F28E2B","#E15759","#76B7B2","#59A14F","#EDC948","#B07AA1","#FF9DA7","#9C755F","#BAB0AC"];

// HTML-escape helper - prevents XSS when injecting graph data into innerHTML
function esc(s) {{
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}}

// == Build vis datasets ==
const nodesDS = new vis.DataSet(RAW_NODES.map(n => ({{
  id: n.id, label: n.label, color: n.color, size: n.size,
  font: n.font, title: n.title,
  _community: n.community, _community_name: n.community_name,
  _source_file: n.source_file, _file_type: n.file_type, _degree: n.degree,
  _tags: n.tags || [], _node_kind: n.node_kind || '',
}})));

const edgesDS = new vis.DataSet(RAW_EDGES.map((e, i) => ({{
  id: i, from: e.from, to: e.to,
  label: '',
  title: e.title,
  dashes: e.dashes,
  width: e.width,
  color: e.color,
  arrows: {{ to: {{ enabled: true, scaleFactor: 0.5 }} }},
}})));

const container = document.getElementById('graph');
const network = new vis.Network(container, {{ nodes: nodesDS, edges: edgesDS }}, {{
  physics: {{
    enabled: true,
    solver: 'forceAtlas2Based',
    forceAtlas2Based: {{
      gravitationalConstant: -60,
      centralGravity: 0.005,
      springLength: 120,
      springConstant: 0.08,
      damping: 0.4,
      avoidOverlap: 0.8,
    }},
    stabilization: {{ iterations: 200, fit: true }},
  }},
  interaction: {{
    hover: true,
    tooltipDelay: 100,
    hideEdgesOnDrag: true,
    navigationButtons: false,
    keyboard: false,
  }},
  nodes: {{ shape: 'dot', borderWidth: 1.5 }},
  edges: {{ smooth: {{ type: 'continuous', roundness: 0.2 }}, selectionWidth: 3 }},
}});

network.once('stabilizationIterationsDone', () => {{
  network.setOptions({{ physics: {{ enabled: false }} }});
}});

// == Tab switching ==
const tabs = document.querySelectorAll('.mode-tab');
const tabPages = document.querySelectorAll('.tab-page');
const graphEl = document.getElementById('graph');
const reviewGraphArea = document.querySelector('#page-review .graph-area');
const learnGraphArea = document.getElementById('learn-graph-area');
const bottomBar = document.querySelector('.bottom-bar');

function moveToTab(target) {{
  tabs.forEach(t => t.classList.remove('active'));
  document.querySelector('.mode-tab[data-tab="' + target + '"]').classList.add('active');
  tabPages.forEach(p => p.classList.remove('active'));
  const page = document.getElementById('page-' + target);
  if (page) page.classList.add('active');
  // Move graph element to the active tab's graph area (review or learn)
  if (target === 'review' && reviewGraphArea) {{
    reviewGraphArea.insertBefore(graphEl, reviewGraphArea.firstChild);
    if (bottomBar) bottomBar.style.display = 'flex';
    setTimeout(() => network.redraw(), 50);
  }} else if (target === 'learn' && learnGraphArea) {{
    learnGraphArea.insertBefore(graphEl, learnGraphArea.firstChild);
    if (bottomBar) bottomBar.style.display = 'flex';
    setTimeout(() => network.redraw(), 50);
  }} else {{
    // Overview tab - hide bottom bar, graph stays in last tab's area (hidden)
    if (bottomBar) bottomBar.style.display = 'none';
  }}
}}
tabs.forEach(tab => {{
  tab.addEventListener('click', () => {{
    moveToTab(tab.dataset.tab);
  }});
}});

// == Node detail panel ==
function showInfo(nodeId) {{
  const n = nodesDS.get(nodeId);
  if (!n) return;
  const neighborIds = network.getConnectedNodes(nodeId);
  const neighborItems = neighborIds.map(nid => {{
    const nb = nodesDS.get(nid);
    const color = nb ? nb.color.background : '#7a7f96';
    return `<span class="neighbor-link" style="border-left:3px solid ${{esc(color)}}" data-nid="${{esc(nid)}}">${{esc(nb ? nb.label : nid)}}</span>`;
  }}).join('');
  const tagsHtml = (n._tags && n._tags.length)
    ? `<div class="detail-tags">${{n._tags.map(t => `<span class="detail-tag">${{esc(t)}}</span>`).join('')}}</div>` : '';
  const kindHtml = n._node_kind ? `<span class="kind-badge kb-extracted">${{esc(n._node_kind)}}</span>` : '';

  // Check if this node is in the review queue (low-confidence)
  const reviewItem = REVIEW.find(r => r.node_id === nodeId || r.endpointId === nodeId);
  const isLowConf = !!reviewItem;

  // Determine confidence badge
  let confBadge = '';
  if (reviewItem) {{
    const type = reviewItem.type || (reviewItem.anchorKind ? 'island' : 'island');
    const badgeClass = type === 'island' ? 'kb-island' : (type === 'ambiguous_edge' ? 'kb-ambiguous' : (type === 'inferred_edge' ? 'kb-inferred' : 'kb-island'));
    confBadge = `<span class="kind-badge ${{badgeClass}}">${{esc(type.replace('_edge','').toUpperCase())}}</span>`;
  }} else {{
    confBadge = `<span class="kind-badge kb-extracted">EXTRACTED</span>`;
  }}

  const detailBody = document.getElementById('detail-body');
  const detailHeader = document.getElementById('detail-header');
  const editSection = document.getElementById('edit-section');

  detailHeader.innerHTML = `
    <div class="detail-name">${{esc(n.label)}}</div>
    <div class="detail-meta">${{confBadge}} ${{kindHtml}} <span>${{esc(n._file_type || 'unknown')}}</span></div>
  `;
  detailBody.innerHTML = `
    <div class="detail-field"><span class="detail-field-label">社区</span><span class="detail-field-value">${{esc(n._community_name)}}</span></div>
    <div class="detail-field"><span class="detail-field-label">连接数</span><span class="detail-field-value">${{n._degree}}</span></div>
    <div class="detail-field"><span class="detail-field-label">来源文件</span><span class="detail-field-value">${{esc(n._source_file || '-')}}</span></div>
    ${{tagsHtml}}
    ${{neighborIds.length ? `<div class="detail-field" style="border-bottom:none;padding-top:8px"><span class="detail-field-label">相邻节点 (${{neighborIds.length}})</span></div><div id="neighbors-list">${{neighborItems}}</div>` : ''}}
  `;

  // Show/hide edit section based on confidence
  if (isLowConf) {{
    editSection.style.display = 'block';
    // Pre-fill edit fields if available
    const detail = reviewItem.detail || reviewItem.reason || '';
    const file = reviewItem.source_file || reviewItem.file || '';
    if (detail) document.getElementById('edit-textarea').value = detail;
    if (file) document.getElementById('edit-file-path').textContent = '→ ' + file;
  }} else {{
    editSection.style.display = 'none';
  }}
}}

function focusNode(nodeId) {{
  network.focus(nodeId, {{ scale: 1.4, animation: true }});
  network.selectNodes([nodeId]);
  showInfo(nodeId);
  // Also select in node list
  document.querySelectorAll('.node-item').forEach(el => el.classList.remove('selected'));
  const listEl = document.querySelector('.node-item[data-nid="' + nodeId + '"]');
  if (listEl) {{
    listEl.classList.add('selected');
    listEl.scrollIntoView({{ block: 'nearest' }});
  }}
}}

// Neighbor links use a data attribute + one delegated listener rather than an
// inline onclick. A node id/label sourced from a document or a scraped URL
// (graphify add) can contain a double-quote; dropping the stringified id
// unescaped into a quoted onclick both broke every link and allowed a hostile
// source to inject an event handler into the local report (stored XSS, #1838).
// esc() on data-nid keeps the value inside the attribute; the listener reads it
// back verbatim. Bound to document so it survives the innerHTML rebuild that
// recreates #neighbors-list on each showInfo().
document.addEventListener('click', e => {{
  const el = e.target.closest('.neighbor-link');
  if (el && el.dataset.nid !== undefined) focusNode(el.dataset.nid);
}});

// Track hovered node - hover detection is more reliable than click params
let hoveredNodeId = null;
network.on('hoverNode', params => {{
  hoveredNodeId = params.node;
  container.style.cursor = 'pointer';
}});
network.on('blurNode', () => {{
  hoveredNodeId = null;
  container.style.cursor = 'default';
}});
container.addEventListener('click', () => {{
  if (hoveredNodeId !== null) {{
    showInfo(hoveredNodeId);
    network.selectNodes([hoveredNodeId]);
  }}
}});
network.on('click', params => {{
  if (params.nodes.length > 0) {{
    showInfo(params.nodes[0]);
  }}
}});

// == Search ==
const searchInput = document.getElementById('search');
const searchResults = document.getElementById('search-results');
searchInput.addEventListener('input', () => {{
  const q = searchInput.value.toLowerCase().trim();
  searchResults.innerHTML = '';
  if (!q) {{ searchResults.style.display = 'none'; return; }}
  const matches = RAW_NODES.filter(n => n.label.toLowerCase().includes(q)).slice(0, 20);
  if (!matches.length) {{ searchResults.style.display = 'none'; return; }}
  searchResults.style.display = 'block';
  matches.forEach(n => {{
    const el = document.createElement('div');
    el.className = 'search-item';
    el.innerHTML = `<span class="search-item-dot" style="background:${{n.color.background}}"></span><span>${{esc(n.label)}}</span>`;
    el.onclick = () => {{
      focusNode(n.id);
      searchResults.style.display = 'none';
      searchInput.value = '';
    }};
    searchResults.appendChild(el);
  }});
}});
document.addEventListener('click', e => {{
  if (searchResults && !searchResults.contains(e.target) && e.target !== searchInput)
    searchResults.style.display = 'none';
}});

// == Unified filter system ==
const hiddenCommunities = new Set();
const TYPE_ACTIVE = {{}};
const TAG_ACTIVE = {{}};
let tagOnlyTagged = false;

TYPE_INDEX.forEach(t => {{ TYPE_ACTIVE[t.type] = true; }});
TAG_INDEX.forEach(t => {{ TAG_ACTIVE[t.tag] = true; }});

function isNodeHidden(n) {{
  if (!TYPE_ACTIVE[n.file_type]) return true;
  if (hiddenCommunities.has(n.community)) return true;
  const tags = n.tags || [];
  if (tagOnlyTagged && tags.length === 0) return true;
  if (tags.length > 0 && tags.some(t => !TAG_ACTIVE[t])) return true;
  return false;
}}

function applyFilters() {{
  const updates = RAW_NODES.map(n => ({{ id: n.id, hidden: isNodeHidden(n) }}));
  nodesDS.update(updates);
  updateStats();
  renderNodeList();
}}

function updateStats() {{
  const visible = RAW_NODES.filter(n => !isNodeHidden(n)).length;
  const el = document.getElementById('stats');
  if (el) el.innerHTML = `<b>${{visible}}</b>/${{RAW_NODES.length}} · <b>${{RAW_EDGES.length}}</b>边 · <b>${{LEGEND.length}}</b>社区`;
}}

// == Filter chip rendering (type, tag, community) ==
function renderFilterChips() {{
  // Type filter chips
  const typeContainer = document.getElementById('filter-type');
  if (typeContainer) {{
    typeContainer.innerHTML = '';
    TYPE_INDEX.forEach(t => {{
      const chip = document.createElement('span');
      chip.className = 'filter-chip active';
      chip.innerHTML = `<span class="filter-chip-dot" style="background:${{COMMUNITY_COLORS[t.type.charCodeAt(0) % 10] || '#4E79A7'}}"></span>${{esc(t.type)}} <span class="filter-chip-count">${{t.count}}</span>`;
      chip.addEventListener('click', () => {{
        TYPE_ACTIVE[t.type] = !TYPE_ACTIVE[t.type];
        chip.classList.toggle('active', TYPE_ACTIVE[t.type]);
        applyFilters();
      }});
      typeContainer.appendChild(chip);
    }});
  }}
  // Tag filter chips
  const tagContainer = document.getElementById('filter-tags');
  if (tagContainer) {{
    tagContainer.innerHTML = '';
    if (!TAG_INDEX.length) {{
      tagContainer.innerHTML = '<span style="font-size:0.6875rem;color:var(--gf-text-faint)">暂无标签</span>';
    }} else {{
      TAG_INDEX.forEach(t => {{
        const chip = document.createElement('span');
        chip.className = 'filter-chip active';
        chip.innerHTML = `${{esc(t.tag)}} <span class="filter-chip-count">${{t.count}}</span>`;
        chip.addEventListener('click', () => {{
          TAG_ACTIVE[t.tag] = !TAG_ACTIVE[t.tag];
          chip.classList.toggle('active', TAG_ACTIVE[t.tag]);
          applyFilters();
        }});
        tagContainer.appendChild(chip);
      }});
    }}
  }}
  // Community filter chips (in bottom bar)
  const commContainer = document.getElementById('filter-community');
  if (commContainer) {{
    commContainer.innerHTML = '';
    LEGEND.forEach(c => {{
      const chip = document.createElement('span');
      chip.className = 'legend-item active';
      chip.dataset.cid = c.cid;
      chip.innerHTML = `<span class="legend-dot" style="background:${{c.color}}"></span><span>${{esc(c.label)}}</span><span class="legend-count">${{c.count}}</span>`;
      chip.addEventListener('click', () => {{
        if (hiddenCommunities.has(c.cid)) {{
          hiddenCommunities.delete(c.cid);
          chip.classList.add('active');
          chip.classList.remove('dimmed');
        }} else {{
          hiddenCommunities.add(c.cid);
          chip.classList.remove('active');
          chip.classList.add('dimmed');
        }}
        applyFilters();
      }});
      commContainer.appendChild(chip);
    }});
  }}
}}

// == Node list rendering (all nodes, with status indicators) ==
const REVIEW_NODE_IDS = new Set(REVIEW.map(r => r.node_id || r.endpointId).filter(Boolean));
const REVIEW_META = {{
  island: {{ label: '孤岛', dot: '#dc4444', badge: 'nb-island' }},
  ambiguous_edge: {{ label: '多匹配', dot: '#d97706', badge: 'nb-ambiguous' }},
  inferred_edge: {{ label: '推断', dot: '#2563eb', badge: 'nb-inferred' }},
  semantic_gap: {{ label: 'LLM缺失', dot: '#6b7280', badge: 'nb-gap' }},
}};

function reviewTypeOf(item) {{
  if (item.type) return item.type;
  if (item.anchorKind) return 'island';
  if (item.reason && item.reason.includes('LLM')) return 'semantic_gap';
  return 'island';
}}

function renderNodeList() {{
  const container = document.getElementById('node-list');
  if (!container) return;
  const visibleNodes = RAW_NODES.filter(n => !isNodeHidden(n));
  const showLimit = 100;
  container.innerHTML = '';
  visibleNodes.slice(0, showLimit).forEach(n => {{
    const isReview = REVIEW_NODE_IDS.has(n.id);
    const reviewItem = isReview ? REVIEW.find(r => (r.node_id || r.endpointId) === n.id) : null;
    const el = document.createElement('div');
    el.className = 'node-item';
    el.dataset.nid = n.id;
    if (isReview && reviewItem) {{
      const type = reviewTypeOf(reviewItem);
      const meta = REVIEW_META[type] || REVIEW_META.island;
      el.innerHTML = `
        <div class="node-item-head">
          <span class="node-status-dot" style="background:${{meta.dot}}"></span>
          <span class="node-badge ${{meta.badge}}">${{esc(meta.label)}}</span>
          <span class="node-title">${{esc(n.label)}}</span>
        </div>
        <div class="node-detail">${{esc(reviewItem.detail || reviewItem.reason || '')}}</div>
        <div class="node-file">${{esc(n._source_file || '')}}</div>
      `;
    }} else {{
      el.innerHTML = `
        <div class="node-item-head">
          <span class="node-type-dot" style="background:${{n.color.background}}"></span>
          <span class="node-title">${{esc(n.label)}}</span>
        </div>
        <div class="node-detail">${{esc(n._node_kind || n._file_type || '')}} · ${{n._degree}} 连接</div>
        <div class="node-file">${{esc(n._source_file || '')}}</div>
      `;
    }}
    el.addEventListener('click', () => {{
      focusNode(n.id);
    }});
    container.appendChild(el);
  }});
  // Show count hint if truncated
  if (visibleNodes.length > showLimit) {{
    const hint = document.createElement('div');
    hint.style.cssText = 'padding:8px 16px;text-align:center;font-size:0.6875rem;color:var(--gf-text-muted);border-top:1px solid var(--gf-border-subtle)';
    hint.textContent = '显示前 ' + showLimit + ' 个 / 共 ' + visibleNodes.length + ' 个节点';
    container.appendChild(hint);
  }}
  // Update review badge count
  const badge = document.getElementById('review-badge');
  if (badge) {{
    badge.textContent = REVIEW.length;
  }}
}}

// == Edit tab switching ==
document.addEventListener('click', e => {{
  const tab = e.target.closest('.edit-tab');
  if (tab) {{
    tab.parentElement.querySelectorAll('.edit-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
  }}
}});

// == Initialize ==
renderFilterChips();
renderNodeList();
updateStats();
// Render overview community cards
const ovwComm = document.getElementById('overview-communities');
if (ovwComm) {{
  LEGEND.slice(0, 6).forEach(c => {{
    const card = document.createElement('div');
    card.className = 'comm-card';
    card.style.setProperty('--comm-color', c.color);
    card.innerHTML = `<div class="comm-head"><span class="comm-dot" style="background:${{c.color}}"></span><span class="comm-name">${{esc(c.label)}}</span><span class="comm-count">${{c.count}} 节点</span></div><div class="comm-desc">点击进入审核模式查看该社区详情</div>`;
    card.addEventListener('click', () => {{
      const tab = document.querySelector('.mode-tab[data-tab="review"]');
      if (tab) tab.click();
    }});
    ovwComm.appendChild(card);
  }});
}}
</script>"""


def _html_document_title(output_path: str) -> str:
    """Return a portable label for the graph.html <title>.

    Tracked artifacts must not embed the generator host absolute path
    (regression of #433; reported again as #2598 on Windows). Keep from the
    configured output-dir bare name (``.graph`` / ``GRAPHIFY_OUT``
    basename) onward — portable in every case; otherwise fall back to a
    cwd-relative label, and finally the filename only.
    """
    from graphify.paths import GRAPHIFY_OUT_NAME

    raw = str(output_path).replace("\\", "/")
    # Drop Windows drive prefix so Path parts are comparable on any OS.
    if len(raw) >= 3 and raw[1] == ":" and raw[0].isalpha() and raw[2] == "/":
        raw = raw[2:]  # "/Users/..." style after drive strip
    p = Path(raw)

    parts = list(Path(raw).parts)
    # Path("C:/Users/..") on POSIX may keep "C:" as first part — strip it.
    if parts and len(parts[0]) == 2 and parts[0][1] == ":" and parts[0][0].isalpha():
        parts = parts[1:]
    # Prefer keeping from the output-dir marker onward: portable in every
    # case, whereas a cwd-relative path still leaks host/user segments when
    # the graph is built from a directory ABOVE the project (#2598 follow-up).
    marker = GRAPHIFY_OUT_NAME
    for i, part in enumerate(parts):
        if part == marker or part.startswith(".graph"):
            return "/".join(parts[i:])

    # No standard out-dir marker (fully custom output path): fall back to a
    # cwd-relative label when the target is under cwd, else the bare filename.
    try:
        resolved = p if p.is_absolute() else (Path.cwd() / p)
        rel = resolved.resolve().relative_to(Path.cwd().resolve())
        label = rel.as_posix()
        if label and label != ".":
            return label
    except (ValueError, OSError, RuntimeError):
        pass

    name = p.name
    return name if name else "graph.html"

def to_html(
    G: nx.Graph,
    communities: dict[int, list[str]],
    output_path: str,
    community_labels: dict[int, str] | None = None,
    member_counts: dict[int, int] | None = None,
    node_limit: int | None = None,
    learning_overlay: dict | None = None,
    review_queue: list[dict] | None = None,
) -> bool:
    """Generate an interactive vis.js HTML visualization of the graph.

    Features: node size by degree, click-to-inspect panel, search box,
    community filter, physics clustering by community, confidence-styled edges.
    Raises ValueError if graph exceeds MAX_NODES_FOR_VIZ.

    If member_counts is provided (aggregated community view), node sizes are
    based on community member counts rather than graph degree.

    If node_limit is set and the graph exceeds it, automatically builds an
    aggregated community-level meta-graph instead of raising ValueError.

    If review_queue is provided, a collapsible "Review Queue" panel is added
    to the sidebar, surfacing items that need human verification: unmatched
    anchors (islands), ambiguous multi-match edges, inferred edges, and
    LLM semantic gaps. Each item carries its source file so the user can
    filter by file. Clicking an item focuses the related node in the graph.

    Returns True when the output was written. Returns False when an aggregated
    view would contain fewer than two communities and is intentionally skipped.
    """
    limit = node_limit if node_limit is not None else _viz_node_limit()
    if G.number_of_nodes() > limit:
        if node_limit is not None:
            # Build aggregated community meta-graph
            from collections import Counter as _Counter
            import networkx as _nx
            print(f"Graph has {G.number_of_nodes()} nodes (above {limit} limit). Building aggregated community view...")
            node_to_community = {nid: cid for cid, members in communities.items() for nid in members}
            # Compute dominant file_type and aggregated tags per community so
            # the meta-graph nodes carry type/tag attributes for the filter
            # panels (dominant type = most common among members; tags = union).
            ft_by_comm: dict[int, _Counter] = {}
            tags_by_comm: dict[int, set[str]] = {}
            for nid, cid in node_to_community.items():
                ndata = G.nodes[nid]
                ft = ndata.get("file_type", "")
                if ft:
                    ft_by_comm.setdefault(cid, _Counter())[ft] += 1
                node_tags = ndata.get("tags")
                if node_tags:
                    tags_by_comm.setdefault(cid, set()).update(node_tags)
            meta = _nx.Graph()
            for cid, members in communities.items():
                ft_counts = ft_by_comm.get(cid)
                dom_ft = ft_counts.most_common(1)[0][0] if ft_counts else ""
                agg_tags = sorted(tags_by_comm.get(cid, set()))
                meta.add_node(str(cid),
                    label=(community_labels or {}).get(cid, f"Community {cid}"),
                    file_type=dom_ft,
                    tags=agg_tags,
                )
            edge_counts = _Counter()
            for u, v in G.edges():
                cu, cv = node_to_community.get(u), node_to_community.get(v)
                if cu is not None and cv is not None and cu != cv:
                    edge_counts[(min(cu, cv), max(cu, cv))] += 1
            for (cu, cv), w in edge_counts.items():
                meta.add_edge(str(cu), str(cv), weight=w,
                              relation=f"{w} cross-community edges", confidence="AGGREGATED")
            if meta.number_of_nodes() <= 1:
                print("Single community - aggregated view not useful. Skipping graph.html.")
                return False
            meta_communities = {cid: [str(cid)] for cid in communities}
            mc = {cid: len(members) for cid, members in communities.items()}
            # Remap hyperedges from semantic node IDs to community IDs
            raw_hyperedges = G.graph.get("hyperedges", [])
            if raw_hyperedges:
                remapped = []
                for he in raw_hyperedges:
                    he_members = he.get("nodes", [])
                    comm_ids, seen = [], set()
                    for nid in he_members:
                        c = node_to_community.get(nid)
                        if c is None:
                            continue
                        s = str(c)
                        if s in seen:
                            continue
                        seen.add(s)
                        comm_ids.append(s)
                    if len(comm_ids) < 2:
                        continue
                    remapped.append({
                        "id": he.get("id", ""),
                        "label": he.get("label") or he.get("relation", "").replace("_", " "),
                        "nodes": comm_ids,
                    })
                meta.graph["hyperedges"] = remapped
            written = to_html(meta, meta_communities, output_path,
                              community_labels=community_labels, member_counts=mc)
            if not written:
                return False
            print(f"graph.html written (aggregated: {meta.number_of_nodes()} community nodes, {meta.number_of_edges()} cross-community edges)")
            print("Tip: run with --obsidian for full node-level detail.")
            return True
        raise ValueError(
            f"Graph has {G.number_of_nodes()} nodes - too large for HTML viz "
            f"(limit: {limit}). Use --no-viz, raise GRAPHIFY_VIZ_NODE_LIMIT, "
            f"or reduce input size."
        )

    node_community = _node_community_map(communities)
    degree = dict(G.degree())
    max_deg = max(degree.values(), default=1) or 1
    max_mc = (max(member_counts.values(), default=1) or 1) if member_counts else 1

    # Work-memory overlay (derived sidecar). When not passed explicitly, load it
    # best-effort from the sibling .graphify_learning.json next to the output
    # graph.html (which lives beside graph.json). Empty/missing => no learning
    # fields, so the un-annotated render is byte-identical to pre-feature.
    if learning_overlay is None:
        learning_overlay = {}
        try:
            from graphify.reflect import load_learning_overlay as _llo
            learning_overlay = _llo(Path(output_path))
        except Exception:
            learning_overlay = {}
    # Status -> ring color. preferred=green, contested=amber. Tentative gets no
    # ring (it's not yet trustworthy enough to highlight in the map).
    _RING = {"preferred": "#22c55e", "contested": "#f59e0b"}

    # Build nodes list for vis.js
    vis_nodes = []
    for node_id, data in G.nodes(data=True):
        cid = node_community.get(node_id, 0)
        color = COMMUNITY_COLORS[cid % len(COMMUNITY_COLORS)]
        label = sanitize_label(data.get("label", node_id))
        deg = degree.get(node_id, 1)
        if member_counts:
            mc = member_counts.get(cid, 1)
            size = 10 + 30 * (mc / max_mc)
            font_size = 12
        else:
            size = 10 + 30 * (deg / max_deg)
            # Only show label for high-degree nodes by default; others show on hover
            font_size = 12 if deg >= max_deg * 0.15 else 0
        node = {
            "id": node_id,
            "label": label,
            "color": {"background": color, "border": color, "highlight": {"background": "#ffffff", "border": color}},
            "size": round(size, 1),
            "font": {"size": font_size, "color": "#ffffff"},
            "title": _html.escape(label),
            "community": cid,
            "community_name": sanitize_label((community_labels or {}).get(cid, f"Community {cid}")),
            "source_file": sanitize_label(str(data.get("source_file") or "")),
            "file_type": data.get("file_type", ""),
            "tags": [_normalize_tag(t) for t in (data.get("tags") or [])],
            "node_kind": data.get("node_kind", ""),
            "degree": deg,
        }
        # Conditional learning fields — only present for annotated nodes, so
        # un-annotated output keeps the exact pre-feature node dict shape.
        entry = learning_overlay.get(str(node_id)) if learning_overlay else None
        if entry:
            status = sanitize_label(str(entry.get("status", "")))
            stale = bool(entry.get("stale"))
            node["learning_status"] = status
            node["learning_stale"] = stale
            ring = _RING.get(status)
            if ring:
                # Status-colored ring via the border; stale => desaturated +
                # dashed (vis.js supports per-node `shapeProperties.borderDashes`).
                if stale:
                    ring = "#9ca3af"
                    node["shapeProperties"] = {"borderDashes": [4, 4]}
                node["borderWidth"] = 3
                node["color"] = {
                    "background": color, "border": ring,
                    "highlight": {"background": "#ffffff", "border": ring},
                }
            # Lesson line appended to the hover title.
            if status == "contested":
                lesson = f"Lesson: contested (useful {entry.get('uses', 0)} / dead-end {entry.get('neg', 0)})"
            elif status == "preferred":
                lesson = f"Lesson: preferred source ({entry.get('uses', 0)} useful, score={entry.get('score', 0)})"
            else:
                lesson = f"Lesson: {status} ({entry.get('uses', 0)} useful)"
            if stale:
                lesson += " [code changed - re-verify]"
            node["title"] = _html.escape(label) + "\n" + _html.escape(sanitize_label(lesson))
        vis_nodes.append(node)

    # Pre-aggregate type and tag indices for the filter panels. Done here
    # (server-side) so the frontend doesn't scan all nodes on load.
    from collections import Counter as _Cnt
    _ft_counts: _Cnt = _Cnt()
    _tag_counts: _Cnt = _Cnt()
    for _vn in vis_nodes:
        _ft = _vn.get("file_type", "")
        if _ft:
            _ft_counts[_ft] += 1
        for _t in _vn.get("tags", []):
            _tag_counts[_t] += 1
    type_index = [{"type": ft, "count": c} for ft, c in _ft_counts.most_common()]
    tag_index = [{"tag": t, "count": c} for t, c in _tag_counts.most_common()]

    # Build edges list. Restore original edge direction from _src/_tgt
    # (stashed by build.py for exactly this reason): undirected NetworkX
    # canonicalizes endpoint order, which would otherwise flip the arrow
    # for `calls` and `rationale_for` in the rendered graph (#563).
    vis_edges = []
    for u, v, data in G.edges(data=True):
        confidence = data.get("confidence", "EXTRACTED")
        relation = data.get("relation", "")
        true_src = data.get("_src", u)
        true_tgt = data.get("_tgt", v)
        vis_edges.append({
            "from": true_src,
            "to": true_tgt,
            "label": relation,
            "title": _html.escape(f"{relation} [{confidence}]"),
            "dashes": confidence != "EXTRACTED",
            "width": 2 if confidence == "EXTRACTED" else 1,
            "color": {"opacity": 0.7 if confidence == "EXTRACTED" else 0.35},
            "confidence": confidence,
        })

    # Build community legend data
    legend_data = []
    for cid in sorted((community_labels or {}).keys()):
        color = COMMUNITY_COLORS[cid % len(COMMUNITY_COLORS)]
        lbl = _html.escape(sanitize_label((community_labels or {}).get(cid, f"Community {cid}")))
        n = member_counts.get(cid, len(communities.get(cid, []))) if member_counts else len(communities.get(cid, []))
        legend_data.append({"cid": cid, "color": color, "label": lbl, "count": n})

    # Build review queue items from the graph's low-confidence edges + the
    # externally-supplied islands/gaps. The graph edges are the source of
    # AMBIGUOUS (multi-match) and INFERRED items; islands (unmatched anchors)
    # and semantic gaps (LLM failures) come from the review_queue argument.
    review_items: list[dict] = []
    if review_queue:
        for r in review_queue:
            review_items.append(dict(r))
    # Extract AMBIGUOUS and INFERRED edges from the graph itself.
    for u, v, data in G.edges(data=True):
        confidence = data.get("confidence", "EXTRACTED")
        if confidence in ("AMBIGUOUS", "INFERRED"):
            src_label = sanitize_label(G.nodes[u].get("label", u))
            tgt_label = sanitize_label(G.nodes[v].get("label", v))
            relation = data.get("relation", "")
            review_items.append({
                "type": "ambiguous_edge" if confidence == "AMBIGUOUS" else "inferred_edge",
                "title": f"{src_label} → {tgt_label}",
                "detail": f"{relation} [{confidence}]",
                "source_file": sanitize_label(str(data.get("source_file") or "")),
                "source_location": sanitize_label(str(data.get("source_location") or "")),
                "node_id": u,  # focus the source node on click
            })

    # Escape </script> sequences so embedded JSON cannot break out of the script tag
    def _js_safe(obj) -> str:
        return json.dumps(obj).replace("</", "<\\/")

    nodes_json = _js_safe(vis_nodes)
    edges_json = _js_safe(vis_edges)
    legend_json = _js_safe(legend_data)
    review_json = _js_safe(review_items)
    hyperedges_json = _js_safe(getattr(G, "graph", {}).get("hyperedges", []))
    title = _html.escape(sanitize_label(_html_document_title(output_path)))
    stats = f"{G.number_of_nodes()} 节点 &middot; {G.number_of_edges()} 条边 &middot; {len(communities)} 个社区"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>graphify - {title}</title>
<script src="https://unpkg.com/vis-network@9.1.6/standalone/umd/vis-network.min.js"
        integrity="sha384-Ux6phic9PEHJ38YtrijhkzyJ8yQlH8i/+buBR8s3mAZOJrP1gwyvAcIYl3GWtpX1"
        crossorigin="anonymous"></script>
{_html_styles()}
</head>
<body>
<!-- Topbar -->
<header class="topbar">
  <div class="brand"><div class="brand-mark">G</div><span>graphify</span><span class="brand-sub">{title}</span></div>
  <div class="divider-v"></div>
  <nav class="mode-tabs">
    <button class="mode-tab" data-tab="overview"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="13" height="13"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>概览</button>
    <button class="mode-tab active" data-tab="review"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="13" height="13"><path d="M9 12l2 2 4-4M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>审核<span class="badge" id="review-badge">0</span></button>
    <button class="mode-tab" data-tab="learn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="13" height="13"><path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253"/></svg>学习</button>
  </nav>
  <div class="search-wrap">
    <div class="search-box">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4-4"/></svg>
      <input id="search" type="text" placeholder="搜索节点..." autocomplete="off">
    </div>
    <div id="search-results"></div>
  </div>
  <a class="report-link" href="GRAPH_REPORT.md"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M14 2v6h6"/></svg>报告 ↗</a>
</header>

<!-- Overview tab -->
<div id="page-overview" class="tab-page">
  <div class="overview-page">
    <div class="ovw-max">
      <div class="ovw-hero">
        <h1>{title}</h1>
        <p>{G.number_of_nodes()} nodes · {G.number_of_edges()} edges · {len(communities)} communities</p>
      </div>
      <p class="ovw-subtitle">知识图谱总体概览-节点统计、代码分布与社区结构。</p>
      <div class="stat-grid">
        <div class="stat-card" style="--stat-color:#4E79A7">
          <div class="stat-value">{G.number_of_nodes()}</div>
          <div class="stat-label">节点</div>
          <div class="stat-trend">across {len(communities)} communities</div>
        </div>
        <div class="stat-card" style="--stat-color:#F28E2B">
          <div class="stat-value">{G.number_of_edges()}</div>
          <div class="stat-label">关系边</div>
          <div class="stat-trend">calls · imports · uses · similar</div>
        </div>
        <div class="stat-card" style="--stat-color:#59A14F">
          <div class="stat-value">{len(communities)}</div>
          <div class="stat-label">社区 / 模块</div>
          <div class="stat-trend">Leiden clustering</div>
        </div>
        <div class="stat-card" style="--stat-color:#B07AA1">
          <div class="stat-value">{len(review_items)}</div>
          <div class="stat-label">待审核项</div>
          <div class="stat-trend">low-confidence items</div>
        </div>
      </div>
      <div class="chart-grid">
        <div class="chart-card">
          <div class="chart-title">代码分布</div>
          {''.join(f'<div class="bar-row"><span class="bar-label">{t["type"]}</span><div class="bar-track"><div class="bar-fill" style="width:{min(100, t["count"] * 100 // max(1, max(tt["count"] for tt in type_index)))}%;background:#4E79A7"><span class="bar-count">{t["count"]}</span></div></div></div>' for t in type_index)}
        </div>
        <div class="chart-card">
          <div class="chart-title">社区规模</div>
          {''.join(f'<div class="bar-row"><span class="bar-label"><span class="legend-dot" style="width:8px;height:8px;background:{c["color"]};display:inline-block"></span> {c["label"]}</span><div class="bar-track"><div class="bar-fill" style="width:{min(100, c["count"] * 100 // max(1, max(cc["count"] for cc in legend_data)))}%;background:{c["color"]}"><span class="bar-count">{c["count"]}</span></div></div></div>' for c in legend_data)}
        </div>
      </div>
      <div class="chart-card" style="margin-top:16px">
        <div class="chart-title">社区 / 模块</div>
        <div class="comm-grid" id="overview-communities"></div>
      </div>
    </div>
  </div>
</div>

<!-- Review tab (active by default) -->
<div id="page-review" class="tab-page active">
  <div class="workspace">
    <!-- Left: node list with filters -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <div class="sidebar-title">节点列表</div>
        <div class="sidebar-meta">{G.number_of_nodes()} 节点 · {len(review_items)} 项待审核</div>
      </div>
      <div class="filter-section">
        <div class="filter-section-label">数据类型</div>
        <div class="filter-chip-row" id="filter-type"></div>
      </div>
      <div class="filter-section">
        <div class="filter-section-label">标签</div>
        <div class="filter-chip-row" id="filter-tags"></div>
      </div>
      <div class="sidebar-list" id="node-list"></div>
    </aside>
    <!-- Center: graph -->
    <div class="graph-area">
      <div id="graph"></div>
      <div class="graph-stats" id="stats">{stats}</div>
    </div>
    <!-- Right: detail + edit -->
    <aside class="detail-panel">
      <div class="detail-header" id="detail-header">
        <div class="detail-name">点击节点查看详情</div>
        <div class="detail-meta"></div>
      </div>
      <div class="detail-body" id="detail-body">
        <div style="color:var(--gf-text-muted);font-size:0.75rem;text-align:center;padding:20px 0">选择左侧列表中的节点或点击图谱中的节点</div>
      </div>
      <div class="detail-nav">
        <button class="detail-nav-btn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M14 2v6h6"/></svg>源文件 ↗</button>
        <button class="detail-nav-btn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/></svg>路径</button>
        <button class="detail-nav-btn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>解释</button>
      </div>
      <div class="edit-section" id="edit-section" style="display:none">
        <div class="edit-header"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>审核修正</div>
        <div class="edit-body">
          <div class="edit-tab-row"><button class="edit-tab active">关系</button><button class="edit-tab">节点</button></div>
          <div class="edit-field"><label class="edit-label">关系类型</label><select class="edit-select"><option>calls</option><option>imports</option><option>uses</option><option>defines</option><option>semantically_similar_to</option></select></div>
          <div class="edit-field"><label class="edit-label">置信度</label><select class="edit-select"><option>EXTRACTED</option><option>AMBIGUOUS</option><option>INFERRED</option></select></div>
          <div class="edit-field"><label class="edit-label">修正说明（写入错误报告）</label><textarea class="edit-textarea" id="edit-textarea" placeholder="描述问题与期望的修正..."></textarea></div>
          <div class="edit-actions"><button class="btn btn-ghost">跳过</button><button class="btn btn-primary">提交修正</button></div>
          <div class="edit-note" id="edit-file-path">→ .graph/error-report/</div>
        </div>
      </div>
    </aside>
  </div>
</div>

<!-- Learn tab -->
<div id="page-learn" class="tab-page">
  <div class="workspace">
    <aside class="sidebar">
      <div class="sidebar-header">
        <div class="sidebar-title">引导漫游</div>
        <div class="sidebar-meta">按依赖顺序浏览架构</div>
      </div>
      <div class="sidebar-list" id="tour-list">
        <div style="padding:20px 16px;color:var(--gf-text-muted);font-size:0.75rem">漫游功能需要运行 <code style="font-family:var(--gf-font-mono);background:var(--gf-panel);padding:1px 4px;border-radius:3px">graphify --learn</code> 生成。</div>
      </div>
    </aside>
    <div class="graph-area" id="learn-graph-area">
      <!-- graph container will be moved here by JS when learn tab is active -->
      <div class="graph-stats">{stats}</div>
    </div>
    <aside class="detail-panel">
      <div class="detail-header">
        <div class="detail-name">学习模式</div>
        <div class="detail-meta">点击图谱节点查看详情</div>
      </div>
      <div class="detail-body" id="learn-detail">
        <div style="color:var(--gf-text-muted);font-size:0.75rem;text-align:center;padding:20px 0">选择图谱中的节点查看信息</div>
      </div>
      <div class="detail-nav">
        <button class="detail-nav-btn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M14 2v6h6"/></svg>源文件 ↗</button>
        <button class="detail-nav-btn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/></svg>路径</button>
        <button class="detail-nav-btn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>解释</button>
      </div>
    </aside>
  </div>
</div>

<!-- Bottom filter bar (community filter) - hidden on overview, shown on review/learn -->
<footer class="bottom-bar" id="bottom-bar" style="display:none">
  <span style="font-size:0.6875rem;color:var(--gf-text-muted);text-transform:uppercase;letter-spacing:0.08em;font-weight:600">社区</span>
  <div id="filter-community" style="display:flex;gap:6px;overflow-x:auto"></div>
  <div class="bottom-divider"></div>
  <div class="bottom-stats" id="stats-bottom">{stats}</div>
</footer>

{_html_script(nodes_json, edges_json, legend_json, _js_safe(type_index), _js_safe(tag_index), review_json)}
{_hyperedge_script(hyperedges_json)}
</body>
</html>"""

    write_text_atomic(output_path, html)
    return True
