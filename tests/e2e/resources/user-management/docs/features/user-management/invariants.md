# 业务不变式 — 用户管理

## 不变式目录

| ID | 业务不变式<anchor:ddd> | 代码锚点<anchor:code> | 业务理由<anchor:desc> | 违反后果 |
|----|--------|---------|---------|---------|
| INV-001 | 邮箱全局唯一 | `UserRepository.save` | 同一邮箱不能注册多个用户，保证身份唯一性 | 注册时抛出异常，阻止重复注册 |
| INV-002 | 密码最短8字符 | `PasswordHasher.hash` | 降低暴力破解风险，符合基本安全要求 | 哈希时抛出异常，拒绝弱密码 |
| INV-003 | 已删除用户不可操作 | `User.changePassword` | 软删除后的用户不能修改密码或档案，保留审计快照 | 抛出异常，操作被拒绝 |
| INV-004 | 只有活跃用户可被挂起 | `User.suspend` | 已挂起或已删除的用户不能再次挂起 | 抛出异常，状态转换非法 |
| INV-005 | 聚合根不变式 | `com.example.User` | 全限定名锚点: 验证路径消歧匹配 (Gap-6) | 路径不匹配 → AMBIGUOUS |
| INV-006 | 日志不变式 | \Logger\ | Logger 实例全局唯一 (多匹配: src/utils + src/middleware) | AMBIGUOUS |
