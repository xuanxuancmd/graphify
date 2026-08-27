# 用户管理 — 限界上下文索引

## 概要

- **分类**: 核心域
- **代码根**: `src/models`, `src/repositories`, `src/services`
- **业务价值**: 管理用户身份、档案与生命周期——系统的核心身份管理能力

## 关键概念

- 用户: 系统中的注册身份，含邮箱、密码哈希、档案和状态
- 档案: 用户的展示信息（昵称、头像、简介），不可变值对象
- 用户状态: active / suspended / deleted，控制登录和操作权限

## 工件链接

### 业务约束

| 工件 | 用途 | 摘要 | 链接 |
|------|------|------|------|
| 业务流程 | 跨 BC 时序编排 + 失败/补偿矩阵 | 2 个用例 | [business-flow.md](./business-flow.md) |
| 业务不变式 | 判断什么必须永远为真 | 4 条不变式 | [invariants.md](./invariants.md) |
| 契约 | 接口业务语义 + 端点归属 | 5 个契约 | [contracts.md](./contracts.md) |
| 业务事件 | 业务状态转换 | 6 个事件 | [domain-events.md](./domain-events.md) |
| 聚合协作 | 聚合协作 + 行为归属 | 1 聚合, 1 值对象, 1 领域服务 | [domain-model.md](./domain-model.md) |

### 技术约束（BC 特有）

| 规则 | 摘要 | 链接 |
|------|------|------|
| 聚合根 + 值对象 | User 充血模型，Profile 不可变 | [../technical-constraints.md](../technical-constraints.md) |
| 仓储模式 | 领域层不直接操作存储 | [../technical-constraints.md](../technical-constraints.md) |

## 跨 BC 关系

| 方向 | 对端 BC | 关系类型 | 同步/异步 | 业务含义 |
|------|---------|---------|:---------:|---------|
| 入站 | 认证 (BC-02) | 客户-供应商 | 同步 | 认证依赖用户管理的查询和持久化承诺 |
