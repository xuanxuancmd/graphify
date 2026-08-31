## graphify

本项目在 .graph/ 下有一个知识图谱，包含 god nodes、社区结构和跨文件关系。

规则：
- 对于代码库相关问题，当 .graph/graph.json 存在时，请先运行 `graphify query "<question>"`。使用 `graphify path "<A>" "<B>"` 查询关系，使用 `graphify explain "<concept>"` 聚焦某个概念。这些命令返回一个范围明确的子图，通常比 GRAPH_REPORT.md 或直接 grep 输出小得多。
- 如果 .graph/wiki/index.md 存在，请用它做整体导航，而不是直接浏览原始源文件。
- 仅在需要做整体架构评审，或 query/path/explain 没有提供足够上下文时，才读取 .graph/GRAPH_REPORT.md。
- 修改代码后，请运行 `graphify update .` 以保持图谱最新（仅走 AST，无 API 开销）。
