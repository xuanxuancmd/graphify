---
name: reverse-engineering-ddd
description: >-
  逆向工程提取项目业务约束、技术约束等隐性知识，供后续 AI 理解需求与增量开发使用。
  触发词：逆向工程, 领域知识梳理, reverse-engineer domain, extract domain knowledge, clarify legacy。
---

# reverse-engineering-ddd

## 概述

本 skill 阅读已有项目，与用户**共建**业务约束、技术约束等隐性知识层，供后续 AI 理解需求、增量开发时按需加载。

### 知识库的职责边界

本知识库**只承载 AI 难以从代码仓提取、且对未来增量开发有意义的隐性知识**（WHY/RULES/REASONS/TRADE-OFFS）。

| 层 | 提供者 | 内容 | 性质 |
|---|---|---|---|
| **隐性知识层** | 本 skill 产出 | 业务约束、技术约束等 | 代码无法揭示的 WHY/RULES/REASONS，需人工共建 |
| **代码结构层** | graphify 图谱 | 类型、字段、方法、调用关系、依赖、ER/字段关系、表结构、CI/lint/覆盖率配置 | 代码即真理，可查询，随代码演进 |

### 核心原则

1. **代码是提问的素材，不是结论的来源。** 代码告诉你 WHAT，只有人告诉你 WHY 和 SO-THAT。读码是为了生成好问题，不是生成结论。
2. **一次一个问题。** 通过提问逐步了解项目，与用户达成思想上的一致——而非"呈现推断请你确认"。
3. **产物是已确认的干净态。** 产物文档中不出现 `[INFERRED]`、`[OBSERVED]`、file:line 证据、代码段粘贴等中间态——这些只存在于临时文件，产物不包含自检项等临时内容。
4. **临时文件闭环即删。** 证据、推断、假设、提问记录在 `draft/` 临时文件中；所有 phase 闭环、产物定稿后删除。
5. **不为代码结构复述。** 可以引用包名、类名、关键函数名等（这些名称本身包含业务专有名词）。但禁止引用代码段，代码详情应该使用 graphify 图谱。
6. **不臆造。** 产物中的每条知识都需有代码信号或用户陈述为依据。依据写在临时文件，产物只写结论。
7. **准入门槛：AI 难提取 + 对未来有意义。** 每条拟写入产物的知识必须同时满足两个条件：(a) AI 难以直接从代码仓提取（否则归 代码图谱查询，不在此重复）；(b) 对未来增量开发有指导意义（能影响"怎么改是对的"决策）。任一不满足则不记录。特别是：可从 CI/lint/构建配置直接读到的质量门禁、覆盖率门槛、lint 规则等事实层内容，不记入本知识库。
8. **表格优先，按需展开。** 产物默认用表格表述，简单业务一个表格足矣。只有复杂场景才在表格行后追加详情子节（`### {ID}: {名称}`）。不强行展开所有章节——无内容的维度标 N/A 或不生成文件。**文件内部标注"可选"的章节，无实际内容时直接删除整个章节，不保留空表格、空描述或占位符。**
9. **简单业务简单描述。** 一句话能说清的不用段落，一段能说清的不用多段。文档体量与业务复杂度匹配，避免冗余。
10. **模板即产物结构。** 模板文件只含产物结构 + 占位符，不含填写指引 blockquote、自检章节、判定规则表等过程性内容（这些归 references 参考文档）。执行者照模板填充即得到干净产物。

### 反模式：显而易见的通用知识禁止记录

本知识库只承载**项目特有的隐性知识**（WHY/RULES/REASONS），不承载任何合格开发者已知晓的行业常识。通用知识即使代码中未显式写出（AI 难提取），也不记录——记录它们不提供项目特有的决策价值，反而稀释知识库的信噪比。

## --help 模式

当用户传入 `--help` 参数（或在对话中请求查看 skill 帮助）时，**立即读取并输出 [help.md](help.md) 的全部内容**，不执行逆向工程流程。

help.md 独立维护，包含所有产物文件的用途、价值、所涉及的 DDD 概念介绍，以及 DDD 核心术语速查表。该文档与逆向工程流程解耦，可独立修改——新增产物文件或调整 DDD 概念解释时，只需编辑 help.md。

## 何时使用

- 需要理解现有代码库的**业务结构**（限界上下文、业务流程、业务不变式、契约语义）
- 需要理解项目的**约束体系**（技术选型约束）
- 被要求"理解当前业务"、"梳理领域知识"、"逆向工程"

---

## 约束类型体系

影响开发决策的知识分为两类约束。这两类是完备的——任何影响开发决策的约束都可以归入其中之一。

| 约束类型 | 回答的问题 | 提取方法 | 产物 |
|---------|----------|---------|------|
| **业务约束** | "领域里什么必须为真？" | DDD 战略设计 | `context-map.md` + 各 BC 的 `business-flow.md` / `invariants.md` / `contracts.md` / `domain-events.md` / `domain-model.md` |
| **技术约束** | "业务通过什么技术实现？代码编写有什么规则？" 业务实现技术（设计模式/算法/架构/并发模型/安全模型/高可靠设计）+ 编码规范 + 合规约束 + trade-off 优先级（当代码中出现有意场景化差异时） | 扫描代码模式/构建配置 → 问用户选型理由 | `technical-constraints.md`（全局+BC级） |

> 原"质量约束"（CI 门禁、覆盖率、lint 规则等）可从 CI/lint/构建配置直接读取，AI 能提取且对未来增量开发意义有限，已合并：trade-off 优先级融入技术约束的选型理由字段，其余不单独产出。

> 模板可按项目需要更换章节结构，但必须保持"规则+理由"的写法。

### 与 Diátaxis 的对应

本知识库对应 Diátaxis 框架的 **Explanation 象限**——理解导向，回答"为什么是这样"。

| Diátaxis 象限 | 性质 | 归属 |
|--------------|------|------|
| **Explanation** | 理解导向——"为什么" | **本知识库** |
| **Reference** | 事实导向——"是什么" | graphify 图谱 / 代码结构查询 / CI/lint/构建配置 |
| **How-to** | 任务导向——"怎么做新事" | 编码段（不在本知识库范围） |
| **Tutorial** | 学习导向——"入门" | 编码段（不在本知识库范围） |

---

## 产出工件

产出分两类：**产物文件**（经确认、干净、长期保留）和**临时文件**（承载中间态、闭环后删除）。

```
docs/
├── context-map.md                    # ① 业务边界图（BC + 关系 + 统一语言）—— L0 会话级预加载
├── technical-constraints.md          # ② 技术约束（仅全局适用）—— 编码前读
│
├── features/                         # 按 BC（子特性）组织（L2 按需加载）
│   └── <bc-name>/
│       ├── index.md                  # ④ BC入口（速查表）—— 开发该 BC 时读
│       ├── technical-constraints.md  # 技术约束（仅该 BC 特有）—— 开发该 BC 时读
│       ├── business-flow.md          # 关键业务用例时序编排（Application Service 编排）+ 失败/补偿矩阵（Saga 模式，非 DDD）。时序仅保留入口点和核心角色，方法级细节交 understand 图谱。含周期任务、外部触发等关键入口
│       ├── invariants.md             # 业务不变式（可空：无聚合根/无状态、无真正业务不变式或仅显而易见规格时不生成）
│       ├── contracts.md              # 业务契约语义（混合 DDD OHS/PL + Design by Contract + Saga，非纯 DDD）
│       ├── domain-events.md          # 业务事件（DDD 标准概念，Evans 原书未收录、后补入 DDD Reference；失败/补偿列属 Saga）
│       ├── domain-model.md           # 聚合协作视图（业务级，非字段级ER）
│       └── api/                      # Karate .feature 文件目录（可选；需另行安装 harness-karate-design skill，未安装时不生成）
│
│
└── draft/                            # ⚠️ 临时工作区——闭环后整体删除
    ├── inferences-draft.md           # 代码信号 + [INFERRED] 推断（合并）
    ├── assumptions-draft.md          # [ASSUMPTION] 假设记录
    ├── questions-log.md              # 已提问与回答记录
    └── audit-*.md                    # 各产物的匿名审查报告（审查协议见 references/audit-prompt.md）
```

### 产物归属规则

| 约束类型 | 全局级产物 | BC 级产物 |
|---------|-----------|----------|
| 业务约束 | `context-map.md` | `business-flow.md` / `invariants.md` / `contracts.md` / `domain-events.md` / `domain-model.md` |
| 技术约束 | `technical-constraints.md`（仅全局适用约束） | `features/<bc>/technical-constraints.md`（仅该 BC 特有约束） |

> 判断全局 vs BC 级：约束适用于所有 BC → 全局 `technical-constraints.md`；仅适用于某个 BC → 该 BC 的 `features/<bc>/technical-constraints.md`。跨 BC 通用的约束（如全局错误处理规范）归全局文件，不要误拆到 BC 下。

### 归属原则

信息不存在"共享"——一定有一个维护主体：

- 业务概念由 BC B 定义、BC A 使用 → 归属 B 的 `domain-model.md`；A 的 `contracts.md` 记录依赖
- 两个 BC 共同维护同一组概念（极少）→ 指定一个主体 BC 定义，另一个在 `context-map.md` 中标记为 Conformist 关系
- 约束全局适用 → 全局产物；仅 BC 特有 → 记入对应约束文件并标注适用范围

### 加载策略

本知识库与 graphify 图谱协同工作。图谱是主检索入口（代码结构 + 业务结构），本知识库承载图谱无法提取的隐性知识（WHY/RULES/REASONS）。

| 层级 | 何时读 | 读什么 | 目的 |
|------|--------|--------|------|
| **L0 会话级预加载** | 每次会话开始 | `context-map.md` + 全局 `technical-constraints.md` | 业务地图 + 全局技术约束。图谱无法替代，模型需要它才知道"该查什么" |
| **L1 按需加载** | graphify query 返回 doc-anchor 时按其 `filePath` 加载；或 query 无相关结果时由 AI 自主判断是否需要 | 按下表 BC 级产物清单选载（含 BC 级 `technical-constraints.md`） | 获取图谱无法提供的完整业务语境（WHY/RULES/REASONS） |

> 跨 BC 依赖不靠共享文件，靠 BC 自身的 `contracts.md` 记录指向对端 BC。查全局依赖看 `context-map.md` 关系表。BC 的 `features/<bc>/api/` 子目录承载该 BC 对外暴露 API 的 Karate 测试 feature（由 `harness-karate-design` 生成），与业务约束产物同层但用 `api/` 子目录隔离。

### 工件承载边界（按需选载，不全载）

> AI 增量开发时按下表判断需要加载哪个工件，避免全载浪费上下文。

| 工件 | 承载什么（独占） | 不承载什么（去其他工件查） | 加载时机 |
|------|----------------|------------------------|---------|
| `technical-constraints.md`（全局） | 跨所有 BC 适用的技术选型理由 + 编码规范 + 合规约束 | BC 特有约束 → BC 级 technical-constraints | 每次会话 L0 预加载 |
| `technical-constraints.md`（BC 级） | 仅该 BC 特有的技术选型理由 + 编码规范 + 合规约束 | 全局约束 → 全局 technical-constraints；业务流程→business-flow | 开发该 BC 时读 |
| `business-flow.md` | 关键业务用例时序编排（含周期任务/外部触发入口，仅入口点+核心角色，方法级细节交图谱）；失败/补偿矩阵；每步业务理由（WHY）。**概念映射**：时序编排→DDD Application Service；跨 BC 协作→DDD Domain Event；失败/补偿→Saga 模式（非 DDD） | 聚合静态结构→domain-model；静态约束→invariants；单接口承诺→contracts；事件→domain-events；User Story/单场景断言→.feature；调用图/方法签名→图谱 | 涉及业务流程编排、失败补偿策略、定位入口点（含周期任务）时 |
| `invariants.md` | 业务不变式（聚合根的状态承诺，违反即业务状态非法）；显而易见的不变式不记录 | 防御性编程（参数校验）；接口契约（单次调用承诺）→contracts；流程编排→business-flow；显而易见的规格→不记录 | 需要判断什么必须永远为真时 |
| `contracts.md` | 单接口的业务承诺（前置/后置/失败语义/幂等性）；跨 BC 契约的协议+定位符+operationId。**概念映射**：协议/语言→DDD OHS/Published Language；业务承诺→Design by Contract；失败后果→Saga | 流程编排→business-flow；聚合结构→domain-model；错误码详情→swagger/契约文件本身 | 需要理解接口的业务语义、查 swagger 端点归属时 |
| `domain-events.md` | 业务状态变更事件。**概念映射**：DDD 标准概念（Evans 原书未收录、后补入 DDD Reference）；失败/补偿列属 Saga 模式 | 流程编排→business-flow；接口承诺→contracts | 需要理解业务状态转换时 |
| `domain-model.md` | 聚合协作视图（业务级）；聚合边界；状态机；行为归属（贫血/充血） | 字段级 ER→图谱；流程编排→business-flow；接口承诺→contracts | 需要理解聚合如何协作完成业务、行为在哪个对象上时 |

### 表格标签

BC 级产物的表格标签遵循**三标签一组原则**：每张表要么三个标签全有，要么三个标签全无。

| 标签 | 含义 |
|---|---|
| `<anchor:ddd>` | DDD 业务概念标识——**业务术语**（非代码类名、非 ID），列名会作为图谱类别关键词提取。特例：代码类名本身就是业务术语时可使用类名（如领域事件名 `ConnectorStarted`，或 Kafka 生态中 `Worker`/`Connector` 等通用术语） |
| `<anchor:code>` | 代码锚点——**仅支持三类格式**：`类名` / `类名.函数名` / `HTTP方法:/路径`（如 `POST:/path`）。禁止文件路径、`文件#类名`等其他格式 |
| `<anchor:desc>` | 业务语义描述——该列内容将作为图谱入库的主描述字段 |

**白名单**（参与校验）：`business-flow.md` / `invariants.md` / `contracts.md` / `domain-events.md` / `domain-model.md`

**豁免**（不参与校验）：`context-map.md`（索引文档）、`technical-constraints.md`（子节列表式）、`index.md`（索引文档）、`domain-model.md` 中的行为归属表（附属属性说明，非独立可检索实体）

**标签规则**：
- 白名单产物中的每张表**要么三个标签全有**（`<anchor:ddd>` + `<anchor:code>` + `<anchor:desc>`），**要么三个标签全无**（附属属性说明表）
- `<anchor:ddd>` 列必须是表的唯一键，内容为有意义的业务概念名称（非 ID），支持语义检索
- `<anchor:desc>` 列内容将作为图谱入库的主描述字段——选择最能代表该实体业务语义的列
- 三个标签是一组，不可拆分

---

## 重建顺序

### Phase 1：业务约束（DDD）

| Step | 内容 | 加载参考 |
|------|------|---------|
| 0 | **全局意图** — 了解项目业务问题、核心能力、能力域，校准后续扫描 | 读项目工程文档（AGENTS.md / README / 架构文档） |
| 1 | **代码结构** — 建立代码图谱/扫描结构，带着意图校准目录解读 | — |
| 2 | **业务边界** — 确定限界上下文、战略分类、关系、统一语言 | [business/ddd.md](references/business/ddd.md) §3 |
| 3 | **业务流程** — 端到端用例叙事，跨 BC 协作 | [business/ddd.md](references/business/ddd.md) §4 |
| 4 | **契约** — 业务承诺与通信方向 | [business/ddd.md](references/business/ddd.md) §5 |
| 5 | **事件** — 业务状态转换 | [business/ddd.md](references/business/ddd.md) §6 |
| 6 | **聚合协作** — 业务级聚合协作，含行为归属识别 | [business/ddd.md](references/business/ddd.md) §7 |
| 7 | **不变式** — "必须永远为真"的业务规则 | [business/ddd.md](references/business/ddd.md) §8 |

> Phase 1 每个 Step 的产物产出后，派发匿名 subAgent 审查真实性（见 [references/audit-prompt.md](references/audit-prompt.md)）。审查报告写入 `docs/draft/audit-{产物文件名}.md`，PASS 才进入下一步。

### Phase 2：技术约束

| Step | 内容 | 加载参考 | 产出 |
|------|------|---------|------|
| 8 | **技术约束** — 业务实现技术（设计模式/算法/架构/并发模型/安全模型/高可靠设计）+ 编码规范（错误处理/日志/测试/命名）+ 合规约束（依赖/兼容性/许可证）+ trade-off 优先级（当代码出现有意场景化差异时）+ 隐形架构决策中的技术选型理由 | [technical/technical.md](references/technical/technical.md) | `technical-constraints.md` |

> Phase 2 全局与各 BC 级 `technical-constraints.md` 产出后，同样派发匿名 subAgent 审查（见 [references/audit-prompt.md](references/audit-prompt.md)）。

### Phase 3：闭环

| Step | 内容 | 加载参考 | 产出 |
|------|------|---------|------|
| 9 | **闭环** — 评审 + 持久化 + 删除临时文件 | [methodology.md](references/methodology.md) §6 | 各 BC `index.md` + AGENTS.md 更新 |

> Phase 2 的约束提取不依赖 Phase 1 的逐 BC 深入分析，但依赖 Step 2 的业务边界（确定全局 vs BC 级归属）。设计决策（为什么是现在的样子）不单独产出，而是融入各约束的"选型理由/决策理由（Why）"字段中。隐形架构决策按性质归入：架构选型理由→技术约束，一致性策略理由→业务不变式，模型风格理由→技术约束。产物聚焦 Why（来自用户），How 简写为规则 + 代码锚点。

---

## 方法论（摘要）

完整方法论见 [references/methodology.md](references/methodology.md)。

### 核心方法：模型探索漩涡

在澄清任何概念时，使用迭代循环：浮现 → 探查 → 挑战 → 精炼 → 验证 → 循环。通过强制在接受用户回答前寻找矛盾证据，防止肤浅的"是的，没错"确认。

### 模糊性处理：STOP vs ASSUME

| 等级 | 标准 | 行为 |
|:---|:---|:---|
| **STOP** | 错了 → 跨步骤/跨 phase 返工 | 立即问用户；一次一问；不继续 |
| **ASSUME & RECORD** | 错了 → 只修复当前工件 | 选最保守选项，记录到 draft，继续 |

### 临时文件与闭环删除

- 代码信号 + 推断 → `draft/inferences-draft.md`
- 假设 → `draft/assumptions-draft.md`
- 提问记录 → `draft/questions-log.md`
- 闭环时：评审假设 → 确认推断落定 → 删除整个 `docs/draft/`

---

## 实现步骤

### Step 0：全局意图对齐

> 代码目录可能不规范，单纯靠目录推断 BC 会偏。先用项目内文档 + 用户提问了解全局业务意图，后续所有扫描都带着这个意图去校准解读。

1. **读取项目内已有文档**（工程文档，非逆向产物）：`AGENTS.md`、`README.md`、架构说明等。**不读** `docs/` 下的逆向产物。
2. **提取文档声明的全局意图**，记录到 `draft/inferences-draft.md` 的信号区。
3. **一次一问，与用户对齐全局意图**：先问"这个项目最重要的业务价值是什么？"，再追问能力域划分。

> Step 0 的产出**不直接写入产物文件**。全局意图在 Step 2（context-map.md）的"领域愿景声明"中落定为产物。

### Step 1：建立代码图谱 + 检测项目结构

1. **检测代码结构查询模式**：检查 graphify 图谱是否已构建。在 `draft/inferences-draft.md` 标注使用的模式。
2. **识别项目语言与构建系统**。
3. **带着 Step 0 的全局意图扫描代码目录**。
4. **扫描候选目录**，生成目录映射写入 `draft/inferences-draft.md` 的信号区。
5. **对比文档意图 vs 代码结构**：记录差异作为 Step 2 的提问素材。
6. **STOP — 提一个边界确认问题。**

### Step 2-7：业务约束（DDD）

详见 [references/business/ddd.md](references/business/ddd.md)。每个 Step 的产出：

| Step | 产出 | 模板 |
|------|------|------|
| 2 | `docs/context-map.md` | [templates/business/context-map.md](templates/business/context-map.md) |
| 3 | 各 BC `business-flow.md` | [templates/business/business-flow.md](templates/business/business-flow.md) |
| 4 | 各 BC `contracts.md` | [templates/business/contracts.md](templates/business/contracts.md) |
| 5 | 各 BC `domain-events.md` | [templates/business/domain-events.md](templates/business/domain-events.md) |
| 6 | 各 BC `domain-model.md` | [templates/business/domain-model.md](templates/business/domain-model.md) |
| 7 | 各 BC `invariants.md` | [templates/business/invariants.md](templates/business/invariants.md) |

### Step 8：技术约束

| Step | 产出 | 模板 |
|------|------|------|
| 8 | 全局 `docs/technical-constraints.md` + 各 BC `docs/features/<bc>/technical-constraints.md` | [templates/technical/technical-constraints.md](templates/technical/technical-constraints.md)（全局与 BC 级复用同一模板） |

### Step 9：闭环

| Step | 产出 | 模板 |
|------|------|------|
| 9 | 各 BC `index.md` + AGENTS.md 更新 | [templates/bc-index.md](templates/bc-index.md) |

1. 将所有产物汇总呈现给用户做**最终通读**。
2. 评审 `draft/assumptions-draft.md`：每条假设 ✅ 确认 | ✏️ 纠正 | ❌ 拒绝。
3. 评审 `draft/inferences-draft.md`：确认所有推断已转为产物结论或被否决。
4. **确认所有产物匿名审查报告（`draft/audit-*.md`）结论为 PASS**——任何 FAIL 的产物已修正并重审通过。
5. 生成各 BC `index.md`。
6. **更新 AGENTS.md**：在项目根目录的 AGENTS.md 中追加/更新知识库指引段落（见下文"AGENTS.md 追加协议"）。
7. **删除 `docs/draft/` 整个目录**（含 `inferences-draft.md`、`assumptions-draft.md`、`questions-log.md`、`audit-*.md`）。

**检查点：** "所有产物已定稿。临时工作区已删除。知识库已注册到 AGENTS.md。知识库现为唯一权威。"

#### AGENTS.md 追加协议

skill 闭环时自动在项目根目录的 `AGENTS.md` 中追加知识库指引段落，让后续 AI 知道知识库存在并知道如何加载。

**追加规则：**
- **幂等**：先检查 AGENTS.md 中是否包含章节`本地知识使用指南`，有则跳过，无则追加
- **只追加不覆盖**：不修改用户已有的 AGENTS.md 内容

**追加内容格式：**（花括号变量需要填充）

## 本地知识使用指南

{微服务简介}

### 必读：业务地图

每次会话开始时直接读取以下文件，建立业务心智模型——graphify 图谱无法提供：
- `docs/context-map.md` — 业务地图：限界上下文（BC）边界、BC 关系、统一语言术语表
- `docs/technical-constraints.md` — 全局技术约束：跨所有 BC 适用的技术选型理由 + 编码规范 + 合规约束，编码场景应该加载。

### BC 级产物清单（解释性，按需加载）

下表说明各 BC 级 `.md` 文件承载什么内容。是否读取、读取哪个，由 AI 在 graphify query 返回结果后自主判断——本清单不做触发式加载条件。

| 文件 | 承载内容 |
|------|---------|-----------------------------------|
| `docs/features/<bc>/technical-constraints.md` | 该 BC 特有的技术选型理由 + 编码规范 |
| `docs/features/<bc>/business-flow.md` | 关键业务用例时序编排（含周期任务/外部触发入口）+ 失败/补偿矩阵 |
| `docs/features/<bc>/invariants.md` | 业务不变式（违反即业务状态非法） |
| `docs/features/<bc>/contracts.md` | 接口业务承诺（前置/后置/失败语义）+ 跨 BC 契约定位符 |
| `docs/features/<bc>/domain-events.md` | 业务状态变更事件 | 理解业务状态转换 |
| `docs/features/<bc>/domain-model.md` | 聚合协作视图 + 边界 + 状态机 + 行为归属 |
| `docs/features/<bc>/apis/*.feature` | 基于 karate 语法的规格用例（可选） |

> graphify query 返回 `doc-anchor` 节点时，其 `filePath` 会指向上表中的文件——这是 AI 判断是否需要进一步读取以获取完整业务语境（WHY/RULES/REASONS）的信号之一，非强制。

---

## 会话恢复

1. 检查 `docs/` 下产物 + `docs/draft/` 临时文件
2. **产物 + 临时文件都存在** → 读 `draft/questions-log.md` 确认对话进度，从下一个待问问题恢复
3. **只有产物、无 draft** → 闭环已完成，按需加载产物即可
4. **无产物** → 从 Step 0 开始
5. **工程文档 vs 逆向产物**：Step 0 读的是 AGENTS.md/README 等工程文档；`docs/features/` 等是逆向产物。恢复时区分两者。

---

## 自检协议

每个 Step 完成后、进入下一步前，必须执行：

1. **产物干净**：该 step 的产物文件不含 file:line、代码段粘贴、中间态标记、填写指引 blockquote、自检章节。允许引用包名/类名/方法名/端点路径/表名等代码锚点
2. **临时留痕**：代码信号 + 推断在 `draft/inferences-draft.md`，假设在 `draft/assumptions-draft.md`，提问在 `draft/questions-log.md`
3. **一次一问**：本轮对话每次只问了一个问题
4. **无虚泛内容**：无"待实现"/"后续补充"等虚泛描述
5. **无通用常识**：产物中无显而易见的通用知识（语言/框架通用实践、协议约定、安全常识、模式定义等）；记录的是项目特有决策 + WHY，不是通用真理（见核心原则"反模式"）
6. **Step 0 校准**（Step 1 起）：代码扫描带着全局意图进行
7. **行为归属**（Step 6 起）：有领域行为时识别贫血/充血，贫血模型已追踪外部 Service 的业务行为；无领域行为的 BC 已跳过行为归属章节（不保留空内容）
8. **约束由来来自用户**（Step 8）：约束的"为什么这么定"来自用户确认；不知道的标 UNKNOWN
9. **表格优先**：简单业务表格足矣，仅复杂场景展开详情子节；标注"可选"的章节无实际内容时已删除整个章节，不保留空表格、空描述或占位符
10. **AGENTS.md 已更新**（Step 9）：知识库指引段落已追加/更新到 AGENTS.md
11. **表格标签**（白名单产物）：每张表要么三个标签全有（`<anchor:ddd>` + `<anchor:code>` + `<anchor:desc>`），要么三个标签全无。`<anchor:ddd>` 列必须是表唯一键且内容为**业务术语**（非代码类名、非 ID；特例：代码类名本身就是术语时可使用类名）。`<anchor:code>` 仅支持三类格式（`类名` / `类名.函数名` / `HTTP方法:/路径`）。白名单：business-flow / invariants / contracts / domain-events / domain-model。豁免：context-map / technical-constraints / index.md / domain-model 中的行为归属表。校验脚本：`scripts/check_ddd_anchors.py`
12. **匿名审查通过**（Step 2-8 每个产物产出后）：产物文件已派发给匿名 subAgent 审查（见 [references/audit-prompt.md](references/audit-prompt.md)），审查报告写入 `docs/draft/audit-{产物文件名}.md`，结论为 PASS（❌ 违规数=0）。FAIL（❌>0）→ STOP，修正产物后重审，不得进入下一步

**任何检查失败 → STOP。修正。不进入下一步。**
