---
trigger: always_on
description: 在 .graph/ 下的 graphify 知识图谱中查询代码库与架构问题。
---

## graphify

本项目在 .graph/ 下有一个 graphify 知识图谱。

规则：
- 对于代码库或架构相关问题，当 `.graph/graph.json` 存在时，请先运行 `graphify query "<question>"`（CLI）或 `query_graph`（MCP）。使用 `graphify path "<A>" "<B>"` / `shortest_path` 查询关系，使用 `graphify explain "<concept>"` / `get_node` 聚焦某个概念。这些命令返回一个范围明确的子图，通常比 `GRAPH_REPORT.md` 或直接 grep 输出小得多。
- 如果 .graph/wiki/index.md 存在，请用它做整体导航，而不是直接读取原始文件
- 仅在需要做整体架构评审，或 query/path/explain 没有提供足够上下文时，才读取 .graph/GRAPH_REPORT.md
- 在本次会话中修改代码文件后，请运行 `graphify update .` 以保持图谱最新（仅走 AST，无 API 开销）
