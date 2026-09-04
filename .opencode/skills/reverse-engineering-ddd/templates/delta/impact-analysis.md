# 影响分析报告 — {变更名称}

> 本文件由匿名 subAgent 在模式二 Step 0 产出（提示词模板见 [references/impact-analysis-prompt.md](../../references/impact-analysis-prompt.md)）。
> 主 Agent 读取本报告后决定刷新范围，不直接读取原始变更文件和 git log。
> 本报告随 change 归档保留，作为审计轨迹。

---

## 变更意图摘要

{从变更目录的 proposal/design 中提取的业务意图，2-3 句话}

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

| BC | 已有 delta | 需新增 delta | 涉及产物 | 刷新阶段 |
|---|---|---|---|---|
| {BC名} | {产物列表或无} | {产物列表} | {business-flow/invariants/...} | 业务约束(编码前) / 技术约束(编码后) / 两者 |

## 变更目录文件分类

| 文件路径 | 分类 | 内容摘要 |
|---|---|---|
| {path} | proposal/design/tasks/spec delta/ddd delta/其他 | {一句话} |

## delta 与代码一致性

| DDD 产物 | delta 声明 | 代码证据 | 一致性 |
|---|---|---|---|
| {BC}/{产物} | {delta 描述的变更} | {代码实际变更} | 一致 / delta有代码无 / 代码有delta无 |

## 建议的刷新范围

### 业务约束类（编码前刷新）

- {BC}/{产物}: {一句话说明需要刷新什么}

### 技术约束类（编码后回刷）

- {BC}/{产物}: {一句话说明需要回刷什么}
