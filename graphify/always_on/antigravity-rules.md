---
trigger: always_on
description: Consult the graphify knowledge graph at .graph/ for codebase and architecture questions.
---

## graphify

This project has a graphify knowledge graph at .graph/.

Rules:
- For codebase or architecture questions, when `.graph/graph.json` exists, first run `graphify query "<question>"` (CLI) or `query_graph` (MCP). Use `graphify path "<A>" "<B>"` / `shortest_path` for relationships and `graphify explain "<concept>"` / `get_node` for focused concepts. These return a scoped subgraph, usually much smaller than `GRAPH_REPORT.md` or raw grep output.
- If .graph/wiki/index.md exists, navigate it instead of reading raw files
- Read .graph/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context
- After modifying code files in this session, run `graphify update .` to keep the graph current (AST-only, no API cost)
