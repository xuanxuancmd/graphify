# DDD Delta — 技术约束 — {系统名称（全局） / BC 名称（BC 级）}

> 模式二（`--changes`）产物。记录本次变更新增/修改/删除的技术约束。
> 通常在编码后回刷阶段（Step 3）填写——技术选型理由需从代码 diff + 用户确认获得。
> 格式规范见 [references/incremental-merge.md](../../references/incremental-merge.md)。
> 按 TC ID 匹配；ADDED 追加到对应 section 末尾；MODIFIED 整条替换。

## ADDED

### {section 名——如 设计模式 / 算法选择 / 架构模式 / 并发模型 / 安全模型 / 高可靠设计 / trade-off 优先级 / 错误处理 / 日志/可观测性 / 测试规范 / 命名规范 / 依赖与禁止项 / 兼容性约束}

### TC-{NNN}: {技术选型名称}
- **选型理由（Why）**: {为什么选这个——业务约束驱动、替代方案考虑、踩坑经验。来自用户确认，不知道标 UNKNOWN}
- **实现规则**: {必须/禁止/应该……}
- **代码锚点**: `{类名/方法名/配置路径}` —— 可选
- **适用范围**: 全局 / {BC 名称}

## MODIFIED

### {section 名}

### TC-{NNN}: {修改后的技术选型名称}
- **选型理由（Why）**: {修改后的理由}
- **实现规则**: {修改后的规则}
- **代码锚点**: `{……}` —— 可选
- **适用范围**: {……}

## REMOVED

### {section 名}

| TC ID |
|-------|
| TC-{NNN} |

## RENAMED

> 技术约束的 RENAMED 指 TC 条目的标题改名（`### TC-NNN: {标题}`），不涉及 `<anchor:ddd>` 列（technical-constraints 豁免锚点校验）。

### {section 名}

| TC ID | 旧标题 | 新标题 |
|-------|--------|--------|
| TC-{NNN} | {旧技术选型名称} | {新技术选型名称} |
