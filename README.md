# graphify

**一个面向 AI 编码助手的技能。** 在 Claude Code、CodeBuddy、Codex、OpenCode、OpenClaw、Factory Droid 或 Trae 中输入 `/graphify`，它会读取你的文件、构建知识图谱，并把原本不明显的结构关系还给你。更快理解代码库，找到架构决策背后的"为什么"。

完全多模态。你可以直接丢进去代码、PDF、Markdown、截图、流程图、白板照片，甚至其他语言的图片 —— graphify 会用 Claude vision 从这些内容中提取概念和关系，并把它们连接到同一张图里。

> Andrej Karpathy 会维护一个 `/raw` 文件夹，把论文、推文、截图和笔记都丢进去。graphify 就是在解决这类问题 —— 相比直接读取原始文件，每次查询的 token 消耗可降低 **71.5 倍**，结果还能跨会话持久保存，并且会明确区分哪些内容是实际发现的，哪些只是合理推断。

```
/graphify .                        # 可用于任意目录：代码库、笔记、论文都可以
```

```
.graph/
├── graph.html       可交互图谱：可点节点、搜索、按社区过滤
├── GRAPH_REPORT.md  God nodes、意外连接、建议提问
├── graph.json       持久化图谱：数周后仍可查询，无需重新读原始文件
└── cache/           SHA256 缓存：重复运行时只处理变更过的文件
```

## 工作原理

graphify 分两轮执行。第一轮是确定性的 AST 提取，对代码文件做结构分析（类、函数、导入、调用图、docstring、解释性注释），这一轮不需要 LLM。第二轮会并行调用 Claude 子代理处理文档、论文和图片，从中提取概念、关系和设计动机。最后把两边结果合并到一个 NetworkX 图里，用 Leiden 社区发现算法做聚类，并导出成可交互 HTML、可查询 JSON，以及一份人类可读的审计报告。

**聚类是基于图拓扑完成的，不依赖 embeddings。** Leiden 按边密度发现社区。Claude 抽取出的语义相似边（`semantically_similar_to`，标记为 `INFERRED`）本来就存在于图中，所以会直接影响社区划分。图结构本身就是相似性信号，不需要额外的 embedding 步骤，也不需要向量数据库。

每条关系都会被标记为 `EXTRACTED`（直接在源材料中找到）、`INFERRED`（合理推断，并附带置信度分数）或 `AMBIGUOUS`（有歧义，需要复核）。所以你始终知道哪些是实际发现的，哪些是模型猜出来的。

## 安装

**要求：** Python 3.10+，并且使用以下平台之一：[Claude Code](https://claude.ai/code)、[CodeBuddy](https://codebuddy.ai)、[Codex](https://openai.com/codex)、[OpenCode](https://opencode.ai)、[OpenClaw](https://openclaw.ai)、[Factory Droid](https://factory.ai) 或 [Trae](https://trae.ai)

```bash
pip install graphifyy && graphify install
```

> PyPI 包当前暂时叫 `graphifyy`，因为 `graphify` 这个名字还在回收中。CLI 命令和 skill 命令仍然都是 `graphify`。

### 平台支持

| 平台 | 安装命令 |
|------|----------|
| Claude Code | `graphify install` |
| OpenCode | `graphify install --platform opencode` |
| CodeAgent | `graphify install --platform codeagent` |

安装命令做两件事：①把 skill 装到全局（`~/.claude/skills/` 或 `~/.config/opencode/skills/` 等），②把常驻 hook 装到全局配置（Claude/CodeAgent 写 `~/.claude/settings.json` / `~/.cac/settings.json` 的 PreToolUse hook；OpenCode 写 `~/.config/opencode/plugins/graphify.js` 的 `tool.execute.before` plugin）。

Codex 用户还需要在 `~/.codex/config.toml` 的 `[features]` 下打开 `multi_agent = true`，这样才能并行提取。CodeBuddy 使用与 Claude Code 相同的 Agent 工具和 PreToolUse hook 机制。OpenClaw 目前的并行 agent 支持还比较早期，所以使用顺序提取。Trae 使用 Agent 工具进行并行子代理调度，**不支持** PreToolUse hook，因此 AGENTS.md 是其常驻机制。

然后打开你的 AI 编码助手，输入：

```
/graphify .
```

`/graphify` 建图成功后，会自动往项目根的 `AGENTS.md`（或 `CLAUDE.md`）注入一段 `## graphify` 常驻提示，告诉 agent 这个项目有图谱、先查图谱再 grep。无需再手动跑额外命令。

### 常驻 hook 和显式触发的区别

常驻 hook（全局安装时已配好）会优先暴露 `GRAPH_REPORT.md` —— 这是一页式总结，包含 god nodes、社区结构和意外连接。你的助手在搜索文件前会先读到它（通过 PreToolUse hook 或 plugin 提醒），因此会按结构导航，而不是按关键字乱搜。这已经能覆盖大部分日常问题。

`/graphify query`、`/graphify path` 和 `/graphify explain` 会更深入：它们会逐跳遍历底层 `graph.json`，追踪节点之间的精确路径，并展示边级别细节（关系类型、置信度、源位置）。当你想从图谱里精确回答某个问题，而不仅仅是获得整体感知时，就该用这些命令。

可以这样理解：常驻 hook 是先给助手一张地图，`/graphify` 这几个命令则是让它沿着地图精确导航。

> `graphify <platform> install`（如 `graphify opencode install`、`graphify claude install`）已废弃。全局 hook 安装由 `graphify install --platform <P>` 完成，项目级 AGENTS.md/CLAUDE.md 注入由 `/graphify` 建图时自动完成。

<details>
<summary>手动安装（curl）</summary>

```bash
mkdir -p ~/.claude/skills/graphify
curl -fsSL https://raw.githubusercontent.com/safishamsi/graphify/v3/graphify/skill.md \
  > ~/.claude/skills/graphify/SKILL.md
```

把下面内容加到 `~/.claude/CLAUDE.md`：

```
- **graphify** (`~/.claude/skills/graphify/SKILL.md`) - any input to knowledge graph. Trigger: `/graphify`
When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.
```

</details>

## 用法

### Skill 命令（在 AI 编码助手里输入）

所有 skill 命令均为对外命令。`<path>` 可省略，默认为当前目录 `.`。多个 flag 可组合使用（如 `/graphify . --mode deep --directed --svg`）。

#### 建图与更新

| 命令 | 说明 |
|---|---|
| `/graphify` | 对当前目录全量建图（AST + 语义 LLM） |
| `/graphify <path>` | 对指定目录全量建图 |
| `/graphify <path> --update` | 增量更新：只重提取变更文件（代码走 AST 免费，文档/图片走 LLM 语义） |
| `/graphify <path> --cluster-only` | 只重新聚类已有图谱，不重新提取 |
| `/graphify <path> --mode deep` | 更激进地抽取 INFERRED 边 |
| `/graphify <path> --directed` | 构建有向图（保留边方向 source→target） |
| `/graphify <path> --whisper-model <model>` | 指定 Whisper 模型转录视频/音频（默认 small，可选 medium/large） |

> `--update` 不带路径时默认对当前目录增量更新。代码变更走 AST（免费、无 LLM）；文档/论文/图片变更走 LLM 语义提取。

#### GitHub 与多仓库

| 命令 | 说明 |
|---|---|
| `/graphify https://github.com/<owner>/<repo>` | clone 仓库后全量建图 |
| `/graphify https://github.com/<owner>/<repo> --branch <branch>` | clone 指定分支 |
| `/graphify <url1> <url2> ...` | 多个 repo clone 后合并为一张跨仓库图 |

#### 添加内容

| 命令 | 说明 |
|---|---|
| `/graphify add <url>` | 拉取 URL 保存到 ./raw，更新图谱 |
| `/graphify add <url> --author "Name"` | 标记原作者 |
| `/graphify add <url> --contributor "Name"` | 标记是谁把它加入语料库的 |

#### 查询与分析

| 命令 | 说明 |
|---|---|
| `/graphify query "<question>"` | BFS 遍历，获取广度上下文 |
| `/graphify query "<question>" --dfs` | DFS 遍历，追踪一条具体路径 |
| `/graphify query "<question>" --budget <N>` | 限制输出 token 数（默认 2000） |
| `/graphify path "<A>" "<B>"` | 两节点间最短路径 |
| `/graphify explain "<X>"` | 节点的自然语言解释 |

#### 导出与可视化

| 命令 | 说明 |
|---|---|
| `/graphify <path> --no-viz` | 跳过 HTML，只生成 report + JSON |
| `/graphify <path> --svg` | 额外导出 graph.svg（可嵌入 Notion、GitHub） |
| `/graphify <path> --graphml` | 导出 graph.graphml（Gephi、yEd） |
| `/graphify <path> --neo4j` | 生成 .graph/cypher.txt 供 Neo4j 导入 |
| `/graphify <path> --neo4j-push <uri>` | 直接推送到运行中的 Neo4j |
| `/graphify <path> --falkordb` | 生成 .graph/cypher.txt 供 FalkorDB 导入 |
| `/graphify <path> --falkordb-push <uri>` | 直接推送到运行中的 FalkorDB |
| `/graphify <path> --obsidian` | 额外生成 Obsidian vault |
| `/graphify <path> --obsidian --obsidian-dir <dir>` | vault 写到自定义路径（如已有 vault） |
| `/graphify <path> --wiki` | 构建 agent 可抓取的 wiki（index.md + 每个 community 一篇文章） |

#### 监视与服务

| 命令 | 说明 |
|---|---|
| `/graphify <path> --watch` | 监视文件夹：代码变更自动重建（无 LLM），文档变更提醒跑 `--update` |
| `/graphify <path> --mcp` | 启动 MCP stdio server，供 agent 访问图谱 |

### CLI 命令（终端里运行）

#### 安装与卸载

| 命令 | 说明 | 对外/对内 |
|---|---|---|
| `graphify install [--platform P]` | 通用安装：装全局 skill + 装全局常驻 hook（PreToolUse/plugin）。P = claude\|windows\|codeagent\|codebuddy\|codex\|opencode\|aider\|amp\|agents\|claw\|droid\|trae\|trae-cn\|gemini\|cursor\|antigravity\|hermes\|kiro\|pi\|devin | 对外 |
| `graphify uninstall [--purge]` | 从所有已检测平台移除（`--purge` 同时删除 .graph/） | 对外 |
| `graphify claude install` | [deprecated] 全局 hook 安装，已归入 `graphify install --platform claude` | 对外 |
| `graphify codeagent install` | [deprecated] 全局 hook 安装，已归入 `graphify install --platform codeagent` | 对外 |
| `graphify <host> install` | [deprecated] 各平台独立安装命令，已归入 `graphify install --platform <host>` | 对外 |

> 项目级 AGENTS.md / CLAUDE.md 注入不再由 CLI 完成，而是在 `/graphify` 建图时自动注入。

#### Git hooks

| 命令 | 说明 | 对外/对内 |
|---|---|---|
| `graphify hook install` | 安装 post-commit + post-checkout hook（跨平台） | 对外 |
| `graphify hook uninstall` | 移除 git hooks | 对外 |
| `graphify hook status` | 检查是否已安装 | 对外 |

#### 图谱构建与更新

| 命令 | 说明 | 对外/对内 |
|---|---|---|
| `graphify extract <path>` | 完整提取（AST + 语义 LLM），适合 CI/脚本 | 对外 |
| `graphify update <path>` | 只重提取代码文件并更新图谱（不需要 LLM） | 对外 |
| `graphify update <path> --force` | 强制覆盖（即使节点数减少） | 对外 |
| `graphify update <path> --no-cluster` | 跳过聚类，只写原始提取结果 | 对外 |
| `graphify cluster-only <path>` | 只重新聚类已有 graph.json | 对外 |
| `graphify watch <path>` | 监视文件夹，代码变更时自动重建图谱 | 对外 |

#### 查询与分析

| 命令 | 说明 | 对外/对内 |
|---|---|---|
| `graphify query "<question>"` | BFS 遍历图谱回答问题 | 对外 |
| `graphify query "<question>" --dfs` | 深度优先遍历 | 对外 |
| `graphify query "<question>" --budget N` | 限制输出 token 数（默认 2000） | 对外 |
| `graphify path "A" "B"` | 两节点间最短路径 | 对外 |
| `graphify explain "X"` | 节点的自然语言解释 | 对外 |
| `graphify affected "X"` | 反向遍历，查找受 X 影响的节点 | 对外 |
| `graphify god-nodes` | 列出连接数最多的节点 | 对外 |
| `graphify diagnose multigraph` | 检测同端点边折叠风险 | 对外 |
| `graphify benchmark [graph.json]` | 测量 token 压缩比 | 对外 |
| `graphify check-update <path>` | 检查是否需要语义重新提取 | 对外 |

#### 导出与可视化

| 命令 | 说明 | 对外/对内 |
|---|---|---|
| `graphify export html` | 从 graph.json 生成可交互 HTML | 对外 |
| `graphify export callflow-html` | 生成 Mermaid 调用流 HTML | 对外 |
| `graphify export obsidian` | 导出 Obsidian vault | 对外 |
| `graphify export svg` | 导出 graph.svg | 对外 |
| `graphify export graphml` | 导出 graph.graphml（Gephi、yEd） | 对外 |
| `graphify export neo4j` | 生成 Neo4j cypher.txt | 对外 |
| `graphify export falkordb` | 推送到 FalkorDB | 对外 |
| `graphify tree` | 生成 D3 可折叠树 HTML | 对外 |

#### 全局图谱

| 命令 | 说明 | 对外/对内 |
|---|---|---|
| `graphify global add <graph.json>` | 添加/更新项目图谱到全局图谱 | 对外 |
| `graphify global add <graph.json> --as <tag>` | 指定 repo 标签 | 对外 |
| `graphify global remove <tag>` | 从全局图谱移除某 repo | 对外 |
| `graphify global list` | 列出全局图谱中的 repo | 对外 |
| `graphify global path` | 打印全局图谱文件路径 | 对外 |

#### 跨仓库与 URL

| 命令 | 说明 | 对外/对内 |
|---|---|---|
| `graphify clone <github-url>` | 克隆 GitHub repo 供 /graphify 使用 | 对外 |
| `graphify merge-graphs <g1> <g2>` | 合并多个 graph.json 为跨仓库图谱 | 对外 |
| `graphify merge-driver <base> <current> <other>` | git merge driver（由 hook install 注册到 .git/config） | 对内 |
| `graphify add <url>` | 拉取 URL 并保存到 ./raw | 对外 |
| `graphify add <url> --author "Name"` | 标记原作者 | 对外 |
| `graphify add <url> --contributor "Name"` | 标记贡献者 | 对外 |

#### 自动维护（内部命令，无需手动调用）

| 命令 | 说明 | 对外/对内 |
|---|---|---|
| `graphify check` | SessionStart hook 自动调用：检测 embedding 是否过期，过期则后台增量刷新 | 对内 |
| `graphify check --all` | 每周计划任务：遍历活跃项目全量刷新 | 对内 |
| `graphify check --no-check` | 内部 detach 子进程：跳过检测，直接刷新 | 对内 |
| `graphify schedule` | 注册每日计划任务（install 时自动注册） | 对内 |
| `graphify schedule --status` | 查看任务是否已注册 | 对内 |
| `graphify schedule --unregister` | 移除计划任务 | 对内 |
| `graphify hook-check` | Codex Desktop PreToolUse hook 的 no-op | 对内 |
| `graphify hook-guard [search\|read] [--strict]` | Claude/Codebuddy PreToolUse guard，引导 agent 优先用图谱 | 对内 |

#### 反馈与学习

| 命令 | 说明 | 对外/对内 |
|---|---|---|
| `graphify save-result` | 保存 Q&A 结果到 .graph/memory/ | 对外（query 后自动调用） |
| `graphify reflect` | 聚合 .graph/memory/ 生成 lessons 文档 | 对外 |
| `graphify label <path>` | 用 LLM 为社区命名 | 对外 |

#### Embedding 配置

在 `.graph/graphifyrc` 中配置（非环境变量）：

```
embed_backend=sentence-transformers     # 或 openai/gemini/kimi/deepseek/ollama/azure
embed_model=paraphrase-multilingual-MiniLM-L12-v2
embed_base_url=http://localhost:8080/v1  # openai-compatible 后端
embed_api_key=any-non-empty-value        # 本地服务器
```

支持混合文件类型：

| 类型 | 扩展名 | 提取方式 |
|------|--------|----------|
| 代码 | `.py .ts .js .go .rs .java .c .cpp .rb .cs .kt .scala .php` | tree-sitter AST + 调用图 + docstring / 注释中的 rationale |
| 文档 | `.md .txt .rst` | 通过 Claude 提取概念、关系和设计动机 |
| 论文 | `.pdf` | 引文挖掘 + 概念提取 |
| 图片 | `.png .jpg .webp .gif` | Claude vision —— 截图、图表、任意语言都可以 |

## 你会得到什么

**God nodes** —— 度最高的概念节点（整个系统最容易汇聚到的地方）

**意外连接** —— 按综合得分排序。代码-论文之间的边会比代码-代码边权重更高。每条结果都会附带一段人话解释。

**建议提问** —— 图谱特别擅长回答的 4 到 5 个问题。

**“为什么”** —— docstring、行内注释（`# NOTE:`、`# IMPORTANT:`、`# HACK:`、`# WHY:`）以及文档里的设计动机都会被抽取成 `rationale_for` 节点。不只是知道代码“做了什么”，还能知道“为什么要这么写”。

**置信度分数** —— 每条 `INFERRED` 边都有 `confidence_score`（0.0-1.0）。你不只知道哪些是猜出来的，还知道模型对这个猜测有多有把握。`EXTRACTED` 边恒为 1.0。

**语义相似边** —— 跨文件的概念连接，即使结构上没有直接依赖也能建立关联。比如两个函数做的是同一类问题但彼此没有调用，或者某个代码类和某篇论文里的算法概念本质相同。

**超边（Hyperedges）** —— 用来表达 3 个以上节点的群组关系，这是普通两两边表达不出来的。比如：一组类共同实现一个协议、认证链路里的一组函数、同一篇论文某一节里的多个概念共同组成一个想法。

**Token 基准** —— 每次运行后都会自动打印。对混合语料（Karpathy 的仓库 + 论文 + 图片），每次查询的 token 消耗可以比直接读原文件少 **71.5 倍**。第一次运行需要先提取并建图，这一步会花 token；后续查询直接读取压缩后的图谱，节省会越来越明显。SHA256 缓存保证重复运行时只重新处理变更文件。

**自动同步**（`--watch`）—— 在后台终端里跑着，代码库一变化，图谱就会跟着更新。代码文件保存会立刻触发重建（只走 AST，不用 LLM）；文档/图片变更则会提醒你跑 `--update` 进行 LLM 再提取。

**Git hooks**（`graphify hook install`）—— 安装 `post-commit` 和 `post-checkout` hook。每次 commit 后、每次切分支后都会自动重建图谱，不需要额外开一个后台进程。

**Wiki**（`--wiki`）—— 为每个 community 和 god node 生成类似维基百科的 Markdown 文章，并提供 `index.md` 作为入口。任何 agent 只要读 `index.md`，就能通过普通文件导航整个知识库，而不必直接解析 JSON。

## Worked examples

| 语料 | 文件数 | 压缩比 | 输出 |
|------|--------|--------|------|
| Karpathy 的仓库 + 5 篇论文 + 4 张图片 | 52 | **71.5x** | [`worked/karpathy-repos/`](worked/karpathy-repos/) |
| graphify 源码 + Transformer 论文 | 4 | **5.4x** | [`worked/mixed-corpus/`](worked/mixed-corpus/) |
| httpx（合成 Python 库） | 6 | ~1x | [`worked/httpx/`](worked/httpx/) |

Token 压缩效果会随着语料规模增大而更明显。6 个文件本来就塞得进上下文窗口，所以 graphify 在这种场景里的价值更多是结构清晰度，而不是 token 压缩。到了 52 个文件（代码 + 论文 + 图片）这种规模，就能做到 71x+。每个 `worked/` 目录里都带了原始输入和真实输出（`GRAPH_REPORT.md`、`graph.json`），你可以自己跑一遍核对数字。
