## graphify

对于关于本仓库架构、结构、组件，或如何新增/修改/查找代码的任何问题，当 `.graph/graph.json`
存在时，你的第一个动作应当是 `graphify query "<question>"`。使用 `graphify path "<A>" "<B>"`
查询关系，使用 `graphify explain "<concept>"` 查询聚焦概念。这些命令返回一个范围明确的子图，
通常比完整报告或直接 grep 输出小得多。

触发短语："如何……"、"……在哪里"、、"……是做什么的"、"新增/修改某个 <组件>"、
"解释一下架构"，以及任何依赖文件或类之间关系的提问。

如果 `.graph/wiki/index.md` 存在，请用它做整体导航。仅在需要做整体架构评审，或 query/path/explain
没有提供足够上下文时，才读取 `.graph/GRAPH_REPORT.md`。只有以下情况才直接读取源文件：
(a) 修改/调试具体代码，(b) 图谱缺少所需细节，或 (c) 图谱缺失或已陈旧。

在 Copilot Chat 中输入 `/graphify` 即可构建或更新图谱。
