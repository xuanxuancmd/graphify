# 业务流程 — 用户管理

## 用例: 用户注册

**用例 ID**: UC-01-01

### 入口点

| 用例入口<anchor:ddd> | 入口类型 | 代码锚点<anchor:code> | 业务触发<anchor:desc> |
|---------|---------|---------|---------|
| 注册 | 应用服务 | `AuthService.register` | 新用户通过注册表单提交邮箱和密码 |

### 时序编排

| 步骤 | 业务动作<anchor:ddd> | 代码锚点<anchor:code> | 核心角色 / BC | 业务理由（WHY）<anchor:desc> |
|------|---------|---------|-------------|--------------|
| 1 | 检查邮箱唯一性 | `UserRepository.findByEmail` | BC-01 | 防止重复注册 |
| 2 | 哈希密码 | `PasswordHasher.hash` | BC-02 | 密码不可明文存储 |
| 3 | 创建用户 | `User.register` | BC-01 | 通过工厂方法保证注册不变式 |
| 4 | 持久化用户 | `UserRepository.save` | BC-01 | 保存到数据存储 |
| 5 | 签发令牌 | `JwtManager.generateToken` | BC-02 | 注册成功后自动登录 |

### 失败/补偿矩阵

| 失败点<anchor:ddd> | 代码锚点<anchor:code> | 失败的业务后果 | 补偿动作 | 恢复原状态？ | 业务理由<anchor:desc> |
|--------|---------|--------------|---------|:-----------:|---------|
| 邮箱已注册 | `UserRepository.findByEmail` | 用户未创建，无副作用 | 返回错误提示 | 是 | 无需补偿，注册未执行 |
| 持久化失败 | `UserRepository.save` | 用户对象已创建但未存储 | 无 | 是 | 内存中的用户对象会被 GC，无残留 |

## 用例: 用户登录

**用例 ID**: UC-01-02

### 入口点

| 用例入口<anchor:ddd> | 入口类型 | 代码锚点<anchor:code> | 业务触发<anchor:desc> |
|---------|---------|---------|---------|
| 登录 | 应用服务 | `AuthService.login` | 已注册用户提交邮箱和密码进行身份验证 |

### 时序编排

| 步骤 | 业务动作<anchor:ddd> | 代码锚点<anchor:code> | 核心角色 / BC | 业务理由（WHY）<anchor:desc> |
|------|---------|---------|-------------|--------------|
| 1 | 按邮箱查询用户 | `UserRepository.findByEmail` | BC-01 | 定位用户记录 |
| 2 | 检查用户状态 | `AuthService.login` | BC-02 | 挂起或删除的用户不允许登录 |
| 3 | 验证密码 | `PasswordHasher.verify` | BC-02 | 验证用户身份 |
| 4 | 签发令牌 | `JwtManager.generateToken` | BC-02 | 返回访问凭证 |

### 失败/补偿矩阵

| 失败点<anchor:ddd> | 代码锚点<anchor:code> | 失败的业务后果 | 补偿动作 | 恢复原状态？ | 业务理由<anchor:desc> |
|--------|---------|--------------|---------|:-----------:|---------|
| 用户不存在 | `UserRepository.findByEmail` | 无副作用 | 返回认证失败 | 是 | 不泄露用户是否存在 |
| 密码错误 | `PasswordHasher.verify` | 无副作用 | 返回认证失败 | 是 | 不泄露具体失败原因 |
| 用户已挂起 | `AuthService.login` | 无副作用 | 返回账户状态错误 | 是 | 提示用户联系管理员 |
