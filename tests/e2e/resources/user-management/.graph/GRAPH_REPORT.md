# Graph Report - user-management  (2026-08-27)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 235 nodes · 362 edges · 19 communities (13 shown, 6 thin omitted)
- Extraction: 91% EXTRACTED · 6% INFERRED · 3% AMBIGUOUS · INFERRED: 22 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e0b2be77`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10
- Community 11
- Community 13
- Community 14
- Community 15
- Community 16
- Community 17
- Community 18

## God Nodes (most connected - your core abstractions)
1. `User` - 27 edges
2. `UserService` - 19 edges
3. `buildApp()` - 18 edges
4. `UserRepository` - 16 edges
5. `AuthService` - 14 edges
6. `JwtManager` - 14 edges
7. `AuthController` - 13 edges
8. `PasswordHasher` - 10 edges
9. `1. 业务实现技术` - 10 edges
10. `Logger` - 9 edges

## Surprising Connections (you probably didn't know these)
- `聚合根不变式` --references--> `User`  [AMBIGUOUS]
  docs/features/user-management/invariants.md → src/models/user.ts
- `日志不变式` --references--> `Logger`  [AMBIGUOUS]
  docs/features/user-management/invariants.md → src/utils/logger.ts
- `日志不变式` --references--> `Logger`  [AMBIGUOUS]
  docs/features/user-management/invariants.md → src/middleware/request-logger.ts
- `分层架构` --references--> `AuthController`  [EXTRACTED]
  docs/technical-constraints.md → src/auth/auth.controller.ts
- `聚合根 + 值对象模式` --references--> `User`  [EXTRACTED]
  docs/technical-constraints.md → src/models/user.ts

## Import Cycles
- None detected.

## Communities (19 total, 6 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.07
Nodes (32): 用户管理, 认证, 创建用户, 持久化失败, 持久化用户, 按邮箱查询用户, 检查邮箱唯一性, 用户不存在 (+24 more)

### Community 1 - "Community 1"
Cohesion: 0.09
Nodes (21): 检查用户状态, 注册, 用户已挂起, 登录, 签发令牌, 令牌刷新端点, 注册端点, 登录端点 (+13 more)

### Community 2 - "Community 2"
Cohesion: 0.15
Nodes (13): 档案, AuthResult, JwtManager, TokenPayload, PasswordHasher, AppConfig, buildApp(), defaultConfig (+5 more)

### Community 3 - "Community 3"
Cohesion: 0.07
Nodes (21): BC 内契约, C-001: 注册, C-002: 登录, 契约 — 用户管理, 跨 BC 契约, 业务事件 — 用户管理, 1. 聚合根, 2. 领域实体 (+13 more)

### Community 4 - "Community 4"
Cohesion: 0.10
Nodes (19): 1.1 设计模式, 1.2 算法选择, 1.3 架构模式, 1.4 安全模型, 1. 业务实现技术, 2.1 错误处理, 2.2 日志/可观测性, 2.3 测试规范 (+11 more)

### Community 5 - "Community 5"
Cohesion: 0.17
Nodes (11): src, compilerOptions, declaration, esModuleInterop, module, moduleResolution, outDir, skipLibCheck (+3 more)

### Community 6 - "Community 6"
Cohesion: 0.18
Nodes (8): 认证, 哈希密码, 密码错误, 验证密码, 用户查询承诺, 密码最短8字符, 密码哈希算法, JWT 令牌认证

### Community 7 - "Community 7"
Cohesion: 0.24
Nodes (3): 日志不变式, Logger, Logger

### Community 8 - "Community 8"
Cohesion: 0.20
Nodes (9): description, devDependencies, typescript, name, scripts, build, type, version (+1 more)

### Community 9 - "Community 9"
Cohesion: 0.22
Nodes (9): 业务流程 — 用户管理, 入口点, 入口点, 失败/补偿矩阵, 失败/补偿矩阵, 时序编排, 时序编排, 用例: 用户注册 (+1 more)

### Community 10 - "Community 10"
Cohesion: 0.29
Nodes (6): 1. 限界上下文, 2.1 对外契约文件清单, 2. 业务关系, 3. 统一语言, 4. 领域愿景声明, 上下文图 — User Management System

### Community 11 - "Community 11"
Cohesion: 0.40
Nodes (4): Bounded Contexts, Purpose, Structure, User Management Test Project

## Ambiguous Edges - Review These
- `.handleRegister()` → `业务异常用 Error 抛出`  [AMBIGUOUS]
  docs/technical-constraints.md · relation: references
- `.generateToken()` → `签发令牌`  [AMBIGUOUS]
  docs/features/user-management/business-flow.md · relation: references
- `.generateToken()` → `JWT 令牌认证`  [AMBIGUOUS]
  docs/technical-constraints.md · relation: references
- `Logger` → `日志不变式`  [AMBIGUOUS]
  docs/features/user-management/invariants.md · relation: references
- `User` → `聚合根不变式`  [AMBIGUOUS]
  docs/features/user-management/invariants.md · relation: references
- `.findByEmail()` → `按邮箱查询用户`  [AMBIGUOUS]
  docs/features/user-management/business-flow.md · relation: references
- `.findByEmail()` → `检查邮箱唯一性`  [AMBIGUOUS]
  docs/features/user-management/business-flow.md · relation: references
- `.findByEmail()` → `用户不存在`  [AMBIGUOUS]
  docs/features/user-management/business-flow.md · relation: references
- `.findByEmail()` → `邮箱已注册`  [AMBIGUOUS]
  docs/features/user-management/business-flow.md · relation: references
- `.findByEmail()` → `用户查询承诺`  [AMBIGUOUS]
  docs/features/user-management/contracts.md · relation: references
- `Logger` → `日志不变式`  [AMBIGUOUS]
  docs/features/user-management/invariants.md · relation: references

## Knowledge Gaps
- **101 isolated node(s):** `HttpRequest`, `HttpResponse`, `name`, `version`, `type` (+96 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `.handleRegister()` and `业务异常用 Error 抛出`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `.generateToken()` and `签发令牌`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `.generateToken()` and `JWT 令牌认证`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `Logger` and `日志不变式`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `User` and `聚合根不变式`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `.findByEmail()` and `按邮箱查询用户`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `.findByEmail()` and `检查邮箱唯一性`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._