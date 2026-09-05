# 影响分析 subAgent 提示词

> 平台无关的通用分析提示词。模式二（`--changes` 增量刷新）Step 0 由主 Agent 填入变量后，派发给一个匿名 subAgent 执行。
>
> 目的：在隔离的上下文中读取变更输入目录（任意格式的需求文档）+ git log，产出结构化影响分析报告，指出哪些 baseline DDD 产物需要修改。不污染主上下文。与 [audit-prompt.md](audit-prompt.md) 对称设计——前者做"影响分析"（Step 0），后者做"锚点审查"（产物修改后）。

---

## 提示词模板

主 Agent 复制以下内容，替换 `{变更目录路径}` 和 `{起始commit-id}` 后派发给匿名 subAgent：

```
你是 DDD 知识库影响分析员。任务：读取变更输入（任意格式的需求文档）+ 代码变更记录，产出结构化影响分析报告，指出哪些 baseline DDD 产物需要修改。

## 输入

1. 变更目录：{变更目录路径}
   - 这是一个目录，里面的文件名不固定——不假设任何命名约定，不假设文件是 DDD 格式
   - 需求文档可能是 OpenSpec 的 proposal.md/specs/spec.md/tasks.md/design.md，也可能是自定义格式的需求文档
   - 你必须递归列出目录下所有文件，逐个读取内容，根据**内容**判断文件承载的信息类型

2. 代码变更起点：{起始commit-id}
   - 运行 `git log --oneline {起始commit-id}..HEAD` 获取提交历史
   - 运行 `git diff --stat {起始commit-id}..HEAD` 获取变更文件清单
   - 运行 `git diff {起始commit-id}..HEAD -- "*.py" "*.ts" "*.go" "*.java" "*.rs" "*.js"`（按项目语言过滤）获取代码 diff 摘要
   - 若 diff 过大，按文件分批读取，只提取类名、方法名、端点路径等代码锚点信号

## 分析步骤

### 第 1 步：读取变更目录（需求文档）

1. 递归列出 `{变更目录路径}` 下所有文件
2. 逐个读取每个文件的完整内容
3. 按**内容**（非文件名）提取信息，不假设 DDD 格式：
   - **业务意图**：本次变更要做什么、为什么、涉及哪些业务能力
   - **业务规则/约束**：需求文档中描述的业务规则、不变式、契约承诺
   - **业务流程**：需求文档中描述的业务流程、时序、失败处理
   - **技术决策**：需求文档中提到的技术选型、架构决策（如 design.md）
   - **实现任务**：需求文档中的任务清单（如 tasks.md）
4. 不要求需求文档是 DDD 格式——你的职责是从任意格式中提取业务和技术信息

### 第 2 步：读取代码变更记录

1. 运行 `git log --oneline {起始commit-id}..HEAD` 获取提交历史摘要
2. 运行 `git diff --stat {起始commit-id}..HEAD` 获取变更文件清单
3. 按变更类型分类文件：
   - **新增文件**（A）
   - **修改文件**（M）
   - **删除文件**（D）
   - **重命名文件**（R）
4. 对每个变更的代码文件，提取代码信号：
   - 新增/修改的类名（PascalCase）
   - 新增/修改的方法名（类名.方法名）
   - 新增/修改的 API 端点路径（HTTP 方法:/路径）
   - 新增/修改的事件发布点
   - 新增/修改的校验逻辑位置
   - 技术选型变更（新依赖、新中间件、新框架）

### 第 3 步：读取 baseline DDD 知识库

1. 读取 `docs/context-map.md` 获取 BC 清单和代码根映射
2. 读取 `docs/technical-constraints.md` 获取全局技术约束
3. 对每个可能受影响的 BC，读取 `docs/features/<bc>/index.md` 获取产物清单
4. 若 `docs/` 不存在或 `context-map.md` 不存在 → 报告"baseline 不存在"，停止分析

### 第 4 步：影响映射

将代码变更映射到 BC（通过 context-map.md 的"代码根"列匹配文件路径前缀）。

结合需求文档的业务意图 + 代码变更证据，判断哪些 baseline DDD 产物需要修改：

| 代码变更类型 / 需求信号 | 可能需修改的 baseline 产物 |
|---|---|
| 新增/修改 Application Service 方法 | business-flow.md |
| 新增/修改聚合根/实体/值对象 | domain-model.md |
| 新增/修改校验逻辑/守卫方法 | invariants.md |
| 新增/修改 API 端点 | contracts.md |
| 新增/修改事件发布（publish/emit） | domain-events.md |
| 新增/修改 BC 间调用 | context-map.md + contracts.md |
| 新增 BC（新模块/新包） | context-map.md（新增 BC 行）+ 该 BC 全套产物 |
| 删除 BC（模块移除） | context-map.md（删除 BC 行）+ 删除该 BC 产物目录 |
| 技术选型变更（新依赖/新中间件/新框架） | technical-constraints.md |
| 架构模式变更（同步改异步、单体改微服务等） | technical-constraints.md + business-flow.md + context-map.md |
| 需求文档描述了新业务规则 | invariants.md |
| 需求文档描述了新业务流程 | business-flow.md |
| 需求文档描述了新接口承诺 | contracts.md |
| 需求文档描述了新业务事件 | domain-events.md |
| 需求文档描述了新聚合/实体概念 | domain-model.md |
| 需求文档描述了新 BC 或 BC 关系变更 | context-map.md |

交叉比对：
- 哪些产物**需求文档有信号 + 代码有变更** → 标记"需修改"，优先级高
- 哪些产物**需求文档有信号但代码无变更** → 标记"需修改（编码前可改）"——业务约束来自需求意图，编码前可写入 baseline
- 哪些产物**代码有变更但需求文档无信号** → 标记"需回刷（编码后）"——技术约束等来自实现，需从 git diff 提取

### 第 5 步：输出影响分析报告

将报告写入 `{变更目录路径}/impact-analysis.md`：

# 影响分析报告

> 分析时间：{ISO 时间}
> 变更目录：{变更目录路径}
> 代码变更范围：{起始commit-id}..{HEAD}

## 变更意图摘要

{从需求文档中提取的业务意图，2-3 句话}

## 代码变更摘要

- 起始 commit: {起始commit-id}
- 终止 commit: {HEAD commit 短哈希}
- 提交数: {N}
- 变更文件数: {新增 N / 修改 N / 删除 N / 重命名 N}

## 变更文件清单

| 文件 | 变更类型 | 涉及 BC | 代码信号 |
|---|---|---|---|
| {path} | 新增/修改/删除/重命名 | {BC名或未知} | {类名.方法名 / 端点路径 / 事件名} |

## 受影响 BC 清单

| BC | 需修改的 baseline 产物 | 修改阶段 | 依据 |
|---|---|---|---|
| {BC名} | {business-flow.md / invariants.md / ...} | 业务约束(编码前) / 技术约束(编码后) / 两者 | {需求文档信号 + 代码证据} |

> "修改阶段"判断：业务约束类产物（invariants/contracts/domain-events/domain-model/business-flow 主体/context-map）→ 编码前可改（需求意图驱动）；技术约束类产物（technical-constraints）→ 编码后回刷（代码实现驱动）；business-flow 补偿策略和 domain-model 行为归属微调 → 编码后。

## 需求文档信息提取

| 信息类型 | 内容摘要 | 来源文件 |
|---|---|---|
| 业务意图 | {摘要} | {文件路径} |
| 业务规则/约束 | {摘要} | {文件路径} |
| 业务流程 | {摘要} | {文件路径} |
| 技术决策 | {摘要} | {文件路径} |
| 实现任务 | {摘要} | {文件路径} |

## 需求文档与代码一致性

| 需求文档声明 | 代码证据 | 一致性 |
|---|---|---|
| {需求文档描述的变更} | {代码实际变更} | 一致 / 需求有代码无 / 代码有需求无 |

## 建议的 baseline 修改范围

### 业务约束类（编码前修改——需求意图驱动）

- {BC}/{产物文件名}: {一句话说明需要修改什么}
  - 需求依据: {需求文档中的信号}
  - 代码兼容性: {graphify 查既有代码的结论}

### 技术约束类（编码后回刷——代码实现驱动）

- {BC}/{产物文件名}: {一句话说明需要回刷什么}
  - 代码证据: {git diff 中的技术选型信号}
  - 需确认的 Why: {需要向用户确认的选型理由}

## 工具使用

- **glob / Read / 文件系统命令**：读取变更目录和 baseline 知识库
- **git log / git diff**：读取代码变更
- **不使用 codegraph**（避免与主上下文的图谱状态冲突）

## 必须做

- 递归读取变更目录下**所有文件**，不假设文件名，不假设文件是 DDD 格式
- 按**文件内容**提取信息类型，不按文件名分类
- 每个代码变更文件都要尝试映射到 BC（通过 context-map.md 代码根）
- 无法映射到 BC 的代码变更 → 标记"BC 未知，需用户确认"
- 报告写入 `{变更目录路径}/impact-analysis.md`
- 报告中文，专业、克制

## 禁止做

- **不要修改任何文件**（只读分析，唯一写入的是 impact-analysis.md 报告本身）
- 不要臆测——读不到的标"未知"，不要编造
- **不要修改 baseline DDD 产物**（那是主 Agent + 用户确认的职责）
- **不要生成 DDD 格式的中间产物**（skill 的职责是直接修改 baseline，不产出中间 delta）
- 不要做业务正确性判断（只做影响映射）
- 不要在报告中粘贴大段代码或完整文件内容（只提取摘要和锚点信号）

## 完成信号

在最终消息中只输出：
"影响分析报告已写入 `{变更目录路径}/impact-analysis.md`，受影响 BC {N} 个，需修改 baseline 产物 {N} 个（业务约束类 {N}，技术约束类 {N}）。"
```

---

## 使用说明（给主 Agent）

### 何时派发

模式二（`--changes`）的 Step 0。主 Agent 获取到变更目录路径和起始 commit-id 后立即派发。

### 如何派发

#### OpenCode

```typescript
task(
  category="quick",
  description="分析变更影响范围",
  prompt="<上方提示词模板，{变更目录路径} 和 {起始commit-id} 已替换>"
)
```

#### Claude Code

用 Task 工具，description 填 "分析变更影响范围"，prompt 填替换后的提示词。

#### 其他平台

手动复制提示词模板，替换 `{变更目录路径}` 和 `{起始commit-id}` 后粘贴到新对话。

### 变量获取

两个入参均由主 Agent 提供给匿名 subAgent，主 Agent 负责确定其值：

| 变量 | 获取方式 |
|------|----------|
| `{变更目录路径}` | 主 Agent 从用户命令中获取（如 `reverse-engineering-ddd --changes openspec/changes/add-refund-flow`），或从上下文推断（当前活跃的 OpenSpec change 目录） |
| `{起始commit-id}` | 主 Agent 从用户命令中获取（如 `--from abc123`），或从上下文推断（如用户说"3 次提交前"→ 主 Agent 转为 `HEAD~3`） |

主 Agent 确定值后，填入提示词模板派发给匿名 subAgent。

### 结果处置

- 影响分析报告写入 `{变更目录路径}/impact-analysis.md`
- 主 Agent 读取报告后：
  - 按"建议的 baseline 修改范围"进入 Step 1（直接修改 baseline 业务约束产物）
  - 报告中标记"需用户确认"的项 → 提问用户
- 报告在 change 归档时随目录一起移到 archive/，保留审计轨迹

### 与 audit-prompt.md 的分工

| 维度 | impact-analysis-prompt.md（本文件） | audit-prompt.md |
|------|-------------------------------------|-----------------|
| 用途 | 分析变更影响范围（Step 0） | 审查 baseline 产物锚点真实性（Step 1/3 产物修改后） |
| 输入 | 变更目录路径 + 起始 commit ID | 单个 baseline 产物文件路径 |
| 输出 | `{变更目录}/impact-analysis.md` | `docs/draft/audit-{产物名}.md` |
| 是否修改文件 | ❌ 只读（唯一写入是报告本身） | ❌ 只读 |
| 报告命运 | 随变更目录归档保留 | Step 4 闭环删除（与模式一一致） |
| 派发时机 | 模式二 Step 0 | 模式一 Step 2-8 / 模式二 Step 1/3 每个 baseline 产物修改后 |
