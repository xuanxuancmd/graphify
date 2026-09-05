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
  .sidebar { width:var(--gf-sidebar-w); background:var(--gf-surface); border-right:1px solid var(--gf-border-subtle); display:flex; flex-direction:column; flex-shrink:0; overflow:hidden; transition:width var(--gf-transition-normal); }
  .sidebar.collapsed { width:0; border-right:none; }
  .sidebar-header { padding:16px 16px 12px; border-bottom:1px solid var(--gf-border-subtle); flex-shrink:0; display:flex; align-items:center; }
  .sidebar-title { font-family:var(--gf-font-heading); font-size:1.0625rem; font-weight:600; color:var(--gf-text-primary); flex:1; }
  .sidebar-meta { font-size:0.6875rem; color:var(--gf-text-muted); margin-top:3px; }
  .sidebar-toggle { width:24px; height:24px; display:flex; align-items:center; justify-content:center; border:none; background:transparent; color:var(--gf-text-muted); border-radius:4px; cursor:pointer; flex-shrink:0; }
  .sidebar-toggle:hover { background:var(--gf-elevated); color:var(--gf-text-primary); }
  .sidebar-toggle svg { width:14px; height:14px; }
  /* Collapse rail (thin strip to re-expand when collapsed) */
  .sidebar-rail { width:16px; background:var(--gf-surface); border-right:1px solid var(--gf-border-subtle); display:none; align-items:center; justify-content:center; cursor:pointer; flex-shrink:0; }
  .sidebar-rail.visible { display:flex; }
  .sidebar-rail:hover { background:var(--gf-elevated); }
  .sidebar-rail svg { width:12px; height:12px; color:var(--gf-text-muted); }
  .detail-rail { width:16px; background:var(--gf-surface); border-left:1px solid var(--gf-border-subtle); display:none; align-items:center; justify-content:center; cursor:pointer; flex-shrink:0; }
  .detail-rail.visible { display:flex; }
  .detail-rail:hover { background:var(--gf-elevated); }
  .detail-rail svg { width:12px; height:12px; color:var(--gf-text-muted); }
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
  .detail-panel { width:var(--gf-detail-w); background:var(--gf-surface); border-left:1px solid var(--gf-border-subtle); display:flex; flex-direction:column; flex-shrink:0; overflow:hidden; transition:width var(--gf-transition-normal); }
  .detail-panel.collapsed { width:0; border-left:none; }
  .detail-header { padding:16px; border-bottom:1px solid var(--gf-border-subtle); flex-shrink:0; display:flex; align-items:center; }
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
  .detail-field-value { color:var(--gf-text-secondary); font-family:var(--gf-font-mono); font-size:0.6875rem; min-width:0; word-break:break-all; }
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
  .edit-note { font-size:0.6875rem; color:var(--gf-text-faint); margin-top:8px; font-family:var(--gf-font-mono); word-break:break-all; }

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

  /* Learn tab v2 —— 多视角（业务流 / 代码架构 / 特性下钻） */
  .learn-shell { flex:1; display:flex; overflow:hidden; }
  .learn-guide { padding:24px; color:var(--gf-text-muted); font-size:0.75rem; line-height:1.8; }
  .learn-guide code { font-family:var(--gf-font-mono); background:var(--gf-panel); padding:1px 5px; border-radius:4px; color:var(--gf-accent-bright); }
  .persp-nav { width:300px; flex-shrink:0; background:var(--gf-surface); border-right:1px solid var(--gf-border-subtle); display:flex; flex-direction:column; }
  .persp-group { border-bottom:1px solid var(--gf-border-subtle); }
  .persp-head { display:flex; align-items:center; gap:8px; padding:12px; cursor:pointer; user-select:none; border-left:2px solid transparent; }
  .persp-head:hover { background:var(--gf-elevated); }
  .persp-group.open .persp-head { border-left-color:var(--gf-accent); background:linear-gradient(90deg, rgba(78,121,167,0.06), transparent 70%); }
  .persp-head .chev { transition:transform var(--gf-transition); color:var(--gf-text-faint); font-size:9px; }
  .persp-group.open .persp-head .chev { transform:rotate(90deg); }
  .persp-title { font-family:var(--gf-font-heading); font-size:0.75rem; font-weight:600; color:var(--gf-text-primary); }
  .persp-sub { font-size:0.625rem; color:var(--gf-text-muted); margin-top:1px; }
  .persp-items { display:none; padding-bottom:8px; }
  .persp-group.open .persp-items { display:block; }
  .persp-item { display:flex; align-items:center; gap:8px; width:100%; text-align:left; padding:5px 12px 5px 24px; border:none; border-left:2px solid transparent; background:transparent; font-family:var(--gf-font-body); font-size:0.75rem; color:var(--gf-text-secondary); cursor:pointer; border-radius:0 4px 4px 0; transition:background var(--gf-transition); }
  .persp-item:hover { background:var(--gf-elevated); }
  .persp-item.active { background:rgba(78,121,167,0.08); color:var(--gf-accent-bright); border-left-color:var(--gf-accent); }
  .persp-item .meta { margin-left:auto; font-family:var(--gf-font-mono); font-size:0.5625rem; color:var(--gf-text-faint); white-space:nowrap; }
  .persp-item .md-badge { font-family:var(--gf-font-mono); font-size:0.5rem; padding:1px 5px; border-radius:var(--gf-radius-full,99px); background:var(--gf-status-inferred-bg); color:var(--gf-status-inferred); flex-shrink:0; }
  .learn-footer { margin-top:auto; border-top:1px solid var(--gf-border-subtle); padding:8px 16px; font-size:0.625rem; color:var(--gf-text-muted); display:flex; align-items:center; gap:6px; flex-wrap:wrap; }
  .learn-footer .b { font-family:var(--gf-font-mono); font-size:0.5625rem; padding:1px 5px; border-radius:99px; }
  .learn-footer .b1 { background:var(--gf-status-extracted-bg); color:var(--gf-status-extracted); }
  .learn-footer .b2 { background:var(--gf-status-inferred-bg); color:var(--gf-status-inferred); }

  /* 学习视图容器 */
  .lview { flex:1; display:none; min-width:0; overflow:hidden; animation:learnViewIn 240ms ease-out; }
  .lview.active { display:flex; }
  @keyframes learnViewIn { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:translateY(0); } }

  /* 业务流视角 */
  .stage { flex:1; display:flex; flex-direction:column; min-width:0; }
  .stage-crumb { display:flex; align-items:center; gap:6px; padding:10px 24px; font-family:var(--gf-font-mono); font-size:0.625rem; color:var(--gf-text-muted); border-bottom:1px solid var(--gf-border-subtle); background:var(--gf-surface); }
  .stage-crumb .here { color:var(--gf-accent-bright); }
  .stage-crumb .prov { margin-left:auto; color:var(--gf-text-faint); }
  .stage-scroll { flex:1; overflow:auto; padding:20px 24px; }
  .stage-title-row { display:flex; align-items:baseline; gap:16px; margin-bottom:12px; flex-wrap:wrap; }
  .stage-title-row h1 { font-family:var(--gf-font-heading); font-size:1.375rem; font-weight:600; letter-spacing:-0.01em; }
  .member-chip { font-family:var(--gf-font-mono); font-size:0.5625rem; padding:2px 8px; border-radius:99px; border:1px solid var(--gf-border-medium); color:var(--gf-text-secondary); cursor:pointer; background:var(--gf-panel); }
  .member-chip:hover { border-color:var(--gf-accent); color:var(--gf-accent-bright); }
  .diagram-frame { background:var(--gf-panel); border:1px solid var(--gf-border-subtle); border-radius:12px; padding:12px; }
  .diagram-frame .mermaid { display:flex; justify-content:center; overflow-x:auto; }
  .diagram-frame .mermaid-src { font-family:var(--gf-font-mono); font-size:0.6875rem; color:var(--gf-text-secondary); white-space:pre-wrap; padding:8px; }
  .step-timeline { padding:16px 24px 24px; border-top:1px solid var(--gf-border-subtle); background:var(--gf-surface); }
  .step-tl-head { display:flex; align-items:center; gap:12px; margin-bottom:8px; }
  .step-tl-nav { margin-left:auto; display:flex; align-items:center; gap:8px; }
  .step-tl-nav .pos { font-family:var(--gf-font-mono); font-size:0.625rem; color:var(--gf-text-muted); }
  .step-btn { width:26px; height:26px; border-radius:4px; border:1px solid var(--gf-border-medium); background:var(--gf-panel); color:var(--gf-text-secondary); cursor:pointer; }
  .step-btn:disabled { opacity:0.3; cursor:default; }
  .step-btn:hover:not(:disabled) { border-color:var(--gf-accent); color:var(--gf-accent-bright); }
  .step-track { display:flex; gap:2px; margin-bottom:12px; }
  .step-seg { flex:1; height:3px; border-radius:2px; background:var(--gf-panel); cursor:pointer; }
  .step-seg.done { background:var(--gf-accent-dim); }
  .step-seg.current { background:var(--gf-accent); box-shadow:0 0 8px var(--gf-accent-glow); }
  .step-card { display:flex; gap:16px; background:var(--gf-panel); border:1px solid var(--gf-border-subtle); border-radius:12px; padding:12px 16px; }
  .step-idx { font-family:var(--gf-font-mono); font-size:1.375rem; font-weight:600; color:var(--gf-accent-bright); width:32px; flex-shrink:0; }
  .step-msg { font-family:var(--gf-font-mono); font-size:0.75rem; color:var(--gf-text-primary); margin-bottom:4px; }
  .step-msg .ar { color:var(--gf-accent); }
  .step-desc { font-size:0.75rem; line-height:1.65; color:var(--gf-text-secondary); }
  .step-desc code { font-family:var(--gf-font-mono); font-size:0.85em; background:var(--gf-surface); padding:1px 4px; border-radius:3px; color:var(--gf-accent-bright); }
  .step-cite { font-family:var(--gf-font-mono); font-size:0.5625rem; color:var(--gf-text-faint); margin-top:4px; }
  .ctx-panel { width:320px; flex-shrink:0; border-left:1px solid var(--gf-border-subtle); background:var(--gf-surface); display:flex; flex-direction:column; overflow:hidden; }
  .ctx-head { padding:16px; border-bottom:1px solid var(--gf-border-subtle); }
  .ctx-body { flex:1; overflow-y:auto; padding:16px; }
  .ctx-name { font-family:var(--gf-font-mono); font-size:0.8125rem; font-weight:600; }
  .ctx-intent { font-size:0.75rem; line-height:1.6; color:var(--gf-text-secondary); margin:8px 0; }
  .learn-lbl { font-size:0.5625rem; color:var(--gf-text-muted); text-transform:uppercase; letter-spacing:0.06em; font-weight:600; display:block; margin-bottom:4px; }
  .anchor-chip { display:inline-flex; align-items:center; gap:3px; font-family:var(--gf-font-mono); font-size:0.5625rem; padding:2px 7px; margin:0 3px 3px 0; border-radius:4px; border:1px solid var(--gf-border-medium); background:var(--gf-panel); color:var(--gf-text-secondary); cursor:pointer; transition:all var(--gf-transition); }
  .anchor-chip:hover { border-color:var(--gf-accent); color:var(--gf-accent-bright); }
  .anchor-chip::before { content:''; width:4px; height:4px; border-radius:50%; background:var(--gf-accent); }
  .rf-item { display:flex; align-items:center; gap:8px; padding:8px 12px; margin-bottom:8px; background:var(--gf-panel); border:1px solid var(--gf-border-subtle); border-radius:8px; cursor:pointer; font-size:0.75rem; color:var(--gf-text-secondary); width:100%; text-align:left; font-family:var(--gf-font-body); transition:all var(--gf-transition); }
  .rf-item:hover { background:var(--gf-elevated); }
  .rf-item .go { margin-left:auto; color:var(--gf-text-faint); }
  .ctx-div { height:1px; background:var(--gf-border-subtle); margin:12px 0; }

  /* 代码架构视角 */
  .arch-center { flex:1; overflow-y:auto; padding:20px 24px; display:flex; flex-direction:column; gap:20px; }
  .arch-card { background:var(--gf-surface); border:1px solid var(--gf-border-subtle); border-radius:12px; padding:16px; }
  .arch-card h3 { font-family:var(--gf-font-heading); font-size:0.875rem; font-weight:600; margin-bottom:12px; display:flex; align-items:baseline; gap:8px; flex-wrap:wrap; }
  .arch-card h3 .cnt { font-family:var(--gf-font-mono); font-size:0.5625rem; color:var(--gf-text-faint); font-weight:400; }
  .dir-tree { font-family:var(--gf-font-mono); font-size:0.75rem; line-height:1.9; color:var(--gf-text-secondary); }
  .dir-tree .dir { color:var(--gf-accent-bright); font-weight:600; }
  .dir-tree .row { display:flex; gap:8px; padding:0 6px; margin:0 -2px; border-radius:4px; cursor:pointer; }
  .dir-tree .row::before { content:''; width:5px; height:5px; border-radius:2px; background:var(--gf-border-strong); flex-shrink:0; margin-top:8px; }
  .dir-tree .row.dir-row::before { border-radius:50%; background:var(--gf-accent-dim); }
  .dir-tree .row:hover { background:var(--gf-elevated); }
  .dir-tree .ncnt { margin-left:auto; color:var(--gf-text-faint); font-size:0.5625rem; white-space:nowrap; }
  .feat-grid { display:grid; grid-template-columns:repeat(2,1fr); gap:12px; }
  .feat-card { background:var(--gf-panel); border:1px solid var(--gf-border-subtle); border-radius:8px; padding:12px; cursor:pointer; transition:all var(--gf-transition); }
  .feat-card:hover { transform:translateY(-1px); box-shadow:var(--gf-shadow-md); border-color:rgba(78,121,167,0.4); }
  .feat-name { font-size:0.75rem; font-weight:600; color:var(--gf-text-primary); display:flex; align-items:center; gap:6px; }
  .feat-name .go { margin-left:auto; color:var(--gf-accent); font-size:0.625rem; opacity:0; transition:opacity var(--gf-transition); }
  .feat-card:hover .feat-name .go { opacity:1; }
  .feat-desc { font-size:0.625rem; color:var(--gf-text-muted); margin:4px 0; line-height:1.5; }
  .feat-meta { font-family:var(--gf-font-mono); font-size:0.5625rem; color:var(--gf-text-faint); }
  .arch-right { width:42%; flex-shrink:0; border-left:1px solid var(--gf-border-subtle); display:flex; flex-direction:column; background:var(--gf-root); }
  .arch-right .panel-head { padding:12px 16px; border-bottom:1px solid var(--gf-border-subtle); background:var(--gf-surface); }
  .arch-right .diagram-scroll { flex:1; overflow:auto; padding:16px; }
  .arch-right .cap { padding:8px 16px; font-family:var(--gf-font-mono); font-size:0.5625rem; color:var(--gf-text-muted); border-top:1px solid var(--gf-border-subtle); background:var(--gf-surface); }

  /* 特性下钻视角 */
  .doc-scroll { flex:1; overflow-y:auto; }
  .doc { max-width:820px; margin:0 auto; padding:24px 24px 140px; }
  .doc-header { display:flex; align-items:center; gap:12px; margin-bottom:8px; }
  .doc-header h1 { font-family:var(--gf-font-heading); font-size:1.75rem; font-weight:700; }
  .md-toggle { margin-left:auto; display:flex; background:var(--gf-panel); border-radius:8px; padding:2px; }
  .md-toggle button { border:none; background:transparent; padding:4px 12px; font-family:var(--gf-font-mono); font-size:0.625rem; color:var(--gf-text-muted); border-radius:6px; cursor:pointer; }
  .md-toggle button.active { background:var(--gf-surface); color:var(--gf-accent-bright); box-shadow:var(--gf-shadow-sm); }
  .doc-meta { display:flex; gap:8px; margin-bottom:20px; flex-wrap:wrap; }
  .doc h2 { font-family:var(--gf-font-heading); font-size:1.0625rem; font-weight:600; margin:24px 0 8px; display:flex; align-items:baseline; gap:8px; }
  .doc h2 .no { font-family:var(--gf-font-mono); font-size:0.625rem; color:var(--gf-accent); }
  .doc p { font-size:0.8125rem; line-height:1.7; color:var(--gf-text-secondary); margin-bottom:12px; }
  .doc ul { margin:0 0 12px 16px; }
  .doc li { font-size:0.8125rem; line-height:1.7; color:var(--gf-text-secondary); margin-bottom:8px; }
  .tp-list { display:flex; flex-direction:column; gap:8px; margin:12px 0; }
  .tp-item { background:var(--gf-surface); border:1px solid var(--gf-border-subtle); border-radius:8px; padding:12px 16px; transition:border-color var(--gf-transition); }
  .tp-item:hover { border-color:rgba(78,121,167,0.35); }
  .tp-name { font-size:0.75rem; font-weight:600; color:var(--gf-text-primary); }
  .tp-why { font-size:0.75rem; color:var(--gf-text-secondary); line-height:1.6; margin:3px 0 6px; }
  .code-block { background:var(--gf-panel); border:1px solid var(--gf-border-subtle); border-radius:8px; overflow:hidden; margin:12px 0; }
  .code-block .cb-head { display:flex; align-items:center; padding:6px 12px; border-bottom:1px solid var(--gf-border-subtle); font-family:var(--gf-font-mono); font-size:0.5625rem; color:var(--gf-text-muted); background:var(--gf-surface); gap:6px; }
  .code-block .cb-head .fn { color:var(--gf-accent-bright); }
  .code-block .cb-head .tier { font-size:0.5rem; padding:1px 6px; border-radius:99px; background:var(--gf-status-ambiguous-bg); color:var(--gf-status-ambiguous); margin-left:auto; }
  .code-block pre { font-family:var(--gf-font-mono); font-size:0.6875rem; line-height:1.7; padding:8px 0; overflow-x:auto; color:var(--gf-text-secondary); margin:0; }
  .cl { display:flex; gap:12px; padding:0 12px; white-space:pre; }
  .cl .ln { color:var(--gf-text-faint); width:24px; text-align:right; flex-shrink:0; user-select:none; }
  .cl.focal { background:rgba(78,121,167,0.08); box-shadow:inset 2px 0 0 var(--gf-accent); }
  .cl.focal .ln { color:var(--gf-accent-bright); font-weight:600; }
  .cl .note { color:var(--gf-status-ambiguous); font-style:italic; }
  .doc .mermaid { background:var(--gf-panel); border:1px solid var(--gf-border-subtle); border-radius:12px; padding:12px; margin:12px 0; display:flex; justify-content:center; overflow-x:auto; }
  .md-src { display:none; font-family:var(--gf-font-mono); font-size:0.6875rem; line-height:1.7; color:var(--gf-text-secondary); white-space:pre-wrap; background:var(--gf-panel); border:1px solid var(--gf-border-subtle); border-radius:12px; padding:16px; }
  .doc-wrap.show-src .doc-render { display:none; }
  .doc-wrap.show-src .md-src { display:block; }
  .doc-rail { width:280px; flex-shrink:0; border-left:1px solid var(--gf-border-subtle); background:var(--gf-surface); overflow-y:auto; padding:16px; }
  .rail-item { display:flex; align-items:center; gap:8px; padding:4px 8px; font-size:0.6875rem; color:var(--gf-text-secondary); border-radius:4px; cursor:pointer; border:none; border-left:2px solid transparent; background:transparent; width:100%; text-align:left; font-family:var(--gf-font-body); transition:all var(--gf-transition); }
  .rail-item:hover { background:var(--gf-elevated); border-left-color:var(--gf-accent); }
  .rail-item .no { font-family:var(--gf-font-mono); font-size:0.5625rem; color:var(--gf-accent); width:16px; }

  /* Learn v3: 图谱 / 项目导览 / 业务领域 新视角 */
 .project-summary { padding:12px 16px; border-bottom:1px solid var(--gf-border-subtle); }
 .project-summary .ps-title { font-family:var(--gf-font-heading); font-size:0.8125rem; font-weight:600; color:var(--gf-text-primary); }
 .graph-hint { padding:16px 24px; background:var(--gf-elevated); border-bottom:1px solid var(--gf-border-subtle); font-size:0.75rem; color:var(--gf-text-secondary); line-height:1.6; display:flex; align-items:center; gap:8px; }
 .graph-hint::before { content:''; width:6px; height:6px; border-radius:50%; background:var(--gf-accent); flex-shrink:0; }
 /* 图谱视图切换按钮（学习页右上角） */
 .learn-graph-toggle { position:absolute; top:8px; right:12px; z-index:10; display:flex; align-items:center; gap:5px; padding:5px 10px; border:1px solid var(--gf-border-medium); background:var(--gf-surface); color:var(--gf-text-secondary); border-radius:6px; font-size:0.6875rem; font-weight:500; cursor:pointer; transition:all var(--gf-transition); }
 .learn-graph-toggle:hover { background:var(--gf-elevated); color:var(--gf-accent-bright); border-color:var(--gf-accent-dim); }
 /* 图谱视图覆盖层 */
 .learn-graph-overlay { position:absolute; top:0; left:0; right:0; bottom:0; z-index:20; background:var(--gf-root); display:flex; flex-direction:column; }
 .lgo-header { display:flex; align-items:center; gap:12px; padding:8px 16px; border-bottom:1px solid var(--gf-border-medium); background:var(--gf-surface); flex-shrink:0; }
 .lgo-title { font-family:var(--gf-font-heading); font-size:0.8125rem; font-weight:600; color:var(--gf-text-primary); }
 .lgo-search { flex:1; max-width:300px; padding:4px 8px; border:1px solid var(--gf-border-medium); border-radius:4px; font-size:0.75rem; background:var(--gf-surface); color:var(--gf-text-primary); }
 .lgo-close { padding:4px 10px; border:1px solid var(--gf-border-medium); background:var(--gf-surface); color:var(--gf-text-secondary); border-radius:4px; font-size:0.6875rem; cursor:pointer; }
 .lgo-close:hover { background:var(--gf-elevated); color:var(--gf-text-primary); }
 .lgo-body { flex:1; display:flex; overflow:hidden; }
 .lgo-canvas { flex:1; overflow:hidden; background:var(--gf-root); }
 .lgo-detail { width:280px; border-left:1px solid var(--gf-border-medium); background:var(--gf-surface); overflow-y:auto; padding:16px; flex-shrink:0; }
 .lgo-detail-hint { font-size:0.75rem; color:var(--gf-text-muted); text-align:center; padding:40px 0; }
 .lgo-detail-header { font-family:var(--gf-font-heading); font-size:0.875rem; font-weight:600; color:var(--gf-text-primary); margin-bottom:12px; padding-bottom:8px; border-bottom:1px solid var(--gf-border-subtle); }
 .lgo-detail-row { display:flex; flex-direction:column; gap:2px; margin-bottom:10px; }
 .lgo-detail-row .lgo-label { font-size:0.625rem; text-transform:uppercase; letter-spacing:0.06em; color:var(--gf-text-faint); font-weight:600; }
 .lgo-detail-row span:last-child { font-size:0.75rem; color:var(--gf-text-secondary); line-height:1.5; }
 .lgo-detail-row.lgo-note { background:rgba(78,121,167,0.06); border-radius:6px; padding:8px; }
 .lgo-detail-row.lgo-note .lgo-label { color:var(--gf-accent); }
  .persp-search { margin:12px 16px; }
  .persp-search input { width:100%; padding:6px 10px; border:1px solid var(--gf-border-medium); border-radius:8px; background:var(--gf-panel); font-size:0.75rem; color:var(--gf-text-primary); outline:none; font-family:var(--gf-font-body); }
  .persp-search input:focus { border-color:var(--gf-accent); box-shadow:0 0 0 2px var(--gf-accent-glow); }
  .node-search-list { flex:1; overflow-y:auto; padding:0 8px 8px; }
  .node-search-item { display:flex; align-items:center; gap:8px; padding:5px 10px; border-radius:6px; cursor:pointer; font-size:0.75rem; color:var(--gf-text-secondary); transition:background var(--gf-transition); border:none; background:transparent; width:100%; text-align:left; font-family:var(--gf-font-body); }
  .node-search-item:hover { background:var(--gf-elevated); color:var(--gf-accent-bright); }
  .node-search-item .ns-dot { width:5px; height:5px; border-radius:50%; flex-shrink:0; }
  .node-search-item .ns-label { flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  .node-search-item .ns-meta { font-family:var(--gf-font-mono); font-size:0.5625rem; color:var(--gf-text-faint); }
  .difficulty-badge { display:inline-flex; align-items:center; font-family:var(--gf-font-mono); font-size:0.5625rem; font-weight:600; padding:2px 8px; border-radius:99px; margin-left:8px; vertical-align:middle; }
  .difficulty-simple { background:var(--gf-status-extracted-bg); color:var(--gf-status-extracted); }
  .difficulty-standard { background:var(--gf-status-inferred-bg); color:var(--gf-status-inferred); }
  .difficulty-complex { background:var(--gf-status-ambiguous-bg); color:var(--gf-status-ambiguous); }
  .entry-point-item { display:flex; align-items:center; gap:10px; padding:8px 12px; margin-bottom:6px; background:var(--gf-panel); border:1px solid var(--gf-border-subtle); border-radius:8px; cursor:pointer; transition:border-color var(--gf-transition); }
  .entry-point-item:hover { border-color:rgba(78,121,167,0.4); }
  .entry-point-item .ep-type { font-family:var(--gf-font-mono); font-size:0.5625rem; font-weight:600; padding:2px 7px; border-radius:4px; background:var(--gf-status-inferred-bg); color:var(--gf-status-inferred); text-transform:uppercase; flex-shrink:0; }
  .entry-point-item .ep-handler { font-family:var(--gf-font-mono); font-size:0.75rem; color:var(--gf-text-primary); font-weight:600; }
  .entry-point-item .ep-path { font-family:var(--gf-font-mono); font-size:0.5625rem; color:var(--gf-text-muted); margin-left:auto; }
  .tech-stack-pill { display:inline-flex; align-items:center; font-family:var(--gf-font-mono); font-size:0.625rem; font-weight:500; padding:3px 10px; border-radius:99px; border:1px solid var(--gf-border-medium); background:var(--gf-panel); color:var(--gf-text-secondary); margin:0 4px 4px 0; }
  .domain-card { background:var(--gf-surface); border:1px solid var(--gf-border-subtle); border-radius:12px; padding:16px; margin-bottom:12px; }
  .domain-card h3 { font-family:var(--gf-font-heading); font-size:0.9375rem; font-weight:600; margin-bottom:8px; display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
  .domain-card .dom-meta { font-family:var(--gf-font-mono); font-size:0.5625rem; color:var(--gf-text-faint); }
  .domain-card .dom-desc { font-size:0.75rem; line-height:1.6; color:var(--gf-text-secondary); margin-bottom:8px; }
  .domain-card .dom-section { margin-top:8px; }
  .domain-card .dom-files, .domain-card .dom-symbols { display:flex; flex-wrap:wrap; gap:4px; margin-top:4px; }
  .domain-card .dom-file, .domain-card .dom-sym { font-family:var(--gf-font-mono); font-size:0.5625rem; padding:2px 6px; border-radius:4px; background:var(--gf-panel); color:var(--gf-text-secondary); border:1px solid var(--gf-border-subtle); cursor:pointer; }
  .domain-card .dom-file:hover, .domain-card .dom-sym:hover { border-color:var(--gf-accent); color:var(--gf-accent-bright); }
  .tour-step { display:flex; gap:12px; padding:10px 12px; margin-bottom:6px; background:var(--gf-panel); border:1px solid var(--gf-border-subtle); border-radius:8px; cursor:pointer; transition:border-color var(--gf-transition); }
  .tour-step:hover { border-color:rgba(78,121,167,0.4); }
  .tour-step .ts-idx { font-family:var(--gf-font-mono); font-size:0.875rem; font-weight:600; color:var(--gf-accent-bright); width:24px; flex-shrink:0; }
  .tour-step .ts-title { font-size:0.75rem; font-weight:600; color:var(--gf-text-primary); }
  .tour-step .ts-desc { font-size:0.6875rem; color:var(--gf-text-muted); margin-top:2px; line-height:1.5; }
  .tour-step .ts-nodes { display:flex; flex-wrap:wrap; gap:3px; margin-top:4px; }
  .tour-step .ts-node { font-family:var(--gf-font-mono); font-size:0.5rem; padding:1px 5px; border-radius:3px; background:var(--gf-elevated); color:var(--gf-text-secondary); border:1px solid var(--gf-border-subtle); cursor:pointer; }
  .tour-step .ts-node:hover { border-color:var(--gf-accent); color:var(--gf-accent-bright); }
  .tour-progress-bar { height:4px; background:var(--gf-panel); border-radius:2px; overflow:hidden; margin-bottom:12px; }
  .tour-progress-fill { height:100%; background:var(--gf-accent); border-radius:2px; transition:width 200ms ease-out; }
  .node-note { margin:6px 0; padding:8px 10px; background:rgba(78,121,167,0.06); border-left:3px solid var(--gf-accent); border-radius:0 6px 6px 0; font-size:0.6875rem; line-height:1.6; color:var(--gf-text-secondary); }
  .node-note .nn-label { font-size:0.5625rem; color:var(--gf-accent-bright); text-transform:uppercase; letter-spacing:0.06em; font-weight:600; display:block; margin-bottom:2px; }
  .arch-tree-toggle { display:inline-flex; align-items:center; gap:4px; font-family:var(--gf-font-mono); font-size:0.5625rem; padding:2px 8px; border:1px solid var(--gf-border-medium); border-radius:6px; background:var(--gf-panel); color:var(--gf-text-muted); cursor:pointer; margin-left:auto; }
  .arch-tree-toggle:hover { border-color:var(--gf-accent); color:var(--gf-accent-bright); }
  .dir-tree.collapsed .row:nth-child(n+8) { display:none; }

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

  /* BC bubble diagram */
  .bc-bubble-svg { width:100%; height:420px; display:block; }
  .bc-bubble-line { stroke:var(--gf-border-medium); stroke-width:1.5; opacity:0.35; }
  .bc-bubble-line-thick { stroke-width:3; opacity:0.5; }
  .bc-bubble-circle { cursor:pointer; transition:filter var(--gf-transition); }
  .bc-bubble-circle:hover { filter: brightness(1.2); }
  .bc-bubble-label { font-family:var(--gf-font-heading); font-size:10px; font-weight:600; fill:var(--gf-text-primary); text-anchor:middle; pointer-events:none; }
  .bc-bubble-count { font-family:var(--gf-font-mono); font-size:8px; fill:var(--gf-text-muted); text-anchor:middle; pointer-events:none; }
  .bc-edge-label { font-family:var(--gf-font-mono); font-size:7px; fill:var(--gf-text-faint); text-anchor:middle; pointer-events:none; }

  /* Overview two-column */
  .ovw-two-col { display:flex; gap:16px; margin-bottom:16px; }
  .ovw-left { flex:0 0 320px; display:flex; flex-direction:column; gap:12px; }
  .ovw-right { flex:1; min-width:0; }
  .ovw-info-card { background:var(--gf-surface); border:1px solid var(--gf-border-subtle); border-radius:var(--gf-radius-lg); padding:16px; box-shadow:var(--gf-shadow-sm); }
  .ovw-info-row { display:flex; justify-content:space-between; align-items:center; padding:6px 0; border-bottom:1px solid var(--gf-border-subtle); }
  .ovw-info-row:last-child { border-bottom:none; }
  .ovw-info-label { font-size:0.75rem; color:var(--gf-text-muted); }
  .ovw-info-value { font-size:0.75rem; font-weight:600; color:var(--gf-text-primary); font-family:var(--gf-font-mono); }
  .ovw-lang-bar { display:flex; align-items:center; gap:4px; margin-top:8px; }
  .ovw-lang-seg { height:20px; border-radius:3px; display:flex; align-items:center; justify-content:center; font-size:9px; color:#fff; font-weight:600; font-family:var(--gf-font-mono); overflow:hidden; }
  .ovw-tech-tags { display:flex; flex-wrap:wrap; gap:4px; margin-top:8px; }
  .ovw-tech-tag { padding:2px 8px; border-radius:12px; background:var(--gf-panel); border:1px solid var(--gf-border-medium); font-size:0.6875rem; color:var(--gf-text-secondary); font-family:var(--gf-font-mono); }

  /* Tab pages visibility */
  .ovw-hero-card { background:var(--gf-surface); border:1px solid var(--gf-border-subtle); border-radius:var(--gf-radius-lg); padding:24px 32px; margin-bottom:24px; box-shadow:var(--gf-shadow-sm); display:flex; align-items:center; gap:24px; }
  .ovw-hero-info { flex:1; }
  .ovw-hero-lang { font-family:var(--gf-font-heading); font-size:1.5rem; font-weight:700; color:var(--gf-text-primary); }
  .ovw-hero-meta { font-size:0.75rem; color:var(--gf-text-muted); margin-top:4px; }
  .ovw-hero-stats { display:flex; gap:20px; }
  .ovw-hero-stat { text-align:center; }
  .ovw-hero-stat-val { font-family:var(--gf-font-heading); font-size:1.5rem; font-weight:700; color:var(--gf-text-primary); }
  .ovw-hero-stat-lbl { font-size:0.6875rem; color:var(--gf-text-muted); text-transform:uppercase; letter-spacing:0.08em; font-weight:600; }

  /* Tab pages visibility */
 .tab-page { display:none; flex:1; min-height:0; position:relative; }
 .tab-page.active { display:flex; }

  /* Scrollbar */
  ::-webkit-scrollbar { width:6px; height:6px; }
  ::-webkit-scrollbar-track { background:transparent; }
  ::-webkit-scrollbar-thumb { background:rgba(78,121,167,0.15); border-radius:6px; }
  ::-webkit-scrollbar-thumb:hover { background:rgba(78,121,167,0.28); }
  :focus-visible { outline:2px solid var(--gf-accent); outline-offset:2px; }

  /* All-props modal */
  .props-modal { position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.4); z-index:9999; display:flex; align-items:center; justify-content:center; }
  .props-modal-content { background:var(--gf-surface); border-radius:var(--gf-radius-lg); box-shadow:var(--gf-shadow-lg); max-width:600px; width:90%; max-height:80vh; overflow:hidden; display:flex; flex-direction:column; }
  .props-modal-header { padding:16px 20px; border-bottom:1px solid var(--gf-border-subtle); display:flex; align-items:center; }
  .props-modal-title { font-family:var(--gf-font-heading); font-size:0.9375rem; font-weight:600; color:var(--gf-text-primary); flex:1; }
  .props-modal-body { padding:16px 20px; overflow-y:auto; flex:1; }
  .props-modal-row { padding:6px 0; border-bottom:1px solid var(--gf-border-subtle); }
  .props-modal-row:last-child { border-bottom:none; }
  .props-modal-key { font-size:0.6875rem; color:var(--gf-text-muted); text-transform:uppercase; letter-spacing:0.04em; font-weight:600; margin-bottom:2px; }
  .props-modal-val { font-size:0.75rem; color:var(--gf-text-secondary); font-family:var(--gf-font-mono); word-break:break-all; white-space:pre-wrap; }
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


def _html_script(nodes_json: str, edges_json: str, legend_json: str, type_index_json: str, tag_index_json: str, review_json: str = "[]", bc_bubbles_json: str = "[]", bc_links_json: str = "[]", lang_donut_json: str = "[]", lang_total: int = 0, bc_details_json: str = "[]", learn_json: str = "null") -> str:
    return f"""<script>
const RAW_NODES = {nodes_json};
const RAW_EDGES = {edges_json};
const LEGEND = {legend_json};
const TYPE_INDEX = {type_index_json};
const TAG_INDEX = {tag_index_json};
const REVIEW = {review_json};
const LEARN = {learn_json};
const COMMUNITY_COLORS = ["#4E79A7","#F28E2B","#E15759","#76B7B2","#59A14F","#EDC948","#B07AA1","#FF9DA7","#9C755F","#BAB0AC"];
const BC_BUBBLES = {bc_bubbles_json};
const BC_LINKS = {bc_links_json};
const LANG_DONUT = {lang_donut_json};
const LANG_TOTAL = {lang_total};
const BC_DETAILS = {bc_details_json};

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
  _raw: n,  // keep full raw node data for detail display
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

// Edge index for the audit detail panel: undirected storage keeps one edge
// per node pair, so "from|to" in true direction is a unique key.
const EDGE_BY_KEY = {{}};
RAW_EDGES.forEach((e, i) => {{ EDGE_BY_KEY[e.from + '|' + e.to] = Object.assign({{ _visId: i }}, e); }});
function findEdge(from, to) {{
  return EDGE_BY_KEY[from + '|' + to] || EDGE_BY_KEY[to + '|' + from] || null;
}}

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
const bottomBar = document.querySelector('.bottom-bar');

function moveToTab(target) {{
  tabs.forEach(t => t.classList.remove('active'));
  document.querySelector('.mode-tab[data-tab="' + target + '"]').classList.add('active');
  tabPages.forEach(p => p.classList.remove('active'));
  const page = document.getElementById('page-' + target);
  if (page) page.classList.add('active');
  // The graph lives in the review tab only. Overview and learn own their
  // space (learn = multi-perspective reading UI), so both hide the bottom bar.
  if (target === 'review') {{
    reviewGraphArea.insertBefore(graphEl, reviewGraphArea.firstChild);
    if (bottomBar) bottomBar.style.display = 'flex';
    setTimeout(() => network.redraw(), 50);
  }} else {{
    if (bottomBar) bottomBar.style.display = 'none';
  }}
}}
tabs.forEach(tab => {{
  tab.addEventListener('click', () => {{
    moveToTab(tab.dataset.tab);
  }});
}});

// == Review queue threshold filter ==
function filterReviewQueue(threshold) {{
  document.getElementById('threshold-value').textContent = parseFloat(threshold).toFixed(2);
  const items = document.querySelectorAll('.node-item[data-score]');
  let visible = 0;
  items.forEach(item => {{
    const score = parseFloat(item.dataset.score);
    if (score < threshold) {{
      item.style.display = '';
      visible++;
    }} else {{
      item.style.display = 'none';
    }}
  }});
  // Update the count in the sidebar header
  const meta = document.querySelector('#review-sidebar .sidebar-meta');
  if (meta) meta.textContent = visible + ' 项待审核';
  const badge = document.getElementById('review-badge');
  if (badge) badge.textContent = visible;
}}

// Audit reason card: label + wrapped text. word-break keeps long paths and
// verbatim quotes readable inside the detail panel (fixed-width, no clipping).
function gfReasonBlock(label, text) {{
  if (!text) return '';
  return '<div style="margin:2px 0 8px">' +
    '<div style="font-size:0.5625rem;color:var(--gf-text-muted);text-transform:uppercase;letter-spacing:0.06em;font-weight:600;margin-bottom:2px">' + esc(label) + '</div>' +
    '<div style="font-size:0.6875rem;color:var(--gf-text-secondary);white-space:pre-wrap;word-break:break-all;line-height:1.5;background:var(--gf-elevated);padding:6px 8px;border-radius:6px;border-left:2px solid var(--gf-accent)">' + esc(text) + '</div>' +
  '</div>';
}}

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
  // Follow the detail panel: whichever review item (if any) the shown node
  // belongs to is the current 跳过/提交修正 target.
  _currentReviewItem = reviewItem || null;

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
  const detailHeader = document.getElementById('detail-header-content');
  const editSection = document.getElementById('edit-section');

  // Teaching annotation from LEARN.node_notes (v3)
  const nodeNotes = (LEARN && LEARN.node_notes && LEARN.node_notes.notes) || {{}};
  const nodeNote = nodeNotes[nodeId];
  const nodeNoteHtml = nodeNote ? `<div class="node-note"><span class="nn-label">\u6559\u5b66\u6ce8\u89e3</span>${{esc(String(nodeNote).slice(0, 500))}}</div>` : '';

  // Audit provenance section: extraction reason / evidence quote / evaluation
  // verdict for nodes implicated in the review queue (parity with edges).
  const auditHtml = (reviewItem && (reviewItem.reason || reviewItem.evidence_quote || reviewItem.evaluation_reason))
    ? `
    <div class="detail-field" style="flex-direction:column;align-items:flex-start;border-bottom:none;padding-top:8px">
      <span class="detail-field-label" style="margin-bottom:4px">审查依据</span>
    </div>
    ${{gfReasonBlock('推断理由', reviewItem.reason)}}
    ${{gfReasonBlock('原文引用', reviewItem.evidence_quote)}}
    ${{gfReasonBlock('评估结论', reviewItem.evaluation_reason)}}
    ${{reviewItem.source_location ? `<div class="detail-field"><span class="detail-field-label">位置</span><span class="detail-field-value">${{esc(reviewItem.source_location)}}</span></div>` : ''}}`
    : '';

  detailHeader.innerHTML = `
    <div class="detail-name">${{esc(n.label)}}</div>
    <div class="detail-meta">${{confBadge}} ${{kindHtml}} <span>${{esc(n._file_type || 'unknown')}}</span></div>
  `;
  detailBody.innerHTML = `
    <div class="detail-field"><span class="detail-field-label">来源文件</span><span class="detail-field-value">${{esc(n._source_file || '-')}}</span></div>
    ${{n._raw && n._raw.desc ? `<div class="detail-field" style="flex-direction:column;align-items:flex-start"><span class="detail-field-label" style="margin-bottom:4px">描述</span><span class="detail-field-value" style="font-family:var(--gf-font-body);white-space:pre-wrap;word-break:break-all;font-size:0.6875rem">${{esc((n._raw.desc || '').slice(0,300))}}${{(n._raw.desc || '').length > 300 ? '...' : ''}}</span></div>` : ''}}
    <div class="detail-field"><span class="detail-field-label">社区</span><span class="detail-field-value">${{esc(n._community_name)}}</span></div>
    <div class="detail-field"><span class="detail-field-label">连接数</span><span class="detail-field-value">${{n._degree}}</span></div>
    ${{tagsHtml}}
    ${{auditHtml}}
    ${{nodeNoteHtml}}
    <div style="padding:8px 0"><button class="sidebar-toggle" style="width:auto;padding:4px 10px;border:1px solid var(--gf-border-medium);background:var(--gf-surface);font-size:0.6875rem;font-weight:600;color:var(--gf-text-muted);border-radius:6px" onclick="showAllProps('${{esc(nodeId)}}')">全部属性</button></div>
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

// == Edge detail panel (audit parity with node detail) ==
// Clicking an edge review item (or a graph edge) shows the EDGE's own detail —
// relation, endpoints, source file, extraction reason, evidence quote,
// evaluation verdict — instead of only focusing the source node.
let _currentEdge = null;
function showEdgeInfo(from, to, item) {{
  const e = findEdge(from, to);
  if (!e && !item) return;
  // Track the review item this edge belongs to (for 跳过/提交修正), whether
  // opened from the review list (item passed) or from a canvas edge click
  // (resolved from the queue by edge identity). Non-review edges reset it.
  _currentReviewItem = item
    || REVIEW.find(r => r.edge && r.edge.from === from && r.edge.to === to)
    || null;
  const src = e ? e.from : from, tgt = e ? e.to : to;
  const sN = nodesDS.get(src), tN = nodesDS.get(tgt);
  const sLabel = sN ? sN.label : src, tLabel = tN ? tN.label : tgt;
  const relation = (e && e.label) || (item && item.edge && item.edge.relation) || '';
  const confidence = e ? e.confidence : '';
  const score = e ? e.confidence_score : (item ? item.confidence_score : undefined);
  const reason = (e && e.reason) || (item && item.reason) || '';
  const quote = (e && e.evidence_quote) || (item && item.evidence_quote) || '';
  const evalReason = (e && e.evaluation_reason) || (item && item.evaluation_reason) || '';
  const srcFile = (e && e.source_file) || (item && item.source_file) || '';
  const srcLoc = (e && e.source_location) || (item && item.source_location) || '';
  const badgeCls = confidence === 'EXTRACTED' ? 'kb-extracted' : (confidence === 'AMBIGUOUS' ? 'kb-ambiguous' : 'kb-inferred');
  const scoreTxt = (score !== undefined && score !== null)
    ? ' <span style="font-family:var(--gf-font-mono);color:var(--gf-text-muted)">' + Number(score).toFixed(2) + '</span>'
    : '';
  const detailHeader = document.getElementById('detail-header-content');
  const detailBody = document.getElementById('detail-body');
  const editSection = document.getElementById('edit-section');
  if (detailHeader) {{
    detailHeader.innerHTML =
      '<div class="detail-name">' + esc(sLabel) + ' <span style="color:var(--gf-accent)">&rarr;</span> ' + esc(tLabel) + '</div>' +
      '<div class="detail-meta">' + (confidence ? '<span class="kind-badge ' + badgeCls + '">' + esc(confidence) + '</span> ' : '') +
      '<span>' + esc(relation) + '</span>' + scoreTxt + '</div>';
  }}
  if (detailBody) {{
    detailBody.innerHTML =
      '<div class="detail-field"><span class="detail-field-label">关系</span><span class="detail-field-value">' + esc(relation || '-') + '</span></div>' +
      '<div class="detail-field"><span class="detail-field-label">来源节点</span><span class="detail-field-value"><span class="neighbor-link" style="display:inline;padding:0 4px 0 0" data-nid="' + esc(src) + '">' + esc(sLabel) + '</span></span></div>' +
      '<div class="detail-field"><span class="detail-field-label">目标节点</span><span class="detail-field-value"><span class="neighbor-link" style="display:inline;padding:0 4px 0 0" data-nid="' + esc(tgt) + '">' + esc(tLabel) + '</span></span></div>' +
      '<div class="detail-field"><span class="detail-field-label">来源文件</span><span class="detail-field-value">' + esc(srcFile || '-') + '</span></div>' +
      (srcLoc ? '<div class="detail-field"><span class="detail-field-label">位置</span><span class="detail-field-value">' + esc(srcLoc) + '</span></div>' : '') +
      '<div class="detail-field" style="flex-direction:column;align-items:flex-start;border-bottom:none;padding-top:8px"><span class="detail-field-label" style="margin-bottom:4px">审查依据</span></div>' +
      gfReasonBlock('推断理由', reason) +
      gfReasonBlock('原文引用', quote) +
      gfReasonBlock('评估结论', evalReason) +
      `<div style="padding:4px 0"><button class="sidebar-toggle" style="width:auto;padding:4px 10px;border:1px solid var(--gf-border-medium);background:var(--gf-surface);font-size:0.6875rem;font-weight:600;color:var(--gf-text-muted);border-radius:6px" onclick="showEdgeProps('${{esc(src)}}','${{esc(tgt)}}')">全部属性</button></div>`;
  }}
  if (e && e._visId !== undefined) {{
    try {{ network.selectEdges([e._visId]); network.fit({{ nodes: [src, tgt], animation: {{ duration: 400 }} }}); }} catch (err) {{}}
  }}
  if (editSection) {{
    editSection.style.display = 'block';
    const textarea = document.getElementById('edit-textarea');
    if (textarea) textarea.value = reason || evalReason || (item ? (item.detail || '') : '');
    const filePath = document.getElementById('edit-file-path');
    if (filePath && srcFile) filePath.textContent = '\u2192 ' + srcFile;
  }}
  _currentNodeId = null;
  _currentEdge = {{ from: src, to: tgt, source_file: srcFile }};
}}

function focusNode(nodeId) {{
  network.focus(nodeId, {{ scale: 1.4, animation: true }});
  network.selectNodes([nodeId]);
  showInfo(nodeId);
  _setCurrentNode(nodeId);
  _currentEdge = null;
  // Also select in node list
  document.querySelectorAll('.node-item').forEach(el => el.classList.remove('selected'));
  const listEl = document.querySelector('.node-item[data-nid="' + nodeId + '"]');
  if (listEl) {{
    listEl.classList.add('selected');
    listEl.scrollIntoView({{ block: 'nearest' }});
  }}
  // Update nav buttons with current node context
  const n = nodesDS.get(nodeId);
  document.querySelectorAll('.detail-nav-btn').forEach(btn => {{
    btn.dataset.nodeId = nodeId;
    btn.dataset.sourceFile = n ? (n._source_file || n._raw?.source_file || '') : '';
  }});
}}

// Show all properties in a modal (shared by nodes and edges)
function showPropsModal(raw, title, skipKeys) {{
  // Remove existing modal
  const existing = document.querySelector('.props-modal');
  if (existing) existing.remove();
  // Build modal
  const modal = document.createElement('div');
  modal.className = 'props-modal';
  modal.addEventListener('click', (e) => {{ if (e.target === modal) modal.remove(); }});
  let rowsHtml = '';
  // Always show label first
  rowsHtml += '<div class="props-modal-row"><div class="props-modal-key">label</div><div class="props-modal-val">' + esc(raw.label || title || '') + '</div></div>';
  // Then all other fields (sorted, skip vis-internal)
  const skip = new Set(skipKeys);
  const keys = Object.keys(raw).filter(k => !skip.has(k)).sort();
  for (const key of keys) {{
    let val = raw[key];
    if (val === null || val === undefined || val === '') continue;
    if (Array.isArray(val)) val = val.join(', ');
    else if (typeof val === 'object') val = JSON.stringify(val);
    rowsHtml += '<div class="props-modal-row"><div class="props-modal-key">' + esc(key) + '</div><div class="props-modal-val">' + esc(String(val)) + '</div></div>';
  }}
  modal.innerHTML = 
    '<div class="props-modal-content">' +
      '<div class="props-modal-header">' +
        '<span class="props-modal-title">' + esc(title) + '</span>' +
        '<button class="sidebar-toggle" id="props-modal-close" title="关闭"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>' +
      '</div>' +
      '<div class="props-modal-body">' + rowsHtml + '</div>' +
    '</div>';
  document.body.appendChild(modal);
  // Attach close handler after DOM insertion
  const closeBtn = modal.querySelector('#props-modal-close');
  if (closeBtn) closeBtn.addEventListener('click', () => modal.remove());
}}

function showAllProps(nodeId) {{
  const n = nodesDS.get(nodeId);
  if (!n) return;
  showPropsModal(n._raw || {{}}, n.label || nodeId,
    ['id','label','color','size','font','title','community','community_name','degree']);
}}

function showEdgeProps(from, to) {{
  const e = findEdge(from, to);
  if (!e) return;
  const sN = nodesDS.get(e.from), tN = nodesDS.get(e.to);
  const title = (sN ? sN.label : e.from) + ' \u2192 ' + (tN ? tN.label : e.to);
  showPropsModal(e, title,
    ['from','to','label','title','dashes','width','color','_visId']);
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
    network.selectNodes([params.nodes[0]]);
  }} else if (params.edges && params.edges.length > 0) {{
    // Edge click: show the edge's own audit detail (parity with nodes).
    const raw = RAW_EDGES[params.edges[0]];
    if (raw) showEdgeInfo(raw.from, raw.to);
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
const TYPE_ACTIVE = {{}};   // file_type -> bool (toggle off = hide)
const TAG_SELECTED = new Set();  // selected tags (empty = show all)
let tagOnlyTagged = false;

TYPE_INDEX.forEach(t => {{ TYPE_ACTIVE[t.type] = true; }});

function isNodeHidden(n) {{
  if (!TYPE_ACTIVE[n.file_type]) return true;
  if (hiddenCommunities.has(n.community)) return true;
  const tags = n.tags || [];
  // Tag filter: if no tags selected, show all. If tags selected, show nodes that have at least one selected tag (OR logic).
  if (TAG_SELECTED.size > 0) {{
    if (tags.length === 0) return true;  // hide tagless nodes when filtering by tag
    if (!tags.some(t => TAG_SELECTED.has(t))) return true;
  }}
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
        chip.className = 'filter-chip';
        chip.innerHTML = `${{esc(t.tag)}} <span class="filter-chip-count">${{t.count}}</span>`;
        chip.addEventListener('click', () => {{
          if (TAG_SELECTED.has(t.tag)) {{
            TAG_SELECTED.delete(t.tag);
            chip.classList.remove('active');
          }} else {{
            TAG_SELECTED.add(t.tag);
            chip.classList.add('active');
          }}
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

// == Node list rendering: review list grouped by type ==
const REVIEW_NODE_IDS = new Set(REVIEW.map(r => r.node_id || r.endpointId).filter(Boolean));
const REVIEW_META = {{
  island: {{ label: '孤岛', dot: '#dc4444', badge: 'nb-island', desc: '未匹配的文档锚点' }},
  ambiguous_edge: {{ label: '多匹配', dot: '#d97706', badge: 'nb-ambiguous', desc: '工具多候选，需人工确认' }},
  inferred_edge: {{ label: '推断边', dot: '#2563eb', badge: 'nb-inferred', desc: 'Agent评估为低置信度' }},
  node_review: {{ label: '可疑节点', dot: '#76b7b2', badge: 'nb-gap', desc: '低置信度节点（疑似幻觉）' }},
  semantic_gap: {{ label: 'LLM缺失', dot: '#6b7280', badge: 'nb-gap', desc: 'LLM 语义提取失败' }},
}};
// Temporary "已查看" tracking (session only, not persisted)
const REVIEW_SEEN = new Set();
// The review item currently shown in the detail/edit panel. Gray-out
// (seen + strikethrough) fires ONLY from explicit actions — 跳过 / 提交修正
// / 标记已查看 — never from merely opening an item in the list.
let _currentReviewItem = null;

function reviewTypeOf(item) {{
  if (item.type) return item.type;
  if (item.anchorKind) return 'island';
  if (item.reason && item.reason.includes('LLM')) return 'semantic_gap';
  return 'island';
}}

// Find a node by ID, or by searching label in title string
function findReviewNode(item) {{
  const nodeId = item.node_id || item.endpointId || '';
  if (nodeId && nodesDS.get(nodeId)) return nodeId;
  // Try to find by matching the source node label from the title
  const title = item.title || item.anchor || item.endpointLabel || '';
  if (title) {{
    const parts = title.split(/ -> | -> | -> /);
    for (const part of parts) {{
      const trimmed = part.trim();
      for (const n of RAW_NODES) {{
        if (n.label === trimmed) return n.id;
      }}
    }}
    for (const n of RAW_NODES) {{
      if (n.label && n.label.includes(title.trim())) return n.id;
    }}
  }}
  return null;
}}

function renderNodeList() {{
  const container = document.getElementById('node-list');
  if (!container) return;
  // Preserve the confidence slider (first child), remove the rest
  const slider = container.querySelector('.confidence-bar');
  container.innerHTML = '';
  if (slider) container.appendChild(slider);
  
  // Group review items by type
  const byType = {{}};
  REVIEW.forEach(item => {{
    const type = reviewTypeOf(item);
    if (!byType[type]) byType[type] = [];
    byType[type].push(item);
  }});
  
  // Header for review list
  const header = document.createElement('div');
  header.style.cssText = 'padding:6px 12px;background:var(--gf-panel);border-bottom:1px solid var(--gf-border-subtle)';
  const unseenCount = REVIEW.filter(r => !REVIEW_SEEN.has(r.node_id || r.title)).length;
  header.innerHTML = '<span style="font-size:0.75rem;font-weight:600;color:var(--gf-text-primary)">审核列表</span>' +
    '<span style="margin-left:8px;font-size:0.6875rem;color:var(--gf-text-muted)">' + unseenCount + ' 未查看 / ' + REVIEW.length + ' 总计</span>';
  container.appendChild(header);
  
  // Render each category as a collapsible section
  Object.keys(REVIEW_META).forEach(typeKey => {{
    const meta = REVIEW_META[typeKey];
    const items = byType[typeKey] || [];
    if (items.length === 0) return;
    
    // Category header (collapsible)
    const cat = document.createElement('div');
    cat.style.cssText = 'padding:6px 12px;background:var(--gf-elevated);border-bottom:1px solid var(--gf-border-subtle);cursor:pointer;display:flex;align-items:center;gap:6px;user-select:none';
    const catUnseen = items.filter(r => !REVIEW_SEEN.has(r.node_id || r.title)).length;
    cat.innerHTML = '<span style="width:8px;height:8px;border-radius:50%;background:' + meta.dot + '"></span>' +
      '<span style="font-size:0.75rem;font-weight:600;color:var(--gf-text-primary)">' + esc(meta.label) + '</span>' +
      '<span style="font-size:0.6875rem;color:var(--gf-text-muted)">' + esc(meta.desc) + '</span>' +
      '<span style="margin-left:auto;font-size:0.6875rem;font-weight:600;color:var(--gf-text-muted);font-family:var(--gf-font-mono)">' + catUnseen + '/' + items.length + '</span>';
    let catExpanded = true;
    const list = document.createElement('div');
    cat.addEventListener('click', () => {{
      catExpanded = !catExpanded;
      list.style.display = catExpanded ? 'block' : 'none';
    }});
    container.appendChild(cat);
    container.appendChild(list);
    
    // Render items
    items.forEach(item => {{
      const itemKey = item.node_id || item.title;
      const isSeen = REVIEW_SEEN.has(itemKey);
      const nodeId = findReviewNode(item);
      const el = document.createElement('div');
      el.className = 'node-item';
      if (nodeId) el.dataset.nid = nodeId;
      // Store score for threshold slider filtering
      const itemScore = item.confidence_score !== undefined ? item.confidence_score : 0.0;
      el.dataset.score = itemScore;
      el.style.opacity = isSeen ? '0.4' : '1';
      const title = esc(item.title || item.anchor || item.endpointLabel || '(unnamed)');
      const detail = esc(item.detail || item.reason || '');
      const file = esc(item.source_file || item.file || '');
      const reason = item.evaluation_reason ? esc(item.evaluation_reason) : '';
      const scoreBadge = item.confidence_score !== undefined
        ? '<span style="font-size:9px;font-weight:700;padding:1px 5px;border-radius:10px;font-family:var(--gf-font-mono);margin-left:auto;background:' + (itemScore < 0.1 ? 'var(--gf-status-island-bg)' : (itemScore < 0.6 ? 'var(--gf-status-ambiguous-bg)' : 'var(--gf-status-gap-bg)')) + ';color:' + (itemScore < 0.1 ? 'var(--gf-status-island)' : (itemScore < 0.6 ? 'var(--gf-status-ambiguous)' : 'var(--gf-status-gap)')) + '">' + itemScore.toFixed(2) + '</span>'
        : '';
      el.innerHTML = 
        '<div class="node-item-head">' +
          '<span class="node-status-dot" style="background:' + meta.dot + (isSeen ? ';opacity:0.3' : '') + '"></span>' +
          '<span class="node-title" style="' + (isSeen ? 'text-decoration:line-through;' : '') + '">' + title + '</span>' +
          scoreBadge +
          (isSeen ? '' : '<span style="font-size:0.6875rem;color:var(--gf-text-faint);cursor:pointer" data-action="seen">标记已查看</span>') +
        '</div>' +
        (detail ? '<div class="node-detail">' + detail + '</div>' : '') +
        (item.reason ? '<div class="node-detail" style="color:var(--gf-text-secondary)">为什么: ' + esc(item.reason) + '</div>' : '') +
        (reason ? '<div class="node-detail" style="font-style:italic;color:var(--gf-text-faint)">→ ' + reason + '</div>' : '') +
        (file ? '<div class="node-file" title="' + file + '">' + file + '</div>' : '');
      // Click on "标记已查看" button
      const seenBtn = el.querySelector('[data-action="seen"]');
      if (seenBtn) {{
        seenBtn.addEventListener('click', (e) => {{
          e.stopPropagation();
          REVIEW_SEEN.add(itemKey);
          renderNodeList();
        }});
      }}
      // Click on item -> edge items open the EDGE detail panel (parity with
      // node clicks); node items focus the node (rich detail + edit panel);
      // unresolvable items (islands without a node) fall back to the minimal
      // review view. Opening an item does NOT mark it seen — gray-out happens
      // only via the explicit 跳过 / 提交修正 / 标记已查看 actions.
      el.addEventListener('click', () => {{
        _currentReviewItem = item;
        if (item.edge && findEdge(item.edge.from, item.edge.to)) {{
          showEdgeInfo(item.edge.from, item.edge.to, item);
        }} else if (nodeId && nodesDS.get(nodeId)) {{
          focusNode(nodeId);
        }} else {{
          showReviewEdit(item);
        }}
      }});
      list.appendChild(el);
    }});
  }});
  
  // If no review items, show empty state
  if (REVIEW.length === 0) {{
    const empty = document.createElement('div');
    empty.style.cssText = 'padding:20px;text-align:center;font-size:0.75rem;color:var(--gf-text-muted)';
    empty.textContent = '暂无待审核项';
    container.appendChild(empty);
  }}
  
  // Update review badge count
  const badge = document.getElementById('review-badge');
  if (badge) {{
    badge.textContent = REVIEW.length;
  }}
}}

// Show edit panel for a review item (independent of node focus)
function showReviewEdit(item) {{
  _currentReviewItem = item;
  const editSection = document.getElementById('edit-section');
  if (!editSection) return;
  editSection.style.display = 'block';
  // Update detail header to show review item title
  const detailHeader = document.getElementById('detail-header-content');
  if (detailHeader) {{
    const type = reviewTypeOf(item);
    const meta = REVIEW_META[type] || REVIEW_META.island;
    detailHeader.innerHTML = 
      '<div class="detail-name">' + esc(item.title || item.anchor || item.endpointLabel || '(unnamed)') + '</div>' +
      '<div class="detail-meta"><span class="kind-badge ' + (type === 'island' ? 'kb-island' : (type === 'ambiguous_edge' ? 'kb-ambiguous' : (type === 'inferred_edge' ? 'kb-inferred' : 'kb-island'))) + '">' + esc(meta.label) + '</span> <span>' + esc(item.detail || item.reason || '') + '</span></div>';
  }}
  // Update detail body
  const detailBody = document.getElementById('detail-body');
  if (detailBody) {{
    detailBody.innerHTML = 
      '<div class="detail-field"><span class="detail-field-label">来源文件</span><span class="detail-field-value">' + esc(item.source_file || item.file || '-') + '</span></div>' +
      '<div class="detail-field"><span class="detail-field-label">位置</span><span class="detail-field-value">' + esc(item.source_location || '') + '</span></div>' +
      (item.reason ? '<div class="detail-field" style="flex-direction:column;align-items:flex-start;border-bottom:none;padding-top:8px"><span class="detail-field-label" style="margin-bottom:4px">说明</span></div>' + gfReasonBlock('原因', item.reason) : '');
  }}
  // Pre-fill edit fields
  const detail = item.detail || item.reason || '';
  const file = item.source_file || item.file || '';
  const textarea = document.getElementById('edit-textarea');
  if (textarea && detail) textarea.value = detail;
  const filePath = document.getElementById('edit-file-path');
  if (filePath && file) filePath.textContent = '\u2192 ' + file;
}}

// == Review actions: 跳过 / 提交修正 ==
// These are the ONLY ways (besides the per-item 标记已查看 button) an item
// becomes "seen" (gray + strikethrough). Static HTML cannot write to
// .graph/error-report/, so 提交修正 records the correction for this session
// and clears the form; the graph itself is corrected via the normal flow.
function _reviewItemKey(item) {{
  return item ? (item.node_id || item.title) : null;
}}
function _markCurrentReviewed(actionLabel, extra) {{
  const item = _currentReviewItem;
  const note = document.getElementById('edit-file-path');
  if (!item) {{
    if (note) note.textContent = '\u2192 请先在左侧审核列表中选择一项';
    return;
  }}
  const key = _reviewItemKey(item);
  if (key) REVIEW_SEEN.add(key);
  renderNodeList();
  if (note) note.textContent = '\u2192 已' + actionLabel + '：' + (item.title || key || '') + (extra || '');
  const ta = document.getElementById('edit-textarea');
  if (ta) ta.value = '';
}}
(function() {{
  const skipBtn = document.getElementById('edit-skip');
  if (skipBtn) skipBtn.addEventListener('click', () => _markCurrentReviewed('跳过'));
  const submitBtn = document.getElementById('edit-submit');
  if (submitBtn) submitBtn.addEventListener('click', () => {{
    const ta = document.getElementById('edit-textarea');
    const txt = ta ? (ta.value || '').trim() : '';
    _markCurrentReviewed('提交修正', txt ? '（修正 ' + txt.length + ' 字，已记录到本次会话）' : '');
  }});
}})();

// == Edit tab switching ==
document.addEventListener('click', e => {{
  const tab = e.target.closest('.edit-tab');
  if (tab) {{
    tab.parentElement.querySelectorAll('.edit-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
  }}
}});

// == Render BC bubble diagram with 3D-style spheres + pan/zoom/drag ==
(function() {{
  const svg = document.getElementById('bc-bubbles');
  if (!svg || !BC_BUBBLES.length) return;
  const ns = 'http://www.w3.org/2000/svg';
  svg.style.cursor = 'grab';
  // Define radial gradients for 3D sphere effect
  const defs = document.createElementNS(ns, 'defs');
  BC_BUBBLES.forEach((b, i) => {{
    const grad = document.createElementNS(ns, 'radialGradient');
    grad.setAttribute('id', 'bc-grad-' + i);
    grad.setAttribute('cx', '38%');
    grad.setAttribute('cy', '32%');
    grad.setAttribute('r', '72%');
    const stop1 = document.createElementNS(ns, 'stop');
    stop1.setAttribute('offset', '0%');
    stop1.setAttribute('stop-color', b.color);
    stop1.setAttribute('stop-opacity', '1');
    const stop2 = document.createElementNS(ns, 'stop');
    stop2.setAttribute('offset', '50%');
    stop2.setAttribute('stop-color', b.color);
    stop2.setAttribute('stop-opacity', '0.55');
    const stop3 = document.createElementNS(ns, 'stop');
    stop3.setAttribute('offset', '100%');
    stop3.setAttribute('stop-color', b.color);
    stop3.setAttribute('stop-opacity', '0.2');
    grad.appendChild(stop1);
    grad.appendChild(stop2);
    grad.appendChild(stop3);
    defs.appendChild(grad);
  }});
  svg.appendChild(defs);
  // Create a group to hold all pan/zoom-able content
  const bubbleGroup = document.createElementNS(ns, 'g');
  bubbleGroup.setAttribute('id', 'bc-bubble-group');
  svg.appendChild(bubbleGroup);

  // Draw links with relationship labels
  const linkEls = [];
  const linkLabelEls = [];
  BC_LINKS.forEach((link) => {{
    const line = document.createElementNS(ns, 'line');
    line.setAttribute('x1', link.x1); line.setAttribute('y1', link.y1);
    line.setAttribute('x2', link.x2); line.setAttribute('y2', link.y2);
    line.setAttribute('class', 'bc-bubble-line' + (link.weight > 5 ? ' bc-bubble-line-thick' : ''));
    bubbleGroup.appendChild(line);
    linkEls.push({{el: line, link: link}});
    // Relationship label on line
    const mx = (link.x1 + link.x2) / 2; const my = (link.y1 + link.y2) / 2;
    const labelBg = document.createElementNS(ns, 'rect');
    labelBg.setAttribute('x', mx - 30); labelBg.setAttribute('y', my - 6);
    labelBg.setAttribute('width', 60); labelBg.setAttribute('height', 12);
    labelBg.setAttribute('fill', 'rgba(255,255,255,0.85)');
    labelBg.setAttribute('rx', 3);
    labelBg.style.pointerEvents = 'none';
    bubbleGroup.appendChild(labelBg);
    const t = document.createElementNS(ns, 'text');
    t.setAttribute('x', mx); t.setAttribute('y', my + 3); t.setAttribute('class', 'bc-edge-label');
    t.setAttribute('text-anchor', 'middle');
    // Shorten relation name for display
    const relLabel = (link.label || '').replace('conceptually_related_to', '关联').replace('cites', '引用').replace('references', '引用');
    t.textContent = relLabel;
    bubbleGroup.appendChild(t);
    linkLabelEls.push({{bgEl: labelBg, textEl: t, link: link}});
  }});
  // Draw 3D-style sphere bubbles (store refs for dragging)
  const bubbleEls = [];
  BC_BUBBLES.forEach((b, i) => {{
    // Shadow
    const shadow = document.createElementNS(ns, 'ellipse');
    shadow.setAttribute('cx', b.x + 2);
    shadow.setAttribute('cy', b.y + b.r * 0.15);
    shadow.setAttribute('rx', b.r * 0.9);
    shadow.setAttribute('ry', b.r * 0.3);
    shadow.setAttribute('fill', 'rgba(0,0,0,0.08)');
    shadow.style.pointerEvents = 'none';
    bubbleGroup.appendChild(shadow);
    // Main sphere with radial gradient
    const c = document.createElementNS(ns, 'circle');
    c.setAttribute('cx', b.x); c.setAttribute('cy', b.y); c.setAttribute('r', b.r);
    c.setAttribute('fill', 'url(#bc-grad-' + i + ')');
    c.setAttribute('stroke', b.color);
    c.setAttribute('stroke-width', 2);
    c.setAttribute('stroke-opacity', '0.6');
    c.setAttribute('class', 'bc-bubble-circle');
    c.dataset.bcId = b.id;
    c.style.cursor = 'grab';
    c.addEventListener('click', (e) => {{ e.stopPropagation(); showBcDetail(b.id); }});
    bubbleGroup.appendChild(c);
    // Specular highlight
    const gloss = document.createElementNS(ns, 'ellipse');
    gloss.setAttribute('cx', b.x - b.r * 0.3);
    gloss.setAttribute('cy', b.y - b.r * 0.4);
    gloss.setAttribute('rx', b.r * 0.3);
    gloss.setAttribute('ry', b.r * 0.2);
    gloss.setAttribute('fill', '#ffffff');
    gloss.setAttribute('opacity', '0.45');
    gloss.style.pointerEvents = 'none';
    bubbleGroup.appendChild(gloss);
    // Label
    const label = document.createElementNS(ns, 'text');
    label.setAttribute('x', b.x); label.setAttribute('y', b.y + 2);
    label.setAttribute('class', 'bc-bubble-label');
    label.textContent = b.name.length > 22 ? b.name.slice(0, 20) + '..' : b.name;
    bubbleGroup.appendChild(label);
    // Subdomain tag
    const subTag = document.createElementNS(ns, 'text');
    subTag.setAttribute('x', b.x); subTag.setAttribute('y', b.y + 14);
    subTag.setAttribute('class', 'bc-bubble-count');
    const sdMap = {{core: '核心域', supporting: '支撑域', generic: '通用域', unknown: ''}};
    subTag.textContent = sdMap[b.subdomain] || (b.size ? b.size + ' nodes' : '');
    bubbleGroup.appendChild(subTag);
    // Store refs for drag
    bubbleEls.push({{circle: c, shadow: shadow, gloss: gloss, label: label, subTag: subTag, data: b}});

    // Node drag handler
    c.addEventListener('mousedown', (e) => {{
      e.stopPropagation();
      e.preventDefault();
      c.style.cursor = 'grabbing';
      const startX = e.clientX, startY = e.clientY;
      const origX = b.x, origY = b.y;
      const onMove = (ev) => {{
        const dx = (ev.clientX - startX) / _bcScale;
        const dy = (ev.clientY - startY) / _bcScale;
        const newX = origX + dx, newY = origY + dy;
        // Update sphere elements
        c.setAttribute('cx', newX); c.setAttribute('cy', newY);
        shadow.setAttribute('cx', newX + 2); shadow.setAttribute('cy', newY + b.r * 0.15);
        gloss.setAttribute('cx', newX - b.r * 0.3); gloss.setAttribute('cy', newY - b.r * 0.4);
        label.setAttribute('x', newX); label.setAttribute('y', newY + 2);
        subTag.setAttribute('x', newX); subTag.setAttribute('y', newY + 14);
        // Update connected links
        linkEls.forEach((le) => {{
          const lk = le.link;
          let changed = false;
          if (lk.from === b.id) {{ lk.x1 = newX; lk.y1 = newY; changed = true; }}
          if (lk.to === b.id) {{ lk.x2 = newX; lk.y2 = newY; changed = true; }}
          if (changed) {{
            le.el.setAttribute('x1', lk.x1); le.el.setAttribute('y1', lk.y1);
            le.el.setAttribute('x2', lk.x2); le.el.setAttribute('y2', lk.y2);
          }}
        }});
        // Update link label positions
        linkLabelEls.forEach((lle) => {{
          const lk = lle.link;
          const mx = (lk.x1 + lk.x2) / 2; const my = (lk.y1 + lk.y2) / 2;
          lle.bgEl.setAttribute('x', mx - 30); lle.bgEl.setAttribute('y', my - 6);
          lle.textEl.setAttribute('x', mx); lle.textEl.setAttribute('y', my + 3);
        }});
        b.x = newX; b.y = newY;
      }};
      const onUp = () => {{
        c.style.cursor = 'grab';
        window.removeEventListener('mousemove', onMove);
        window.removeEventListener('mouseup', onUp);
      }};
      window.addEventListener('mousemove', onMove);
      window.addEventListener('mouseup', onUp);
    }});
  }});

  // == SVG Pan / Zoom ==
  let _bcScale = 1, _bcX = 0, _bcY = 0;
  let _bcDragging = false, _bcDragStart = null;
  function _bcUpdateTransform() {{
    bubbleGroup.setAttribute('transform',
      'translate(' + _bcX + ',' + _bcY + ') scale(' + _bcScale + ')');
  }}
  svg.addEventListener('wheel', (e) => {{
    e.preventDefault();
    const rect = svg.getBoundingClientRect();
    const mx = ((e.clientX - rect.left) / rect.width) * 360;
    const my = ((e.clientY - rect.top) / rect.height) * 340;
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    const newScale = Math.max(0.3, Math.min(4, _bcScale * delta));
    _bcX = mx - (mx - _bcX) * (newScale / _bcScale);
    _bcY = my - (my - _bcY) * (newScale / _bcScale);
    _bcScale = newScale;
    _bcUpdateTransform();
  }}, {{passive: false}});
  svg.addEventListener('mousedown', (e) => {{
    if (e.target.tagName === 'circle' && e.target.dataset.bcId) return;
    _bcDragging = true;
    _bcDragStart = {{x: e.clientX - _bcX, y: e.clientY - _bcY}};
    svg.style.cursor = 'grabbing';
  }});
  window.addEventListener('mousemove', (e) => {{
    if (!_bcDragging) return;
    _bcX = e.clientX - _bcDragStart.x;
    _bcY = e.clientY - _bcDragStart.y;
    _bcUpdateTransform();
  }});
  window.addEventListener('mouseup', () => {{
    if (_bcDragging) {{ _bcDragging = false; svg.style.cursor = 'grab'; }}
  }});
  svg.addEventListener('dblclick', (e) => {{
    e.preventDefault();
    _bcScale = 1; _bcX = 0; _bcY = 0;
    _bcUpdateTransform();
  }});

  function showBcDetail(bcId) {{
    const detail = BC_DETAILS.find(d => d.id === bcId || d.name === bcId);
    if (!detail) return;
    const panel = document.getElementById('bc-detail-panel');
    const hint = document.getElementById('bc-detail-hint');
    panel.style.display = 'block';
    hint.style.display = 'none';
    document.getElementById('bc-detail-name').textContent = detail.name;
    document.getElementById('bc-detail-name').style.color = detail.color;
    // Subdomain + description
    let statsText = '';
    const sdMap = {{core: '核心域', supporting: '支撑域', generic: '通用域', unknown: ''}};
    if (detail.subdomain && detail.subdomain !== 'unknown') statsText += sdMap[detail.subdomain] || '';
    if (detail.fileCount) statsText += (statsText ? ' · ' : '') + detail.fileCount + ' 个文件';
    document.getElementById('bc-detail-stats').textContent = statsText;

    // DDD tactical concepts grouped by type
    const conceptsDiv = document.getElementById('bc-detail-concepts');
    let cHtml = '';
    if (detail.desc) {{
      cHtml += '<div style="font-size:0.6875rem;color:var(--gf-text-secondary);line-height:1.5;margin-bottom:8px">' + esc(detail.desc.slice(0, 150)) + '</div>';
    }}
    // Group concepts by type
    const typeLabels = {{
      aggregate_root: '聚合根', domain_event: '领域事件', invariant: '不变式',
      value_object: '值对象', domain_service: '领域服务', contract: '契约',
      glossary_term: '统一语言', concept: '概念',
    }};
    const grouped = {{}};
    if (detail.concepts && detail.concepts.length) {{
      detail.concepts.forEach(c => {{
        const tl = typeLabels[c.type] || c.type || '概念';
        if (!grouped[tl]) grouped[tl] = [];
        grouped[tl].push(c.label);
      }});
    }}
    Object.keys(grouped).forEach(tl => {{
      cHtml += '<div style="font-size:0.6875rem;color:var(--gf-text-muted);text-transform:uppercase;letter-spacing:0.04em;font-weight:600;margin-bottom:4px">' + esc(tl) + '</div>';
      cHtml += '<div style="display:flex;flex-wrap:wrap;gap:3px;margin-bottom:8px">';
      grouped[tl].forEach(c => {{ cHtml += '<span class="detail-tag">' + esc(c) + '</span>'; }});
      cHtml += '</div>';
    }});
    // Related BCs
    if (detail.relatedBCs && detail.relatedBCs.length) {{
      cHtml += '<div style="font-size:0.6875rem;color:var(--gf-text-muted);text-transform:uppercase;letter-spacing:0.04em;font-weight:600;margin-bottom:4px">关联 BC</div>';
      detail.relatedBCs.forEach(r => {{
        const arrow = r.direction === 'out' ? '\u2192' : '\u2190';
        cHtml += '<div style="font-size:0.6875rem;color:var(--gf-text-secondary);padding:1px 0">' + arrow + ' ' + esc(r.label) + '</div>';
      }});
    }}
    conceptsDiv.innerHTML = cHtml;

    // Code files
    const filesDiv = document.getElementById('bc-detail-files');
    let filesHtml = '';
    if (detail.codeFiles && detail.codeFiles.length) {{
      filesHtml += '<div style="font-size:0.6875rem;color:var(--gf-text-muted);text-transform:uppercase;letter-spacing:0.04em;font-weight:600;margin:8px 0 4px">代码文件</div>';
      filesHtml += detail.codeFiles.map(f => '<div style="font-family:var(--gf-font-mono);font-size:0.6875rem;color:var(--gf-text-secondary);padding:1px 0">' + esc(f) + '</div>').join('');
    }}
    filesDiv.innerHTML = filesHtml;
    const jumpBtn = document.getElementById('bc-detail-jump');
    jumpBtn.onclick = () => {{
      const tab = document.querySelector('.mode-tab[data-tab="review"]');
      if (tab) tab.click();
    }};
  }}
}})();

// Nav button handlers
let _currentNodeId = null;
function _setCurrentNode(nodeId) {{ _currentNodeId = nodeId; }}
function navSourceFile() {{
  if (!_currentNodeId) {{
    // Edge selected: open the edge's own source file.
    if (_currentEdge && _currentEdge.source_file) {{
      window.open('../../' + _currentEdge.source_file, '_blank');
    }}
    return;
  }}
  const n = nodesDS.get(_currentNodeId);
  if (!n) return;
  const sf = n._source_file || (n._raw && n._raw.source_file) || '';
  if (sf) {{
    // Open source file relative to .graph/ parent
    window.open('../../' + sf, '_blank');
  }}
}}
function navPath() {{
  if (!_currentNodeId) return;
  const n = nodesDS.get(_currentNodeId);
  if (!n) return;
  // Find shortest path from this node to nearest god node
  const godIds = RAW_NODES.filter(rn => rn.degree > 10).map(rn => rn.id);
  if (!godIds.length) {{ alert('未找到高连接数节点'); return; }}
  let bestPath = null;
  for (const gid of godIds) {{
    if (gid === _currentNodeId) continue;
    try {{
      const path = network.getShortestPath(_currentNodeId, gid);
      if (path && path.length > 1 && (!bestPath || path.length < bestPath.length)) {{
        bestPath = path;
      }}
    }} catch(e) {{}}
  }}
  if (bestPath && bestPath.length > 1) {{
    network.selectNodes(bestPath);
    network.fit({{ nodes: bestPath, animation: true }});
    // Show path in detail
    const pathLabels = bestPath.map(id => {{
      const node = nodesDS.get(id);
      return node ? node.label : id;
    }});
    const detailBody = document.getElementById('detail-body');
    if (detailBody) {{
      detailBody.innerHTML = '<div class="detail-field" style="flex-direction:column;align-items:flex-start"><span class="detail-field-label" style="margin-bottom:4px">最短路径</span><span class="detail-field-value" style="font-family:var(--gf-font-mono);white-space:pre-wrap">' + esc(pathLabels.join(' -> ')) + '</span></div>';
    }}
  }} else {{
    alert('未找到路径');
  }}
}}
function navExplain() {{
  if (!_currentNodeId) return;
  const n = nodesDS.get(_currentNodeId);
  if (!n) return;
  // Show node info with all neighbors expanded
  const neighborIds = network.getConnectedNodes(_currentNodeId);
  const neighborInfo = neighborIds.map(nid => {{
    const nb = nodesDS.get(nid);
    const edges = network.getConnectedEdges(nid);
    return {{ id: nid, label: nb ? nb.label : nid, edgeCount: edges.length }};
  }}).sort((a, b) => b.edgeCount - a.edgeCount);
  const detailBody = document.getElementById('detail-body');
  if (detailBody) {{
    let html = '<div class="detail-field"><span class="detail-field-label">节点</span><span class="detail-field-value">' + esc(n.label) + '</span></div>';
    html += '<div class="detail-field"><span class="detail-field-label">连接数</span><span class="detail-field-value">' + n._degree + '</span></div>';
    html += '<div class="detail-field"><span class="detail-field-label">来源</span><span class="detail-field-value">' + esc(n._source_file || '-') + '</span></div>';
    if (neighborInfo.length) {{
      html += '<div class="detail-field" style="border-bottom:none;padding-top:8px"><span class="detail-field-label">相邻节点 (' + neighborInfo.length + ')</span></div>';
      neighborInfo.forEach(info => {{
        html += '<div class="detail-field"><span class="detail-field-label">' + esc(info.label) + '</span><span class="detail-field-value">' + info.edgeCount + ' 边</span></div>';
      }});
    }}
    detailBody.innerHTML = html;
  }}
}}

// == Sidebar/detail collapse toggles ==
function toggleSidebar(tab) {{
  const sidebar = document.getElementById(tab + '-sidebar');
  const rail = document.getElementById(tab + '-sidebar-rail');
  if (!sidebar || !rail) return;
  const collapsed = sidebar.classList.toggle('collapsed');
  rail.classList.toggle('visible', collapsed);
  setTimeout(() => network.redraw(), 200);
}}
function toggleDetail(tab) {{
  const panel = document.getElementById(tab === 'review' ? 'review-detail' : 'learn-detail-panel');
  const rail = document.getElementById(tab + '-detail-rail');
  if (!panel || !rail) return;
  const collapsed = panel.classList.toggle('collapsed');
  rail.classList.toggle('visible', collapsed);
  setTimeout(() => network.redraw(), 200);
}}

// == Learn tab v2: 多视角（业务流 / 代码架构 / 特性下钻）==
const learnShell = document.getElementById('learn-shell');
const LEARN_OK = !!(LEARN && (LEARN.version === 3 || LEARN.version === 2));

// Mermaid：CDN 失败（离线）时降级为源码展示。
window._gfMermaidOk = (typeof mermaid !== 'undefined');
if (window._gfMermaidOk) {{
  try {{
    mermaid.initialize({{
      startOnLoad: false, theme: 'base',
      themeVariables: {{
        background: '#e8ebf1', primaryColor: '#ffffff', primaryTextColor: '#1a1d2e',
        primaryBorderColor: '#4E79A7', lineColor: '#7a7f96', secondaryColor: '#f4f6fa',
        tertiaryColor: '#eef0f5', actorBkg: '#ffffff', actorBorder: '#4E79A7',
        actorTextColor: '#1a1d2e', actorLineColor: '#c4cbd8', signalColor: '#4a4e64',
        signalTextColor: '#4a4e64', noteBkgColor: 'rgba(78,121,167,0.08)',
        noteTextColor: '#1a1d2e', noteBorderColor: 'rgba(78,121,167,0.35)',
        altBkg: 'rgba(78,121,167,0.04)', activationBkgColor: '#dbe5f0',
        sequenceNumberColor: '#ffffff', clusterBkg: 'rgba(232,235,241,0.7)',
        clusterBorder: 'rgba(78,121,167,0.25)', edgeLabelBackground: '#ffffff',
        fontFamily: "'IBM Plex Sans', sans-serif", fontSize: '13px'
      }}
    }});
  }} catch (e) {{ window._gfMermaidOk = false; }}
}}

function learnMermaid(container, src) {{
  if (!container) return;
  if (window._gfMermaidOk) {{
    const pre = document.createElement('pre');
    pre.className = 'mermaid';
    pre.textContent = src;
    container.appendChild(pre);
    try {{ mermaid.run({{ nodes: [pre] }}); }} catch (e) {{ pre.className = 'mermaid-src'; }}
  }} else {{
    const pre = document.createElement('pre');
    pre.className = 'mermaid-src';
    pre.textContent = src;
    container.appendChild(pre);
  }}
}}

function learnAnchorChips(anchors) {{
  return (anchors || []).map(a => {{
    const file = String(a).split(' L')[0];
    return '<span class="anchor-chip" data-file="' + esc(file) + '" title="打开源文件">' + esc(a) + '</span>';
  }}).join('');
}}

// 锚点点击：data 属性 + 委托监听（同 neighbor-link 的 #1838 修复模式，
// 避免 inline onclick 的引号转义与注入面）。
document.addEventListener('click', e => {{
  const el = e.target.closest('.anchor-chip');
  if (el && el.dataset.file) window.open('../../' + el.dataset.file, '_blank');
}});

function learnBlockHtml(b) {{
  if (b.type === 'p') {{
    return '<p>' + esc(b.text) + '</p>';
  }}
  if (b.type === 'bullets') {{
    return '<ul>' + (b.items || []).map(it =>
      '<li>' + esc(it.text) + (it.anchor ? ' ' + learnAnchorChips([it.anchor]) : '') + '</li>'
    ).join('') + '</ul>';
  }}
  if (b.type === 'techpoints') {{
    return '<div class="tp-list">' + (b.items || []).map(it =>
      '<div class="tp-item"><div class="tp-name">' + esc(it.name) + '</div>' +
      '<div class="tp-why">' + esc(it.why) + '</div>' +
      (it.anchors && it.anchors.length ? '<div>' + learnAnchorChips(it.anchors) + '</div>' : '') +
      '</div>'
    ).join('') + '</div>';
  }}
  if (b.type === 'code') {{
    let lines = '';
    (b.lines || []).forEach(ln => {{
      const note = ln.note ? '<span class="note">  \u2190 ' + esc(ln.note) + '</span>' : '';
      lines += '<div class="cl' + (ln.focal ? ' focal' : '') + '"><span class="ln">' + ln.ln + '</span><span>' + esc(ln.text) + '</span>' + note + '</div>';
    }});
    return '<div class="code-block"><div class="cb-head"><span class="fn">' + esc(b.file) + '</span> \u00b7 L' + b.start + '-L' + b.end +
      (b.fn ? ' \u00b7 ' + esc(b.fn) + '()' : '') + '<span class="tier">' + esc(b.tier || '') + '</span></div><pre>' + lines + '</pre></div>';
  }}
  return '';
}}

let learnCur = {{ persp: 'graph', idx: 0 }};

function switchLearn(persp, idx) {{
  learnCur = {{ persp: persp, idx: idx || 0 }};
  document.querySelectorAll('.lview').forEach(v => v.classList.remove('active'));
  document.querySelectorAll('.persp-item').forEach(it => it.classList.remove('active'));
  document.querySelectorAll('.persp-group').forEach(g => g.classList.remove('open'));
  const grp = document.getElementById('pg-' + persp);
  if (grp) grp.classList.add('open');
  const items = document.querySelectorAll('.persp-item[data-persp="' + persp + '"]');
  if (items[idx]) items[idx].classList.add('active');
  else if (items.length) items[0].classList.add('active');
  const view = document.getElementById('lview-' + persp);
  if (view) {{
    view.classList.add('active');
    if (persp === 'project') renderLearnProject();
    if (persp === 'domain') renderLearnDomain(learnCur.idx);
    if (persp === 'flow') renderLearnFlow(learnCur.idx);
    if (persp === 'arch') renderLearnArch();
    if (persp === 'feature') renderLearnFeature(learnCur.idx);
  }}
}}
window.switchLearn = switchLearn;

// 视角跳转 / 大纲滚动：data 属性 + 委托监听（避免 inline onclick 的
// 引号转义问题，同 #1838 修复模式）。
document.addEventListener('click', e => {{
  const go = e.target.closest('[data-goto]');
  if (go) {{
    const parts = go.dataset.goto.split(':');
    switchLearn(parts[0], parseInt(parts[1], 10) || 0);
    return;
  }}
  const sc = e.target.closest('[data-scroll]');
  if (sc) {{
    const t = document.getElementById(sc.dataset.scroll);
    if (t) t.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
  }}
}});

function initLearn() {{
  if (!learnShell) return;
  if (!LEARN_OK) {{
    learnShell.innerHTML = '<div class="learn-guide">暂无学习内容。运行 <code>/graphify learn</code>（或 CLI <code>graphify learn</code>）生成多视角学习内容 —— 图谱 / 项目导览 / 业务领域 / 业务流 / 代码架构 / 特性下钻。纯结构化模式零 LLM 成本，加 <code>--backend</code> 可获得中文讲解。</div>';
    return;
  }}
  const isV3 = LEARN.version === 3;
  const flows = LEARN.flows || [];
  const feats = LEARN.features || [];
  const tour = isV3 ? (LEARN.tour || []) : [];
  const domains = isV3 ? (LEARN.domains || []) : [];
  const pov = isV3 ? (LEARN.project_overview || {{}}) : {{}};
  // 业务流视角
  // 业务领域视角
  let items1 = flows.map((f, i) =>
    '<button class="persp-item' + (i === 0 ? ' active' : '') + '" data-persp="flow" data-idx="' + i + '">' +
    esc(f.name) + '<span class="meta">' + esc(f.meta || '') + '</span></button>').join('');
  if (!items1) items1 = '<div style="padding:4px 24px;font-size:0.6875rem;color:var(--gf-text-faint)">未识别到业务流</div>';
  let items3 = feats.map((f, i) =>
    '<button class="persp-item" data-persp="feature" data-idx="' + i + '">' +
    esc(f.name) + '<span class="md-badge">MD</span></button>').join('');
  if (!items3) items3 = '<div style="padding:4px 24px;font-size:0.6875rem;color:var(--gf-text-faint)">暂无特性文档</div>';
  let domainItems = domains.map((d, i) =>
    '<button class="persp-item" data-persp="domain" data-idx="' + i + '">' +
    esc(d.name || d.id) + '<span class="meta">' + (d.node_count || 0) + ' 节点</span></button>').join('');
  if (!domainItems) domainItems = '<div style="padding:4px 24px;font-size:0.6875rem;color:var(--gf-text-faint)">' + (isV3 ? '未识别到领域' : 'v2 不支持') + '</div>';
  learnShell.innerHTML =
    '<aside class="persp-nav">' +
      '<div class="persp-group open" id="pg-project"><div class="persp-head"><span class="chev">\u25b6</span><div><div class="persp-title">项目导览</div><div class="persp-sub">目录 \u00b7 入口 \u00b7 技术栈 \u00b7 导览步骤</div></div></div><div class="persp-items"><button class="persp-item active" data-persp="project" data-idx="0">项目概览</button></div></div>' +
      '<div class="persp-group" id="pg-domain"><div class="persp-head"><span class="chev">\u25b6</span><div><div class="persp-title">业务领域</div><div class="persp-sub">领域边界 \u00b7 跨域关系</div></div></div><div class="persp-items">' + domainItems + '</div></div>' +
      '<div class="persp-group" id="pg-flow"><div class="persp-head"><span class="chev">\u25b6</span><div><div class="persp-title">业务流视角</div><div class="persp-sub">从请求到响应的调用路径</div></div></div><div class="persp-items">' + items1 + '</div></div>' +
      '<div class="persp-group" id="pg-arch"><div class="persp-head"><span class="chev">\u25b6</span><div><div class="persp-title">代码架构视角</div><div class="persp-sub">目录 \u00b7 关键特性 \u00b7 基础类图</div></div></div><div class="persp-items"><button class="persp-item" data-persp="arch" data-idx="0">系统总览</button></div></div>' +
      '<div class="persp-group" id="pg-feature"><div class="persp-head"><span class="chev">\u25b6</span><div><div class="persp-title">特性下钻</div><div class="persp-sub">逐特性的深度分析文档（MD）</div></div></div><div class="persp-items">' + items3 + '</div></div>' +
      '<div class="learn-footer"><span>' + tour.length + ' 步导览 \u00b7 ' + flows.length + ' 流 \u00b7 ' + feats.length + ' 文档</span></div>' +
    '</aside>' +
    '<main class="lview active" id="lview-project"></main>' +
    '<main class="lview" id="lview-domain"></main>' +
    '<main class="lview" id="lview-flow"></main>' +
    '<main class="lview" id="lview-arch"></main>' +
    '<main class="lview" id="lview-feature"></main>';
  learnShell.querySelectorAll('.persp-head').forEach(h => {{
    h.addEventListener('click', () => {{
      const grp = h.parentElement;
      const p = grp.id.replace('pg-', '');
      if (p) switchLearn(p, 0);
    }});
  }});
  learnShell.querySelectorAll('.persp-item').forEach(it => {{
    it.addEventListener('click', () => switchLearn(it.dataset.persp, parseInt(it.dataset.idx, 10) || 0));
  }});
  // 图谱视图切换按钮（右上角）
  const learnPage = document.getElementById('page-learn');
  if (learnPage && !document.getElementById('learn-graph-btn')) {{
    const btn = document.createElement('button');
    btn.id = 'learn-graph-btn';
    btn.className = 'learn-graph-toggle';
    btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><circle cx="12" cy="12" r="2"/><circle cx="5" cy="5" r="2"/><circle cx="19" cy="5" r="2"/><circle cx="5" cy="19" r="2"/><circle cx="19" cy="19" r="2"/><line x1="12" y1="12" x2="5" y2="5"/><line x1="12" y1="12" x2="19" y2="5"/><line x1="12" y1="12" x2="5" y2="19"/><line x1="12" y1="12" x2="19" y2="19"/></svg>图谱视图';
    btn.addEventListener('click', toggleLearnGraph);
    learnPage.appendChild(btn);
  }}
  // 图谱视图覆盖层
  if (learnPage && !document.getElementById('learn-graph-overlay')) {{
    const overlay = document.createElement('div');
    overlay.id = 'learn-graph-overlay';
    overlay.className = 'learn-graph-overlay';
    overlay.style.display = 'none';
    overlay.innerHTML =
      '<div class="lgo-header">' +
        '<span class="lgo-title">代码图谱</span>' +
        '<input type="text" class="lgo-search" id="lgo-search" placeholder="搜索节点..." autocomplete="off">' +
        '<button class="lgo-close" id="lgo-close">\u2715 关闭</button>' +
      '</div>' +
      '<div class="lgo-body">' +
        '<div class="lgo-canvas" id="lgo-canvas"></div>' +
        '<aside class="lgo-detail" id="lgo-detail"><div class="lgo-detail-hint">点击节点查看详情</div></aside>' +
      '</div>';
    learnPage.appendChild(overlay);
    document.getElementById('lgo-close').addEventListener('click', toggleLearnGraph);
  }}
  renderLearnProject();
}}

function renderLearnFlow(idx) {{
  const f = (LEARN.flows || [])[idx];
  const el = document.getElementById('lview-flow');
  if (!f || !el) return;
  const chips = (f.participants || []).map(p => '<span class="member-chip">' + esc(p) + '</span>').join('');
  el.innerHTML =
    '<div class="stage">' +
      '<div class="stage-crumb">' + esc(document.title || 'project') + ' / <span class="here">' + esc(f.name) + '</span></div>' +
      '<div class="stage-scroll">' +
        '<div class="stage-title-row"><h1>' + esc(f.name) + '</h1><div style="display:flex;gap:4px;flex-wrap:wrap">' + chips + '</div></div>' +
        '<div class="diagram-frame" id="lf-diagram"></div>' +
      '</div>' +
      '<div class="step-timeline">' +
        '<div class="step-tl-head"><span class="learn-lbl" style="margin:0">分步讲解</span>' +
        '<div class="step-tl-nav"><button class="step-btn" id="lf-prev">\u2190</button><span class="pos" id="lf-pos"></span><button class="step-btn" id="lf-next">\u2192</button></div></div>' +
        '<div class="step-track" id="lf-track"></div>' +
        '<div class="step-card"><div class="step-idx" id="lf-idx"></div><div><div class="step-msg" id="lf-msg"></div><div class="step-desc" id="lf-desc"></div><div class="step-cite" id="lf-cite"></div></div></div>' +
      '</div>' +
    '</div>' +
    '<aside class="ctx-panel">' +
      '<div class="ctx-head"><span class="learn-lbl">主符号上下文</span><div class="ctx-name">' + esc(f.context ? f.context.node : '') + '</div></div>' +
      '<div class="ctx-body">' +
        '<div class="ctx-intent">' + esc(f.context ? f.context.intent : '') + '</div>' +
        '<div class="ctx-div"></div>' +
        '<span class="learn-lbl">代码锚点</span><div>' + learnAnchorChips(f.context && f.context.anchors) + '</div>' +
        '<div class="ctx-div"></div>' +
        '<span class="learn-lbl">深入</span>' +
        '<button class="rf-item" data-goto="feature:' + Math.max(0, (LEARN.features || []).findIndex(x => x.flow_id === f.id)) + '">' + esc(f.name) + ' \u00b7 特性下钻文档<span class="go">\u2192</span></button>' +
      '</div>' +
    '</aside>';
  learnMermaid(document.getElementById('lf-diagram'), f.mermaid || '');
  // 分步讲解 — 过滤末尾纯导航项（无 msg/desc 的伪步骤）
  const steps = (f.steps || []).filter(s => s && (s.msg || s.desc));
  let cur = 0;
  const track = document.getElementById('lf-track');
  steps.forEach((_, i) => {{
    const seg = document.createElement('span');
    seg.className = 'step-seg';
    seg.addEventListener('click', () => {{ cur = i; render(); }});
    track.appendChild(seg);
  }});
  function render() {{
    const s = steps[cur] || {{}};
    document.getElementById('lf-idx').textContent = String(cur + 1).padStart(2, '0');
    document.getElementById('lf-msg').innerHTML = esc(s.msg || '').replace(/(\u2192|\u2190)/g, '<span class="ar">$1</span>');
    document.getElementById('lf-desc').textContent = s.desc || '';
    document.getElementById('lf-cite').textContent = s.cite || '';
    document.getElementById('lf-pos').textContent = (cur + 1) + ' / ' + steps.length;
    document.getElementById('lf-prev').disabled = cur === 0;
    document.getElementById('lf-next').disabled = cur >= steps.length - 1;
    track.querySelectorAll('.step-seg').forEach((seg, i) => {{
      seg.className = 'step-seg' + (i < cur ? ' done' : i === cur ? ' current' : '');
    }});
  }}
  document.getElementById('lf-prev').addEventListener('click', () => {{ if (cur > 0) {{ cur--; render(); }} }});
  document.getElementById('lf-next').addEventListener('click', () => {{ if (cur < steps.length - 1) {{ cur++; render(); }} }});
  if (steps.length) render();
}}

function renderLearnArch() {{
  const a = LEARN.architecture || {{}};
  const el = document.getElementById('lview-arch');
  if (!el) return;
  const rows = (a.tree || []).map(r =>
    '<div class="row' + (r.kind === 'dir' ? ' dir-row' : '') + '"><span class="' + (r.kind === 'dir' ? 'dir' : '') + '">' + esc(r.label) + '</span>' +
    (r.note ? '<span class="ncnt">' + esc(r.note) + '</span>' : '') + '</div>').join('');
  const cards = (a.features || []).map((c, i) =>
    '<div class="feat-card" data-goto="feature:' + i + '">' +
    '<div class="feat-name">' + esc(c.name) + '<span class="go">下钻 \u2192</span></div>' +
    '<div class="feat-desc">' + esc(c.desc || '') + '</div>' +
    '<div class="feat-meta">' + esc(c.modules || '') + '</div></div>').join('');
  const hasClass = !!(a.class_diagram);
  el.innerHTML =
    '<div class="arch-center">' +
      '<div class="arch-card"><h3>目录结构 <span class="cnt">' + (a.tree || []).length + ' 行</span><span class="arch-tree-toggle" id="la-tree-toggle">\u5c55\u5f00</span></h3><div class="dir-tree collapsed" id="la-tree">' + rows + '</div></div>' +
      '<div class="arch-card"><h3>关键特性 <span class="cnt">点击进入特性下钻</span></h3><div class="feat-grid">' + (cards || '<div style="font-size:0.6875rem;color:var(--gf-text-faint)">暂无</div>') + '</div></div>' +
    '</div>' +
    (hasClass ?
      '<aside class="arch-right"><div class="panel-head"><span class="learn-lbl" style="margin:0">\u57fa\u7840\u7c7b\u56fe\uff08AST \u63d0\u53d6\uff0c\u4ec5\u4f9b\u53c2\u8003\uff09</span><div style="font-size:0.625rem;color:var(--gf-text-muted);margin-top:2px">\u9886\u57df\u7ed3\u6784\u5c42 \u00b7 \u7279\u6027\u884c\u4e3a\u89c1\u4e0b\u94bb\u6587\u6863</div></div><div class="diagram-scroll" id="la-diagram"></div><div class="cap">\u6765\u6e90\uff1aAST \u7c7b/\u65b9\u6cd5\u63d0\u53d6 \u00b7 contains + calls \u8fb9</div></aside>'
      : '');
  if (hasClass) learnMermaid(document.getElementById('la-diagram'), a.class_diagram);
  // 目录树展开/折叠
  const archTreeToggle = document.getElementById('la-tree-toggle');
  const archTreeEl = document.getElementById('la-tree');
  if (archTreeToggle && archTreeEl) {{
    archTreeToggle.addEventListener('click', () => {{
      const collapsed = archTreeEl.classList.toggle('collapsed');
      archTreeToggle.textContent = collapsed ? '\u5c55\u5f00' : '\u6298\u53e0';
    }});
  }}
}}

function renderLearnFeature(idx) {{
  const f = (LEARN.features || [])[idx];
  const el = document.getElementById('lview-feature');
  if (!f || !el) return;
  const secs = (f.sections || []).map(s => {{
    let blocks = '';
    (s.blocks || []).forEach(b => {{
      if (b.type === 'mermaid') {{
        blocks += '<div class="mermaid-holder" data-src="' + encodeURIComponent(b.src) + '"></div>';
      }} else {{
        blocks += learnBlockHtml(b);
      }}
    }});
    let secTitle = esc(s.title);
    if (s.title && (s.title.indexOf('\u6027\u80fd') >= 0 || s.title.indexOf('\u53ef\u9760') >= 0)) {{
      secTitle += '<span style="font-size:0.5625rem;color:var(--gf-text-faint);font-weight:400">\uff08\u542f\u53d1\u5f0f\u5206\u6790\uff09</span>';
    }}
    return '<h2 id="fsec-' + s.no + '"><span class="no">' + esc(s.no) + '</span>' + secTitle + '</h2>' + blocks;
  }}).join('');
  const outline = (f.outline || []).map(o =>
    '<button class="rail-item" data-scroll="fsec-' + o.no + '"><span class="no">' + esc(o.no) + '</span>' + esc(o.title) + '</button>').join('');
  el.innerHTML =
    '<div class="doc-scroll"><div class="doc doc-wrap" id="lf-doc">' +
      '<div class="doc-header"><h1>' + esc(f.name) + '</h1>' +
      (function() {{
        const diff = f.difficulty;
        if (!diff) return '';
        const labels = {{simple: '\u7b80\u5355', standard: '\u6807\u51c6', complex: '\u590d\u6742'}};
        return '<span class="difficulty-badge difficulty-' + esc(diff) + '">' + (labels[diff] || esc(diff)) + '</span>';
      }}()) +
      '<div class="md-toggle"><button class="active" id="lf-render">渲染</button><button id="lf-src">MD 源码</button></div></div>' +
      '<div class="doc-meta"><span class="accent-pill">特性下钻</span><span class="accent-pill">' + (f.outline || []).length + ' 节</span>' +
      '<span class="accent-pill">' + (f.backend || LEARN.backend || '结构化') + '</span></div>' +
      '<div class="doc-render">' + secs + '</div>' +
      '<pre class="md-src">' + esc(f.doc_md || '') + '</pre>' +
    '</div></div>' +
    '<aside class="doc-rail">' +
      '<span class="learn-lbl">文档大纲</span>' + outline +
      '<div class="ctx-div"></div>' +
      '<span class="learn-lbl">代码锚点（' + (f.anchors || []).length + '）</span><div>' + learnAnchorChips(f.anchors) + '</div>' +
      '<div class="ctx-div"></div>' +
      '<span class="learn-lbl">关联视角</span>' +
      '<button class="rf-item" data-goto="flow:0">业务流视角<span class="go">\u2192</span></button>' +
      '<button class="rf-item" data-goto="arch:0">基础类图 \u00b7 架构视角<span class="go">\u2192</span></button>' +
    '</aside>';
  // mermaid 块懒渲染（视图已激活，容器可见，测量正确）。
  el.querySelectorAll('.mermaid-holder').forEach(h => {{
    learnMermaid(h, decodeURIComponent(h.dataset.src));
  }});
  const wrap = document.getElementById('lf-doc');
  document.getElementById('lf-render').addEventListener('click', () => {{
    wrap.classList.remove('show-src');
    document.getElementById('lf-render').classList.add('active');
    document.getElementById('lf-src').classList.remove('active');
  }});
  document.getElementById('lf-src').addEventListener('click', () => {{
    wrap.classList.add('show-src');
    document.getElementById('lf-src').classList.add('active');
    document.getElementById('lf-render').classList.remove('active');
  }});
}}

// == 图谱视角：复用审核页 vis.js network ==
// == 图谱视图覆盖层：独立的 vis.Network 实例 + 精简详情面板 ==
function toggleLearnGraph() {{
  const overlay = document.getElementById('learn-graph-overlay');
  if (!overlay) return;
  const isVisible = overlay.style.display !== 'none';
  if (isVisible) {{
    overlay.style.display = 'none';
    if (window._learnNetwork) {{
      try {{ window._learnNetwork.destroy(); }} catch (e) {{}}
      window._learnNetwork = null;
    }}
    return;
  }}
  overlay.style.display = 'flex';
  // 延迟创建，等容器可见后 vis.Network 才能正确测量尺寸
  setTimeout(initLearnGraph, 50);
}}

function initLearnGraph() {{
  const container = document.getElementById('lgo-canvas');
  if (!container || window._learnNetwork) return;
  if (typeof vis === 'undefined' || !RAW_NODES || !RAW_NODES.length) {{
    container.innerHTML = '<div style="padding:40px;text-align:center;color:var(--gf-text-muted)">图谱数据不可用。</div>';
    return;
  }}
  const learnNodes = new vis.DataSet(RAW_NODES.map(n => ({{
    id: n.id, label: n.label, color: n.color, size: n.size,
    font: n.font, title: n.title, community: n.community,
    source_file: n.source_file, file_type: n.file_type, desc: n.desc,
    degree: n.degree, node_kind: n.node_kind,
  }})));
  const learnEdges = new vis.DataSet(RAW_EDGES.map(e => ({{
    from: e.from, to: e.to, label: e.label, dashes: e.dashes,
    width: e.width, color: e.color, title: e.title,
  }})));
  window._learnNetwork = new vis.Network(container, {{ nodes: learnNodes, edges: learnEdges }}, {{
    physics: {{ enabled: true, solver: 'forceAtlas2Based',
      forceAtlas2Based: {{ gravitationalConstant: -30, springLength: 80, springConstant: 0.08, damping: 0.4 }},
      stabilization: {{ iterations: 80 }}
    }},
    interaction: {{ hover: true, tooltipDelay: 200, navigationButtons: false }},
    nodes: {{ shape: 'dot', scaling: {{ min: 8, max: 30 }} }},
  }});
  window._learnNetwork.on('click', (params) => {{
    if (params.nodes.length > 0) {{
      showLearnNodeDetail(params.nodes[0]);
    }}
  }});
  // 搜索框
  const searchInput = document.getElementById('lgo-search');
  if (searchInput) {{
    searchInput.addEventListener('input', () => {{
      const q = searchInput.value.toLowerCase().trim();
      if (!q) return;
      const match = RAW_NODES.find(n => (n.label || '').toLowerCase().includes(q));
      if (match) {{
        window._learnNetwork.focus(match.id, {{ scale: 1.3, animation: {{ duration: 500 }} }});
        window._learnNetwork.selectNodes([match.id]);
        showLearnNodeDetail(match.id);
      }}
    }});
  }}
}}

function showLearnNodeDetail(nid) {{
  const node = RAW_NODES.find(n => n.id === nid);
  if (!node) return;
  const detail = document.getElementById('lgo-detail');
  if (!detail) return;
  const notes = (LEARN && LEARN.node_notes && LEARN.node_notes.notes) || {{}};
  const note = notes[nid] || '';
  detail.innerHTML =
    '<div class="lgo-detail-header">' + esc(node.label || nid) + '</div>' +
    (node.file_type ? '<div class="lgo-detail-row"><span class="lgo-label">类型</span><span>' + esc(node.file_type) + '</span></div>' : '') +
    (node.source_file ? '<div class="lgo-detail-row"><span class="lgo-label">文件</span><span style="font-family:var(--gf-font-mono);font-size:0.625rem">' + esc(node.source_file) + '</span></div>' : '') +
    (node.desc ? '<div class="lgo-detail-row"><span class="lgo-label">描述</span><span>' + esc(node.desc) + '</span></div>' : '') +
    (node.degree !== undefined ? '<div class="lgo-detail-row"><span class="lgo-label">度数</span><span>' + node.degree + '</span></div>' : '') +
    (note ? '<div class="lgo-detail-row lgo-note"><span class="lgo-label">教学注解</span><span>' + esc(note) + '</span></div>' : '');
}}

// == 项目导览视角：project_overview + tour ==
function renderLearnProject() {{
  const el = document.getElementById('lview-project');
  if (!el) return;
  const isV3 = LEARN.version === 3;
  if (!isV3) {{
    el.innerHTML = '<div class="learn-guide">v2 学习内容不支持项目导览视角。请运行 <code>/graphify learn</code> 重新生成 v3 学习内容。</div>';
    return;
  }}
  const pov = LEARN.project_overview || {{}};
  const tour = LEARN.tour || [];
  // 目录结构
  const treeRows = (pov.dir_structure || []).map(r =>
    '<div class="row' + (r.kind === 'dir' ? ' dir-row' : '') + '"><span class="' + (r.kind === 'dir' ? 'dir' : '') + '">' + esc(r.label) + '</span>' +
    (r.note ? '<span class="ncnt">' + esc(r.note) + '</span>' : '') + '</div>').join('');
  // 入口点
  const epItems = (pov.entry_points || []).map(ep =>
    '<div class="entry-point-item" data-file="' + esc((ep.path || '').split(' L')[0]) + '">' +
    '<span class="ep-type">' + esc(ep.type || '') + '</span>' +
    '<span class="ep-handler">' + esc(ep.handler || '') + '</span>' +
    '<span class="ep-path">' + esc(ep.path || '') + '</span>' +
    '</div>').join('');
  // 技术栈
  const tsPills = (pov.tech_stack || []).map(t => '<span class="tech-stack-pill">' + esc(t) + '</span>').join('');
  // tour 进度
  const tourProgress = tour.length ? Math.round(tour.length * 100 / Math.max(tour.length, 1)) : 0;
  const tourSteps = tour.map(s =>
    '<div class="tour-step" data-cid="' + esc(s.community_id !== undefined ? String(s.community_id) : '') + '">' +
    '<div class="ts-idx">' + esc(String(s.order || '')) + '</div>' +
    '<div style="flex:1"><div class="ts-title">' + esc(s.title || '') + '</div>' +
    '<div class="ts-desc">' + esc(s.desc || '') + '</div>' +
    '<div class="ts-nodes">' + (s.nodeIds || []).slice(0, 8).map(nid =>
      '<span class="ts-node" data-nid="' + esc(String(nid)) + '">' + esc(String(nid).slice(0, 24)) + '</span>'
    ).join('') + '</div></div></div>'
  ).join('');
  el.innerHTML =
    '<div class="arch-center">' +
      '<div class="arch-card"><h3>功能介绍</h3><p style="font-size:0.8125rem;line-height:1.7;color:var(--gf-text-secondary)">' + esc(pov.feature_intro || LEARN.project_summary || '') + '</p></div>' +
      (treeRows ? '<div class="arch-card"><h3>目录结构 <span class="cnt">' + (pov.dir_structure || []).length + ' 行</span></h3><div class="dir-tree collapsed" id="lp-tree">' + treeRows + '</div>' +
        '<button class="arch-tree-toggle" id="lp-tree-toggle">展开</button></div>' : '') +
      (epItems ? '<div class="arch-card"><h3>核心入口点 <span class="cnt">' + (pov.entry_points || []).length + ' 个</span></h3>' + epItems + '</div>' : '') +
      (tsPills ? '<div class="arch-card"><h3>技术栈</h3><div style="display:flex;flex-wrap:wrap">' + tsPills + '</div></div>' : '') +
      (tourSteps ? '<div class="arch-card"><h3>导览步骤 <span class="cnt">' + tour.length + ' 步</span></h3>' +
        '<div class="tour-progress-bar"><div class="tour-progress-fill" style="width:100%"></div></div>' + tourSteps + '</div>' : '') +
    '</div>';
  // 目录树展开/折叠
  const treeToggle = document.getElementById('lp-tree-toggle');
  const treeEl = document.getElementById('lp-tree');
  if (treeToggle && treeEl) {{
    treeToggle.addEventListener('click', () => {{
      const collapsed = treeEl.classList.toggle('collapsed');
      treeToggle.textContent = collapsed ? '展开' : '折叠';
    }});
  }}
  // 入口点点击 → 打开源文件
  el.querySelectorAll('.entry-point-item').forEach(item => {{
    item.addEventListener('click', () => {{
      const f = item.dataset.file;
      if (f) window.open('../../' + f, '_blank');
    }});
  }});
  // tour 步骤节点点击 → 图谱聚焦
  el.querySelectorAll('.ts-node').forEach(node => {{
    node.addEventListener('click', () => {{
      const nid = node.dataset.nid;
      moveToTab('review');
      setTimeout(() => {{
        try {{ network.focus(nid, {{ scale: 1.3, animation: {{ duration: 500 }} }}); network.selectNodes([nid]); }} catch (e) {{}}
        showInfo(nid);
      }}, 120);
    }});
  }});
}}

// == 业务领域视角：domains + cross-domain mermaid ==
function renderLearnDomain(idx) {{
  const el = document.getElementById('lview-domain');
  if (!el) return;
  const isV3 = LEARN.version === 3;
  if (!isV3) {{
    el.innerHTML = '<div class="learn-guide">v2 学习内容不支持业务领域视角。请运行 <code>/graphify learn</code> 重新生成 v3 学习内容。</div>';
    return;
  }}
  const domains = LEARN.domains || [];
  if (!domains.length) {{
    el.innerHTML = '<div class="learn-guide">未识别到业务领域。</div>';
    return;
  }}
  const d = domains[idx] || domains[0];
  // cross-domain mermaid: graph LR
  let mermaidSrc = 'graph LR\\n';
  const myId = d.id || ('domain_' + idx);
  domains.forEach((dom, i) => {{
    if (i === idx) return;
    const did = dom.id || ('domain_' + i);
    mermaidSrc += '  ' + did + '["' + (dom.name || did).replace(/"/g, "'") + '"]\\n';
  }});
  (d.cross_domain || []).forEach((cd, ci) => {{
    mermaidSrc += '  ' + myId + ' --> ' + esc(cd.target || '') + '\\n';
    mermaidSrc += '  linkStyle ' + ci + ' stroke:#4E79A7\\n';
  }});
  if (!d.cross_domain || !d.cross_domain.length) {{
    mermaidSrc += '  ' + myId + '["' + (d.name || myId).replace(/"/g, "'") + '"]\\n';
  }}
  // key_files / key_symbols
  const fileChips = (d.key_files || []).map(f =>
    '<span class="dom-file" data-file="' + esc(f) + '">' + esc(f) + '</span>').join('');
  const symChips = (d.key_symbols || []).map(s =>
    '<span class="dom-sym" data-sym="' + esc(s) + '">' + esc(s) + '</span>').join('');
  // cross_domain list
  const cdList = (d.cross_domain || []).map(cd =>
    '<div style="display:flex;align-items:center;gap:8px;padding:4px 0;font-size:0.6875rem;color:var(--gf-text-secondary)">' +
    '<span style="font-family:var(--gf-font-mono);font-size:0.5625rem;color:var(--gf-text-faint)">' + esc(cd.via || '') + '</span>' +
    '<span>\u2192 ' + esc(cd.target || '') + '</span>' +
    '<span style="margin-left:auto;font-family:var(--gf-font-mono);font-size:0.5625rem;color:var(--gf-text-faint)">' + (cd.count || 0) + ' 边</span>' +
    '</div>').join('');
  el.innerHTML =
    '<div class="arch-center">' +
      '<div class="domain-card">' +
        '<h3>' + esc(d.name || d.id) + '<span class="dom-meta">' + (d.node_count || 0) + ' 节点 \u00b7 ' + esc(d.source || '') + '</span></h3>' +
        (d.desc ? '<div class="dom-desc">' + esc(d.desc) + '</div>' : '') +
        (fileChips ? '<div class="dom-section"><span class="learn-lbl">关键文件</span><div class="dom-files">' + fileChips + '</div></div>' : '') +
        (symChips ? '<div class="dom-section"><span class="learn-lbl">关键符号</span><div class="dom-symbols">' + symChips + '</div></div>' : '') +
        (cdList ? '<div class="dom-section"><span class="learn-lbl">跨域关系</span>' + cdList + '</div>' : '') +
      '</div>' +
      '<div class="arch-card"><h3>领域关系图</h3><div class="diagram-frame" id="ld-diagram"></div></div>' +
    '</div>';
  learnMermaid(document.getElementById('ld-diagram'), mermaidSrc);
  // key_file / key_symbol 点击 → 图谱聚焦
  el.querySelectorAll('.dom-file, .dom-sym').forEach(chip => {{
    chip.addEventListener('click', () => {{
      const label = chip.dataset.file || chip.dataset.sym || '';
      const found = RAW_NODES.find(n => n.label === label || n.id === label);
      if (found) {{
        moveToTab('review');
        setTimeout(() => {{
          try {{ network.focus(found.id, {{ scale: 1.3, animation: {{ duration: 500 }} }}); network.selectNodes([found.id]); }} catch (e) {{}}
          showInfo(found.id);
        }}, 120);
      }}
    }});
  }});
}}

// == Initialize ==
renderFilterChips();
renderNodeList();
updateStats();
initLearn();
</script>"""


def _html_document_title(output_path: str) -> str:
    """Return the project name for the graph.html <title>.

    The label reflects the working directory / project name (typically a
    microservice name), NOT the tool name "graphify" and NOT the raw ".graph"
    output-dir name. Tracked artifacts must not embed the generator host
    absolute path (regression of #433; reported again as #2598 on Windows).
    """
    from graphify.paths import GRAPHIFY_OUT_NAME

    raw = str(output_path).replace("\\", "/")
    # Drop Windows drive prefix so Path parts are comparable on any OS.
    if len(raw) >= 3 and raw[1] == ":" and raw[0].isalpha() and raw[2] == "/":
        raw = raw[2:]  # "/Users/..." style after drive strip

    parts = list(Path(raw).parts)
    # Path("C:/Users/..") on POSIX may keep "C:" as first part — strip it.
    if parts and len(parts[0]) == 2 and parts[0][1] == ":" and parts[0][0].isalpha():
        parts = parts[1:]
    # Prefer the project name = the parent directory of the output dir.
    # E.g. "/path/to/myproject/.graph/graph.html" -> "myproject".
    # This avoids leaking host paths and avoids the ".graph" name itself.
    marker = GRAPHIFY_OUT_NAME
    for i, part in enumerate(parts):
        if (part == marker or part.startswith(".graph")) and i > 0:
            return parts[i - 1]

    # No standard out-dir marker (or marker is the first segment with no
    # parent): fall back to the cwd basename — the working directory name.
    try:
        cwd_name = Path.cwd().name
        if cwd_name:
            return cwd_name
    except (ValueError, OSError, RuntimeError):
        pass

    return "graph.html"

def to_html(
    G: nx.Graph,
    communities: dict[int, list[str]],
    output_path: str,
    community_labels: dict[int, str] | None = None,
    member_counts: dict[int, int] | None = None,
    node_limit: int | None = None,
    learning_overlay: dict | None = None,
    review_queue: list[dict] | None = None,
    learn_data: dict | None = None,
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

    If learn_data is provided (or a learn.json sidecar exists next to the
    output), the third tab (学习) is populated with human-oriented learning
    content: a dependency-ordered guided tour and per-node learning cards
    (intent / contract / key-algorithm implementation with focal lines).
    Empty/missing data keeps the tab's guidance placeholder.

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
    # Learn sidecar (human-comprehension content for the third tab). Same
    # best-effort pattern: absent/empty sidecar => no LEARN constant payload,
    # so the un-annotated render stays byte-identical to pre-feature.
    if learn_data is None:
        learn_data = {}
        try:
            from graphify.learn import load_learn_sidecar as _lls
            learn_data = _lls(Path(output_path))
        except Exception:
            learn_data = {}
    # Status -> ring color. preferred=green, contested=amber. Tentative gets no
    # ring (it's not yet trustworthy enough to highlight in the map).
    _RING = {"preferred": "#22c55e", "contested": "#f59e0b"}

    # Reasons sidecar (audit provenance): extraction-time `reason` /
    # `evidence_quote` edge attrs win when present (fresh build in memory);
    # the .graph/temp/reasons.json sidecar fills the gap when G was reloaded
    # from an already-stripped graph.json (e.g. `graphify export html`). Same
    # best-effort pattern as the learning overlay above.
    _reasons_map: dict = {}
    try:
        _rp = Path(output_path).parent / "temp" / "reasons.json"
        if _rp.exists():
            _loaded = json.loads(_rp.read_text(encoding="utf-8"))
            if isinstance(_loaded, dict) and isinstance(_loaded.get("edges"), dict):
                _reasons_map = _loaded["edges"]
    except Exception:
        _reasons_map = {}

    def _edge_reasons(u: str, v: str, data: dict) -> tuple:
        """(reason, evidence_quote) for an edge, attrs first, sidecar fallback."""
        r = data.get("reason")
        q = data.get("evidence_quote")
        if r is None and q is None:
            ent = _reasons_map.get(
                f"{data.get('_src', u)}|{data.get('_tgt', v)}|{data.get('relation', '')}"
            )
            if isinstance(ent, dict):
                r = ent.get("reason")
                q = ent.get("evidence_quote")
        return (
            sanitize_label(r) if r else "",
            sanitize_label(q) if q else "",
        )

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
            "tags": (data.get("tags") or []),
            "node_kind": data.get("node_kind", ""),
            "degree": deg,
            # Concept/doc descriptions power the detail panel's 描述 row.
            "desc": sanitize_label(str(data.get("desc") or "")),
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
        confidence_score = float(data.get("confidence_score", 1.0 if confidence == "EXTRACTED" else 0.55))
        relation = data.get("relation", "")
        true_src = data.get("_src", u)
        true_tgt = data.get("_tgt", v)
        _reason_txt, _quote_txt = _edge_reasons(u, v, data)
        vis_edges.append({
            "from": true_src,
            "to": true_tgt,
            "label": relation,
            "title": _html.escape(f"{relation} [{confidence} {confidence_score:.2f}]"),
            "dashes": confidence != "EXTRACTED",
            "width": 2 if confidence == "EXTRACTED" else 1,
            "color": {"opacity": 0.7 if confidence == "EXTRACTED" else 0.35},
            "confidence": confidence,
            "confidence_score": confidence_score,
            "evaluated": bool(data.get("evaluated", False)),
            # Audit provenance for the edge detail panel (showEdgeInfo).
            "reason": _reason_txt,
            "evidence_quote": _quote_txt,
            "evaluation_reason": sanitize_label(str(data.get("evaluation_reason") or "")),
            "source_file": sanitize_label(str(data.get("source_file") or "")),
            "source_location": sanitize_label(str(data.get("source_location") or "")),
        })

    # Build community legend data
    legend_data = []
    for cid in sorted((community_labels or {}).keys()):
        color = COMMUNITY_COLORS[cid % len(COMMUNITY_COLORS)]
        lbl = _html.escape(sanitize_label((community_labels or {}).get(cid, f"Community {cid}")))
        n = member_counts.get(cid, len(communities.get(cid, []))) if member_counts else len(communities.get(cid, []))
        legend_data.append({"cid": cid, "color": color, "label": lbl, "count": n})

    # Build review queue items. Filtering is score-based: any edge or node
    # with confidence_score below the default threshold (0.8) enters the
    # queue. This replaces the old enum-based filter (AMBIGUOUS + INFERRED)
    # which put ALL INFERRED edges in the queue regardless of how confident
    # the Evaluation Agent was. EXTRACTED items (score=1.0) never enter.
    # The threshold is adjustable via a slider in the UI.
    DEFAULT_REVIEW_THRESHOLD = 0.8
    review_items: list[dict] = []
    if review_queue:
        for r in review_queue:
            review_items.append(dict(r))
    # Low-confidence edges from the graph.
    for u, v, data in G.edges(data=True):
        score = float(data.get("confidence_score", 1.0 if data.get("confidence") == "EXTRACTED" else 0.55))
        if score < DEFAULT_REVIEW_THRESHOLD:
            confidence = data.get("confidence", "EXTRACTED")
            src_label = sanitize_label(G.nodes[u].get("label", u))
            tgt_label = sanitize_label(G.nodes[v].get("label", v))
            relation = data.get("relation", "")
            evaluated = bool(data.get("evaluated", False))
            reason = sanitize_label(str(data.get("evaluation_reason") or ""))
            _ext_reason, _ext_quote = _edge_reasons(u, v, data)
            review_items.append({
                "type": "ambiguous_edge" if confidence == "AMBIGUOUS" else "inferred_edge",
                "title": f"{src_label} → {tgt_label}",
                "detail": f"{relation} [{confidence} {score:.2f}]",
                "confidence_score": score,
                "evaluated": evaluated,
                "evaluation_reason": reason,
                # Extraction-time provenance (why this edge was created).
                "reason": _ext_reason,
                "evidence_quote": _ext_quote,
                "source_file": sanitize_label(str(data.get("source_file") or "")),
                "source_location": sanitize_label(str(data.get("source_location") or "")),
                "node_id": u,
                # Edge identity so the audit click can open the EDGE's own
                # detail panel (parity with node clicks) instead of just
                # focusing the source node.
                "edge": {
                    "from": data.get("_src", u),
                    "to": data.get("_tgt", v),
                    "relation": relation,
                },
            })
    # Low-confidence nodes from the graph (LLM-generated nodes that the
    # Evaluation Agent scored low, or unverified nodes).
    for nid, data in G.nodes(data=True):
        if not isinstance(data, dict):
            continue
        score = float(data.get("confidence_score", 1.0))
        if score < DEFAULT_REVIEW_THRESHOLD:
            label = sanitize_label(data.get("label", nid))
            review_items.append({
                "type": "node_review",
                "title": label,
                "detail": f"[{data.get('confidence', 'INFERRED')} {score:.2f}]",
                "confidence_score": score,
                "evaluated": bool(data.get("evaluated", False)),
                "evaluation_reason": sanitize_label(str(data.get("evaluation_reason") or "")),
                "source_file": sanitize_label(str(data.get("source_file") or "")),
                "source_location": sanitize_label(str(data.get("source_location") or "")),
                "node_id": nid,
            })

    # Sort review items by score ascending (lowest confidence first).
    review_items.sort(key=lambda r: r.get("confidence_score", 1.0))

    # Escape </script> sequences so embedded JSON cannot break out of the script tag
    def _js_safe(obj) -> str:
        return json.dumps(obj).replace("</", "<\\/")

    nodes_json = _js_safe(vis_nodes)
    edges_json = _js_safe(vis_edges)
    legend_json = _js_safe(legend_data)
    review_json = _js_safe(review_items)
    # Learn tab payload: pass null when empty so the frontend branch is a
    # single falsy check (and the byte-identity guarantee holds pre-feature).
    learn_json = _js_safe(learn_data) if learn_data else "null"
    hyperedges_json = _js_safe(getattr(G, "graph", {}).get("hyperedges", []))
    _raw_title = sanitize_label(_html_document_title(output_path))
    title = _html.escape(_raw_title)
    title_mark = _html.escape((_raw_title[:1].upper() or "G"))
    stats = f"{G.number_of_nodes()} 节点 &middot; {G.number_of_edges()} 条边 &middot; {len(communities)} 个社区"

    # Compute project overview data for the overview tab
    _src_files = set()
    _ft_lang_map = {"code": "Code", "concept": "Docs/Concepts", "rationale": "Rationale", "document": "Documents", "config": "Config", "": "Other"}
    for _n in vis_nodes:
        _sf = _n.get("source_file", "")
        if _sf:
            _src_files.add(_sf)
    _num_files = len(_src_files)
    # Detect primary language from file extensions
    _ext_counts: dict[str, int] = {}
    for _sf in _src_files:
        _dot = _sf.rfind(".")
        if _dot >= 0:
            _ext = _sf[_dot+1:].lower()
            _ext_counts[_ext] = _ext_counts.get(_ext, 0) + 1
    _lang_map = {"py": "Python", "ts": "TypeScript", "js": "JavaScript", "go": "Go", "rs": "Rust", "java": "Java", "cs": "C#", "cpp": "C++", "c": "C", "rb": "Ruby", "php": "PHP", "kt": "Kotlin", "scala": "Scala", "md": "Markdown", "yaml": "YAML", "yml": "YAML", "json": "JSON", "toml": "TOML", "txt": "Text"}
    _lang_counts: dict[str, int] = {}
    for _ext, _cnt in _ext_counts.items():
        _lang = _lang_map.get(_ext, _ext)
        _lang_counts[_lang] = _lang_counts.get(_lang, 0) + _cnt
    _primary_lang = max(_lang_counts, key=_lang_counts.get) if _lang_counts else "Unknown"
    _lang_list = ", ".join(f"{k} ({v})" for k, v in sorted(_lang_counts.items(), key=lambda x: -x[1])[:5])
    # Community -> files mapping for BC/feature tree
    _comm_files: dict[int, set[str]] = {}
    for _vn in vis_nodes:
        _cid = _vn.get("community", 0)
        _sf = _vn.get("source_file", "")
        if _sf:
            _comm_files.setdefault(_cid, set()).add(_sf)
    # Project name from title (strip .graph/graph.html suffix)
    _proj_name = title.replace(".graph/graph.html", "").strip("/")
    if not _proj_name:
        # Fallback: use parent directory name of output_path
        from pathlib import Path as _P
        _proj_name = _P(output_path).parent.parent.name or _P(output_path).parent.name or "Project"

    # Compute BC cross-community relationship data for bubble diagram
    _node_comm_map: dict[str, int] = {}
    for _vn in vis_nodes:
        _node_comm_map[_vn["id"]] = _vn.get("community", 0)
    _bc_cross: dict[tuple, int] = {}
    for _u, _v, _d in G.edges(data=True):
        _cu = _node_comm_map.get(_u)
        _cv = _node_comm_map.get(_v)
        if _cu is not None and _cv is not None and _cu != _cv:
            _pair = (min(_cu, _cv), max(_cu, _cv))
            _bc_cross[_pair] = _bc_cross.get(_pair, 0) + 1
    # BC bubble data: list of {id, name, color, size, x, y}
    _bc_bubbles = []
    _bc_links = []
    _significant = [c for c in legend_data if c["count"] > 3]
    _n_bubbles = len(_significant)
    import math as _math
    for _i, _c in enumerate(_significant):
        # Place bubbles in a circle layout
        _angle = 2 * _math.pi * _i / max(1, _n_bubbles) - _math.pi / 2
        _r = 160 if _n_bubbles > 1 else 0
        _bx = 250 + _r * _math.cos(_angle)
        _by = 210 + _r * _math.sin(_angle)
        _bubble_r = 14 + min(40, _c["count"] * 1.4)  # radius proportional to node count, capped
        _bc_bubbles.append({
            "id": _c["cid"], "name": _c["label"], "color": _c["color"],
            "size": _c["count"], "r": _bubble_r, "x": _bx, "y": _by,
        })
    for (_a, _b), _w in sorted(_bc_cross.items(), key=lambda x: -x[1])[:15]:
        _ba = next((x for x in _bc_bubbles if x["id"] == _a), None)
        _bb = next((x for x in _bc_bubbles if x["id"] == _b), None)
        if _ba and _bb:
            _bc_links.append({"from": _a, "to": _b, "weight": _w, "x1": _ba["x"], "y1": _ba["y"], "x2": _bb["x"], "y2": _bb["y"]})
    _bc_bubbles_json = _js_safe(_bc_bubbles)
    _bc_links_json = _js_safe(_bc_links)

    # BC detail data: for each BC (community), collect concepts, flows, key files
    _bc_details = {}
    for _c in _significant:
        _cid = _c["cid"]
        _bc_nodes = [_vn for _vn in vis_nodes if _vn.get("community") == _cid]
        _concepts = [n["label"] for n in _bc_nodes if n.get("file_type") in ("concept", "rationale")]
        _code_files = sorted({n["source_file"] for n in _bc_nodes if n.get("file_type") == "code" and n.get("source_file")})
        _doc_files = sorted({n["source_file"] for n in _bc_nodes if n.get("file_type") in ("concept", "rationale", "document") and n.get("source_file")})
        _bc_details[_cid] = {
            "name": _c["label"], "color": _c["color"], "nodeCount": _c["count"],
            "concepts": _concepts[:8], "codeFiles": _code_files[:6], "docFiles": _doc_files[:4],
            "fileCount": len(_comm_files.get(_cid, set())),
        }
    _bc_details_json = _js_safe(list(_bc_details.values()))

    # Try to read README for service description
    _service_desc = ""
    try:
        from pathlib import Path as _P
        _readme_path = _P(output_path).parent.parent / "README.md"
        if _readme_path.exists():
            _readme_text = _readme_path.read_text(encoding="utf-8")
            for _line in _readme_text.split("\n"):
                _line = _line.strip()
                if _line and not _line.startswith("#") and not _line.startswith("```") and not _line.startswith("-") and len(_line) > 20:
                    _service_desc = sanitize_label(_line)
                    break
    except Exception:
        pass
    # If no README description, try AI-generated description from graph metadata
    if not _service_desc:
        try:
            from graphify.llm import _call_llm, detect_backend
            _backend = detect_backend()
            if _backend:
                # Build clues from graph data
                _top_labels = sorted({_n.get("label", "") for _n in vis_nodes
                                      if _n.get("file_type") == "code" and _n.get("label", "")
                                      }, key=lambda x: len(x))[:10]
                _bc_names = [b["name"] for b in _ddd_bcs if b.get("name")]
                _clues = f"Project: {_proj_name}\nLanguage: {_primary_lang}\nFiles: {len(vis_nodes)} nodes\n"
                if _bc_names:
                    _clues += f"Bounded Contexts: {', '.join(_bc_names[:8])}\n"
                if _top_labels:
                    _clues += f"Key components: {', '.join(_top_labels)}\n"
                _prompt = (
                    f"Based on these clues about a software project, write a single sentence "
                    f"(max 150 chars) describing what this project does. Reply with ONLY the "
                    f"description, no explanation.\n\n{_clues}"
                )
                _ai_desc = _call_llm(_prompt, backend=_backend, max_tokens=80)
                if _ai_desc:
                    _ai_desc = _ai_desc.strip().strip('"').strip("'")
                    if len(_ai_desc) > 5 and len(_ai_desc) < 200:
                        _service_desc = sanitize_label(_ai_desc)
        except Exception:
            pass
    if not _service_desc:
        _service_desc = f"{_primary_lang} project with {len(_significant)} modules"

    # Compute code lines from source files
    _code_lines = 0
    _code_file_lines = {}
    try:
        from pathlib import Path as _P
        _proj_root = _P(output_path).parent.parent
        for _vn in vis_nodes:
            if _vn.get("file_type") == "code":
                _sf = _vn.get("source_file", "")
                if _sf and _sf not in _code_file_lines:
                    _fp = _proj_root / _sf
                    if _fp.exists():
                        _lines = sum(1 for _ in _fp.open(encoding="utf-8", errors="replace"))
                        _code_file_lines[_sf] = _lines
                        _code_lines += _lines
    except Exception:
        pass

    # Detect tech stack from package.json, pyproject.toml, etc
    _tech_stack = []
    _tech_stack_detail = []
    try:
        from pathlib import Path as _P
        import json as _json
        _proj_root = _P(output_path).parent.parent
        _pkg_path = _proj_root / "package.json"
        if _pkg_path.exists():
            _pkg = _json.loads(_pkg_path.read_text(encoding="utf-8"))
            _deps = _pkg.get("dependencies", {})
            _dev_deps = _pkg.get("devDependencies", {})
            # Map common deps to tech categories
            _dep_map = {
                "express": "Express.js", "fastify": "Fastify", "koa": "Koa",
                "jsonwebtoken": "JWT", "bcrypt": "bcrypt", "passport": "Passport",
                "typeorm": "TypeORM", "prisma": "Prisma", "mongoose": "Mongoose",
                "react": "React", "vue": "Vue", "next": "Next.js",
                "jest": "Jest", "vitest": "Vitest", "mocha": "Mocha",
                "winston": "Winston", "pino": "Pino",
            }
            for _dep, _ver in list(_deps.items()) + list(_dev_deps.items()):
                _tech_name = _dep_map.get(_dep, _dep)
                _tech_stack.append(_tech_name)
                _tech_stack_detail.append({"name": _tech_name, "version": _ver, "dep": _dep})
            _tech_stack = _tech_stack[:12]
    except Exception:
        pass
    # Also check pyproject.toml for Python projects
    if not _tech_stack:
        try:
            from pathlib import Path as _P
            _py_path = _P(output_path).parent.parent / "pyproject.toml"
            if _py_path.exists():
                _py_text = _py_path.read_text(encoding="utf-8")
                import re as _re
                _deps = _re.findall(r'[\w-]+', _py_text.split("dependencies")[-1].split("]")[0].split("}")[0]) if "dependencies" in _py_text else []
                _tech_stack = _deps[:12]
        except Exception:
            pass

    # Detect DDD BC nodes from the graph (actual Bounded Contexts, not Leiden communities)
    _ddd_bcs = []
    _ddd_bc_links = []
    _node_id_to_data = {_n["id"]: _n for _n in vis_nodes}
    # Filter by tags field: ["ddd", "bounded_context"]
    for _n in vis_nodes:
        _tags = _n.get("tags") or []
        if "ddd" in _tags and "bounded_context" in _tags:
            _desc = _n.get("desc", "") or ""
            # Infer subdomain type from desc keywords
            _subdomain = "unknown"
            _desc_lower = _desc.lower()
            if "核心" in _desc or "core" in _desc_lower:
                _subdomain = "core"
            elif "支撑" in _desc or "supporting" in _desc_lower:
                _subdomain = "supporting"
            elif "通用" in _desc or "generic" in _desc_lower:
                _subdomain = "generic"
            _subdomain_colors = {"core": "#4E79A7", "supporting": "#F28E2B", "generic": "#8D99AE", "unknown": "#4E79A7"}
            _bc_color = _subdomain_colors[_subdomain]
            _ddd_bcs.append({
                "id": _n["id"], "name": _n.get("label", ""), "color": _bc_color,
                "nodeId": _n["id"], "desc": _desc, "subdomain": _subdomain,
                "concept_id": _n.get("concept_id", ""),
            })
    # If no DDD BC nodes found (project has no DDD docs), fall back to top Leiden communities
    if not _ddd_bcs:
        for _c in _significant[:5]:
            _ddd_bcs.append({"id": str(_c["cid"]), "name": _c["label"], "color": _c["color"], "nodeId": None, "desc": "", "subdomain": "unknown", "concept_id": ""})

    # For each DDD BC, collect related tactical DDD concepts via edges
    _ddd_bc_details = []
    for _bc in _ddd_bcs:
        _bc_node_id = _bc.get("nodeId")
        _related_concepts = []  # aggregate_root, domain_event, etc.
        _related_files = []
        _related_bcs = []
        if _bc_node_id:
            for _u, _v, _d in G.edges(data=True):
                _other_id = None
                _is_outgoing = False
                if _u == _bc_node_id:
                    _other_id = _v
                    _is_outgoing = True
                elif _v == _bc_node_id:
                    _other_id = _u
                    _is_outgoing = False
                if _other_id and _other_id in _node_id_to_data:
                    _other = _node_id_to_data[_other_id]
                    _other_label = _other.get("label", "")
                    _other_tags = _other.get("tags") or []
                    _other_type = _other.get("file_type", "")
                    _other_file = _other.get("source_file", "")
                    _rel = _d.get("relation", "")
                    # DDD tactical concepts (aggregate_root, domain_event, invariant, value_object, domain_service)
                    if "ddd" in _other_tags:
                        _ddd_type = next((t for t in _other_tags if t != "ddd"), None)
                        if _ddd_type and _ddd_type != "bounded_context":
                            _related_concepts.append({"label": _other_label, "type": _ddd_type, "relation": _rel})
                    # Related BCs
                    if "bounded_context" in _other_tags and _other_label not in [r["label"] for r in _related_bcs]:
                        _related_bcs.append({"label": _other_label, "relation": _rel, "direction": "out" if _is_outgoing else "in"})
                    # Code files
                    if _other_type == "code" and _other_file and _other_file not in _related_files:
                        _related_files.append(_other_file)
        _ddd_bc_details.append({
            "id": _bc["id"], "name": _bc["name"], "color": _bc["color"],
            "desc": _bc.get("desc", ""), "subdomain": _bc.get("subdomain", "unknown"),
            "concepts": _related_concepts[:12], "relatedBCs": _related_bcs[:6],
            "files": _related_files[:8], "fileCount": len(_related_files),
            "codeFiles": _related_files[:6], "docFiles": [],
        })

    # Layout BC bubbles in a circle
    _n_bc = len(_ddd_bcs)
    for _i, _bc in enumerate(_ddd_bcs):
        _angle = 2 * _math.pi * _i / max(1, _n_bc) - _math.pi / 2
        _r = 110 if _n_bc > 1 else 0
        _bc["x"] = 180 + _r * _math.cos(_angle)
        _bc["y"] = 170 + _r * _math.sin(_angle)
        _bc["r"] = 30

    # BC links with relationship labels
    _bc_id_set = {b["id"] for b in _ddd_bcs}
    for _u, _v, _d in G.edges(data=True):
        if _u in _bc_id_set and _v in _bc_id_set:
            _ba = next((x for x in _ddd_bcs if x["id"] == _u), None)
            _bb = next((x for x in _ddd_bcs if x["id"] == _v), None)
            if _ba and _bb:
                _rel = _d.get("relation", "related")
                _ddd_bc_links.append({
                    "from": _u, "to": _v, "weight": 1,
                    "x1": _ba["x"], "y1": _ba["y"],
                    "x2": _bb["x"], "y2": _bb["y"],
                    "label": _rel,
                })

    _bc_bubbles_json = _js_safe(_ddd_bcs)
    _bc_links_json = _js_safe(_ddd_bc_links)
    _bc_details_json = _js_safe(_ddd_bc_details)

    # Language donut data
    _lang_donut = [{"label": k, "count": v, "color": COMMUNITY_COLORS[i % len(COMMUNITY_COLORS)]} for i, (k, v) in enumerate(sorted(_lang_counts.items(), key=lambda x: -x[1]))]
    _lang_donut_json = _js_safe(_lang_donut)
    _lang_total = sum(_lang_counts.values())

    # Pre-compute language bar HTML (avoids nested f-string dict issues)
    _lang_bar_html = ""
    if _lang_total > 0:
        _lang_sorted = sorted(_lang_counts.items(), key=lambda x: -x[1])
        _lang_parts = []
        for _i, (_lang_name, _lang_cnt) in enumerate(_lang_sorted):
            _pct = max(8, _lang_cnt * 100 // _lang_total)
            _c = COMMUNITY_COLORS[_i % len(COMMUNITY_COLORS)]
            _lang_parts.append(f'<div style="width:{_pct}%;background:{_c};display:flex;align-items:center;justify-content:center;font-size:9px;color:#fff;font-weight:600;font-family:var(--gf-font-mono)">{_lang_name[:4]} {_lang_cnt}</div>')
        _lang_bar_html = "".join(_lang_parts)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<script src="https://unpkg.com/vis-network@9.1.6/standalone/umd/vis-network.min.js"
        integrity="sha384-Ux6phic9PEHJ38YtrijhkzyJ8yQlH8i/+buBR8s3mAZOJrP1gwyvAcIYl3GWtpX1"
        crossorigin="anonymous"></script>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"
        integrity="sha384-WmdflGW9aGfoBdHc4rRyWzYuAjEmDwMdGdiPNacbwfGKxBW/SO6guzuQ76qjnSlr"
        crossorigin="anonymous"></script>
{_html_styles()}
</head>
<body>
<!-- Topbar -->
<header class="topbar">
  <div class="brand"><div class="brand-mark">{title_mark}</div><span>{title}</span></div>
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
    <div class="ovw-max" style="max-width:100%;margin:0">

      <!-- Hero: service name + description -->
      <div class="ovw-hero-card">
        <div class="ovw-hero-info">
          <div class="ovw-hero-lang">{_proj_name}</div>
          <div class="ovw-hero-meta">{_service_desc}</div>
        </div>
      </div>

      <!-- Two-column: left=project overview (1/2), right=BC spheres (1/2) -->
      <div class="ovw-two-col">
        <!-- Left: project overview as table -->
        <div class="ovw-left" style="flex:1;min-width:0">
          <div class="ovw-info-card">
            <div style="font-family:var(--gf-font-heading);font-size:0.875rem;font-weight:600;color:var(--gf-text-primary);margin-bottom:12px">项目总览</div>

            <!-- Info table -->
            <table style="width:100%;border-collapse:collapse;font-size:0.75rem">
              <tbody>
                <tr style="border-bottom:1px solid var(--gf-border-subtle)"><td style="padding:6px 0;color:var(--gf-text-muted);width:40%">主语言</td><td style="padding:6px 0;font-weight:600;color:var(--gf-text-primary);font-family:var(--gf-font-mono)">{_primary_lang}</td></tr>
                <tr style="border-bottom:1px solid var(--gf-border-subtle)"><td style="padding:6px 0;color:var(--gf-text-muted)">代码行</td><td style="padding:6px 0;font-weight:600;color:var(--gf-text-primary);font-family:var(--gf-font-mono)">{_code_lines:,}</td></tr>
                <tr style="border-bottom:1px solid var(--gf-border-subtle)"><td style="padding:6px 0;color:var(--gf-text-muted)">源文件</td><td style="padding:6px 0;font-weight:600;color:var(--gf-text-primary);font-family:var(--gf-font-mono)">{_num_files}</td></tr>
                <tr style="border-bottom:1px solid var(--gf-border-subtle)"><td style="padding:6px 0;color:var(--gf-text-muted)">代码节点</td><td style="padding:6px 0;font-weight:600;color:var(--gf-text-primary);font-family:var(--gf-font-mono)">{sum(1 for n in vis_nodes if n.get("file_type") == "code")}</td></tr>
                <tr style="border-bottom:1px solid var(--gf-border-subtle)"><td style="padding:6px 0;color:var(--gf-text-muted)">领域概念</td><td style="padding:6px 0;font-weight:600;color:var(--gf-text-primary);font-family:var(--gf-font-mono)">{sum(1 for n in vis_nodes if n.get("file_type") in ("concept", "rationale"))}</td></tr>
                <tr style="border-bottom:1px solid var(--gf-border-subtle)"><td style="padding:6px 0;color:var(--gf-text-muted)">模块数</td><td style="padding:6px 0;font-weight:600;color:var(--gf-text-primary);font-family:var(--gf-font-mono)">{len(_significant)}</td></tr>
                <tr><td style="padding:6px 0;color:var(--gf-text-muted)">待审核</td><td style="padding:6px 0;font-weight:600;color:var(--gf-status-ambiguous);font-family:var(--gf-font-mono)">{len(review_items)}</td></tr>
              </tbody>
            </table>

            <!-- Language bar -->
            <div style="margin-top:12px">
              <div style="font-size:0.6875rem;color:var(--gf-text-muted);margin-bottom:4px">语言分布</div>
              <div style="display:flex;height:20px;border-radius:4px;overflow:hidden">
                {_lang_bar_html}
              </div>
            </div>

            <!-- Tech stack -->
            <div style="margin-top:10px">
              <div style="font-size:0.6875rem;color:var(--gf-text-muted);margin-bottom:4px">技术栈</div>
              <div style="display:flex;flex-wrap:wrap;gap:4px">
                {''.join(f'<span class="ovw-tech-tag">{_t}</span>' for _t in _tech_stack) if _tech_stack else '<span style="font-size:0.6875rem;color:var(--gf-text-faint)">未检测到依赖</span>'}
              </div>
            </div>

            <!-- Module overview table -->
            <div style="margin-top:12px">
              <div style="font-size:0.6875rem;color:var(--gf-text-muted);margin-bottom:4px">模块概览</div>
              <table style="width:100%;border-collapse:collapse;font-size:0.6875rem">
                <thead><tr style="border-bottom:1px solid var(--gf-border-medium)">
                  <th style="text-align:left;padding:4px 0;color:var(--gf-text-muted);font-weight:600">模块</th>
                  <th style="text-align:right;padding:4px 8px;color:var(--gf-text-muted);font-weight:600">节点</th>
                  <th style="text-align:right;padding:4px 8px;color:var(--gf-text-muted);font-weight:600">文件</th>
                  <th style="text-align:left;padding:4px 0;color:var(--gf-text-muted);font-weight:600;width:80px">规模</th>
                </tr></thead>
                <tbody>
                  {''.join(f'''<tr style="border-bottom:1px solid var(--gf-border-subtle);cursor:pointer" onclick="document.querySelector('.mode-tab[data-tab=&quot;review&quot;]').click()">
                    <td style="padding:4px 0"><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:{_c["color"]};margin-right:6px"></span><span style="color:var(--gf-text-primary)">{_c["label"]}</span></td>
                    <td style="padding:4px 8px;text-align:right;font-family:var(--gf-font-mono);color:var(--gf-text-secondary)">{_c["count"]}</td>
                    <td style="padding:4px 8px;text-align:right;font-family:var(--gf-font-mono);color:var(--gf-text-muted)">{len(_comm_files.get(_c["cid"], set()))}</td>
                    <td style="padding:4px 0"><div style="height:4px;background:var(--gf-panel);border-radius:2px;overflow:hidden"><div style="height:100%;width:{min(100, _c["count"] * 100 // max(1, max(cc["count"] for cc in legend_data)))}%;background:{_c["color"]};border-radius:2px"></div></div></td>
                  </tr>''' for _c in _significant[:10])}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- Right: BC 3D spheres + detail panel -->
        <div class="ovw-right" style="flex:1;min-width:0">
          <div class="ovw-info-card" style="padding:12px">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
              <span style="font-family:var(--gf-font-heading);font-size:0.875rem;font-weight:600;color:var(--gf-text-primary)">限界上下文 (BC)</span>
              <span id="bc-detail-hint" style="font-size:0.6875rem;color:var(--gf-text-faint)">滚轮缩放 · 拖拽球体 · 点击查看详情</span>
            </div>
            <div style="display:flex;gap:8px">
              <svg class="bc-bubble-svg" viewBox="0 0 360 340" id="bc-bubbles" style="flex:1"></svg>
              <div id="bc-detail-panel" style="width:200px;flex-shrink:0;display:none;background:var(--gf-elevated);border-radius:var(--gf-radius-md);padding:10px;max-height:320px;overflow-y:auto">
                <div id="bc-detail-name" style="font-family:var(--gf-font-heading);font-size:0.8125rem;font-weight:600;margin-bottom:4px"></div>
                <div id="bc-detail-stats" style="font-size:0.6875rem;color:var(--gf-text-muted);margin-bottom:8px"></div>
                <div id="bc-detail-concepts" style="margin-bottom:8px"></div>
                <div id="bc-detail-files"></div>
                <button id="bc-detail-jump" style="width:100%;margin-top:8px;padding:5px;border:1px solid var(--gf-border-medium);background:var(--gf-surface);color:var(--gf-accent-bright);border-radius:6px;font-size:0.6875rem;font-weight:600;cursor:pointer">审核模式查看 &rarr;</button>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
</div>

<!-- Review tab (active by default) -->
<div id="page-review" class="tab-page active">
  <div class="workspace">
    <!-- Left rail (visible when sidebar collapsed) -->
    <div class="sidebar-rail" id="review-sidebar-rail" onclick="toggleSidebar('review')">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
    </div>
    <!-- Left: node list with filters -->
    <aside class="sidebar" id="review-sidebar">
      <div class="sidebar-header">
        <div style="flex:1">
          <div class="sidebar-title">审核</div>
          <div class="sidebar-meta">{len(review_items)} 项待审核</div>
        </div>
        <button class="sidebar-toggle" onclick="toggleSidebar('review')" title="收起侧栏">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
        </button>
      </div>
      <div class="filter-section">
        <div class="filter-section-label">数据类型</div>
        <div class="filter-chip-row" id="filter-type"></div>
      </div>
      <div class="filter-section">
        <div class="filter-section-label">标签</div>
        <div class="filter-chip-row" id="filter-tags"></div>
      </div>
      <div class="sidebar-list" id="node-list">
        <div class="confidence-bar" style="display:flex;align-items:center;gap:4px;padding:4px 12px;border-bottom:1px solid var(--gf-border-subtle);position:sticky;top:0;background:var(--gf-surface);z-index:5">
          <span style="font-size:0.625rem;color:var(--gf-text-muted);font-weight:600;white-space:nowrap">置信度</span>
          <input type="range" id="confidence-threshold" min="0" max="1" step="0.05" value="0.8" style="width:70px;accent-color:var(--gf-accent);cursor:pointer;height:12px" oninput="filterReviewQueue(this.value)">
          <span id="threshold-value" style="font-family:var(--gf-font-mono);font-size:0.5625rem;color:var(--gf-accent-bright);min-width:20px">&lt;0.80</span>
        </div>
      </div>
    </aside>
    <!-- Center: graph -->
    <div class="graph-area">
      <div id="graph"></div>
      <div class="graph-stats" id="stats">{stats}</div>
    </div>
    <!-- Right: detail + edit -->
    <aside class="detail-panel" id="review-detail">
      <div class="detail-header" id="detail-header">
        <div style="flex:1" id="detail-header-content">
          <div class="detail-name">点击节点查看详情</div>
          <div class="detail-meta"></div>
        </div>
        <button class="sidebar-toggle" onclick="toggleDetail('review')" title="收起面板">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
        </button>
      </div>
      <div class="detail-body" id="detail-body">
        <div style="color:var(--gf-text-muted);font-size:0.75rem;text-align:center;padding:20px 0">选择左侧列表中的节点或点击图谱中的节点</div>
      </div>
      <div class="detail-nav">
        <button class="detail-nav-btn" onclick="navSourceFile()"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M14 2v6h6"/></svg>源文件 ↗</button>
        <button class="detail-nav-btn" onclick="navPath()"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/></svg>路径</button>
        <button class="detail-nav-btn" onclick="navExplain()"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>解释</button>
      </div>
      <div class="edit-section" id="edit-section" style="display:none">
        <div class="edit-header"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>审核修正</div>
        <div class="edit-body">
          <div class="edit-tab-row"><button class="edit-tab active">关系</button><button class="edit-tab">节点</button></div>
          <div class="edit-field"><label class="edit-label">关系类型</label><select class="edit-select"><option>calls</option><option>imports</option><option>uses</option><option>defines</option><option>semantically_similar_to</option></select></div>
          <div class="edit-field"><label class="edit-label">置信度</label><select class="edit-select"><option>EXTRACTED</option><option>AMBIGUOUS</option><option>INFERRED</option></select></div>
          <div class="edit-field"><label class="edit-label">修正说明（写入错误报告）</label><textarea class="edit-textarea" id="edit-textarea" placeholder="描述问题与期望的修正..."></textarea></div>
          <div class="edit-actions"><button class="btn btn-ghost" id="edit-skip">跳过</button><button class="btn btn-primary" id="edit-submit">提交修正</button></div>
          <div class="edit-note" id="edit-file-path">→ .graph/error-report/</div>
        </div>
      </div>
    </aside>
    <!-- Right rail (visible when detail collapsed) -->
    <div class="detail-rail" id="review-detail-rail" onclick="toggleDetail('review')">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
    </div>
  </div>
</div>

<!-- Learn tab (multi-perspective: 业务流 / 代码架构 / 特性下钻) -->
<div id="page-learn" class="tab-page">
  <div class="learn-shell" id="learn-shell">
    <!-- 左视角手风琴 + 视图容器由 JS 从 LEARN 渲染；无数据时显示引导。 -->
  </div>
</div>

<!-- Bottom filter bar (community filter) - hidden on overview, shown on review/learn -->
<footer class="bottom-bar" id="bottom-bar" style="display:none">
  <span style="font-size:0.6875rem;color:var(--gf-text-muted);text-transform:uppercase;letter-spacing:0.08em;font-weight:600">社区</span>
  <div id="filter-community" style="display:flex;gap:6px;overflow-x:auto"></div>
  <div class="bottom-divider"></div>
  <div class="bottom-stats" id="stats-bottom">{stats}</div>
</footer>

{_html_script(nodes_json, edges_json, legend_json, _js_safe(type_index), _js_safe(tag_index), review_json, _bc_bubbles_json, _bc_links_json, _lang_donut_json, _lang_total, _bc_details_json, learn_json)}
{_hyperedge_script(hyperedges_json)}
</body>
</html>"""

    write_text_atomic(output_path, html)
    return True
