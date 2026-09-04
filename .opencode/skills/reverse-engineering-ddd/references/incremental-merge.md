# 增量合并算法参考

> 模式二（`--changes`）Step 4 合并 DDD delta 到 baseline 时加载。
> 借鉴 OpenSpec 的 delta 合并算法（RENAMED → REMOVED → MODIFIED → ADDED + 未提及即保留），适配 DDD 表格行级合并。

---

## §1 Delta 文件格式

### 1.1 顶层区段

每个 delta 文件用四个区段标记操作类型，**按需使用，无内容的区段省略**：

```markdown
# DDD Delta — {产物名} — {BC 名称 / 全局}

## ADDED

### {baseline section 名}
（新增的表格行或 TC 条目）

## MODIFIED

### {baseline section 名}
（修改的表格行——必须携带完整行，含未变更的列）

## REMOVED

### {baseline section 名}
（要删除的行标识——ID 或唯一键）

## RENAMED

### {baseline section 名}
（术语改名——ID + 旧术语 + 新术语）
```

### 1.2 区段语义

| 区段 | 语义 | 表格行格式 | 匹配键 |
|------|------|-----------|--------|
| `## ADDED` | 新增条目 | 完整行（含 ID） | ID 不应在 baseline 存在 |
| `## MODIFIED` | 修改既有条目 | **完整行**（含所有列，含未变更列） | ID 必须在 baseline 存在 |
| `## REMOVED` | 删除条目 | 仅 ID 列 | ID 必须在 baseline 存在 |
| `## RENAMED` | 术语改名 | ID + 旧术语 + 新术语 | ID 必须在 baseline 存在 |

> **MODIFIED 必须携带完整行**——防止"半截修改"丢失列数据。这是借鉴 OpenSpec "MODIFIED 必须复制完整 requirement 块" 的设计。合并时用完整行替换 baseline 中匹配 ID 的行。

### 1.3 `### {section 名}` 对应 baseline 结构

delta 中的 `### {section 名}` 对应 baseline 产物的 section 标题（去掉 `##` 前缀和序号）。例如：

| baseline section | delta `###` 子标题 |
|------------------|-------------------|
| `## 1. 聚合根` | `### 聚合根` |
| `## 2. 领域实体` | `### 领域实体` |
| `## 1. 业务实现技术` | `### 业务实现技术`（technical-constraints 用 TC ID 组织，见 §4） |

---

## §2 合并顺序

**固定顺序：RENAMED → REMOVED → MODIFIED → ADDED**

### 为什么是这个顺序

1. **RENAMED 先做**——术语改名后，后续 MODIFIED 能用新术语定位条目（虽然实际匹配用 ID，但改名可能影响 desc 字段的一致性校验）
2. **REMOVED 次之**——删掉的条目不参与后续匹配
3. **MODIFIED 再做**——用完整行替换既有行
4. **ADDED 最后**——新增条目追加到对应表格末尾

### 幂等性

若 delta 的 ADDED 条目与 baseline 已有条目**内容完全一致**（规范化后）→ no-op，不报错。防止重复刷新同一变更。

> 这借鉴 OpenSpec 的 early-sync pattern——若 delta 已被部分合并到 baseline（如手动编辑），重复合并不应报错。

---

## §3 合并策略：未提及即保留

### 核心原则

合并不是"覆盖文件"，而是**结构化切片重建**：

1. 解析 baseline 产物为结构化切片：preamble（标题+说明）→ sections → 每个 section 内的表格（header + rows）
2. 对每个 section，按 RENAMED → REMOVED → MODIFIED → ADDED 顺序应用 delta 操作
3. **delta 没提到的 section、行、段落 → 原样保留，顺序不变**
4. 新增行追加到对应表格末尾
5. 重组为完整的 baseline 文件

### 表格行级合并

以 `domain-model.md` 的"聚合根"表为例：

**baseline**：
```
| ID | 聚合根 | 代码锚点 | 持久化表 | 业务职责 | 业务入口概念？ |
| AG-01 | 订单 | `Order` | `orders` | 管理订单生命周期 | 是 |
| AG-02 | 商品 | `Product` | `products` | 管理商品信息 | 否 |
```

**delta**（MODIFIED AG-01 + ADDED AG-03）：
```
## MODIFIED

### 聚合根
| ID | 聚合根 | 代码锚点 | 持久化表 | 业务职责 | 业务入口概念？ |
| AG-01 | 订单 | `Order` | `orders` | 管理订单全生命周期（含退款） | 是 |

## ADDED

### 聚合根
| ID | 聚合根 | 代码锚点 | 持久化表 | 业务职责 | 业务入口概念？ |
| AG-03 | 退款单 | `Refund` | `refunds` | 管理退款流程 | 是 |
```

**合并结果**（AG-02 未提及，保留；AG-01 替换；AG-03 追加）：
```
| AG-01 | 订单 | `Order` | `orders` | 管理订单全生命周期（含退款） | 是 |
| AG-02 | 商品 | `Product` | `products` | 管理商品信息 | 否 |
| AG-03 | 退款单 | `Refund` | `refunds` | 管理退款流程 | 是 |
```

### prose 类产物合并

`context-map.md` 的"领域愿景声明"和 `technical-constraints.md` 的 TC 条目是半结构化 prose/列表，不能按表格行合并。策略：

- **context-map.md 领域愿景声明**：delta 的 `## MODIFIED` 下放完整新段落，整体替换
- **technical-constraints.md TC 条目**：按 TC ID（如 TC-001）匹配，ADDED 追加到对应 section 末尾，MODIFIED 整条替换，REMOVED 删除整条

---

## §4 各产物类型的合并规则

### 4.1 表格类产物（白名单产物）

| 产物 | section 划分 | 匹配键 | 特殊处理 |
|------|-------------|--------|----------|
| `business-flow.md` | 每个用例（`## 用例: {名称}`）是一个 section，用例内的"入口点/时序编排/失败补偿"是子表 | 用例 ID（UC-{xx}-{yy}）；表内行按业务术语列匹配 | 用例整体 ADDED/REMOVED 时，整块新增/删除 |
| `invariants.md` | 整个"不变式目录"一个 section | ID（INV-NNN） | — |
| `contracts.md` | "跨 BC 契约"一个 section；"BC 内契约"每个 `### C-00X` 一个条目 | 跨 BC 契约按契约 ID（C-{xx}-{yy}）；BC 内契约按 TC ID（C-00X） | BC 内契约 ADDED 时追加到文件末尾 |
| `domain-events.md` | 整个事件表一个 section | 领域事件名（`<anchor:ddd>` 列值） | — |
| `domain-model.md` | 6 个 section（聚合根/领域实体/值对象/协作视图/状态机/领域服务），每个 section 独立合并 | ID（AG/EN/VO/DS-NNN）；协作视图按业务术语；状态机按"源状态→目标状态" | 行为归属表豁免标签，但同样支持 ADDED/MODIFIED/REMOVED |

### 4.2 索引类产物（豁免锚点校验）

| 产物 | 合并方式 |
|------|----------|
| `context-map.md` | BC 清单按 BC ID 匹配；关系表按"从+到"匹配；统一语言按"术语"匹配；领域愿景声明整体替换 |
| `index.md` | 合并后重新生成（从其他产物汇总摘要），不做 delta 合并 |

### 4.3 列表式产物

| 产物 | 合并方式 |
|------|----------|
| `technical-constraints.md` | 按 TC ID（TC-NNN）匹配；ADDED 追加到对应 section 末尾；MODIFIED 整条替换；REMOVED 删除整条 |

---

## §5 合并前校验（硬失败条件）

合并前对 delta 做**静态校验**，以下任一条件触发 → STOP，不执行合并：

### 5.1 跨区段冲突

同一个 ID 不能同时出现在多个区段：

| 冲突 | 说明 |
|------|------|
| MODIFIED + REMOVED 同一 ID | 不能既修改又删除 |
| ADDED + MODIFIED 同一 ID | 不能既新增又修改 |
| ADDED + REMOVED 同一 ID | 不能既新增又删除 |
| RENAMED + REMOVED 同一 ID | 改名后又被删除——逻辑矛盾 |

### 5.2 匹配失败

| 条件 | 说明 |
|------|------|
| MODIFIED 的 ID 在 baseline 不存在 | 无法替换——可能 baseline 已被其他变更修改，或 delta 引用了过时快照 |
| REMOVED 的 ID 在 baseline 不存在 | 无法删除——同上 |
| RENAMED 的 ID 在 baseline 不存在 | 无法改名——同上 |
| ADDED 的 ID 在 baseline 已存在（且内容不同） | 真冲突，不是幂等——需人工确认 |

### 5.3 MODIFIED 完整性

MODIFIED 的行必须包含 baseline 中该条目的**所有列**。缺少列 → STOP（防止"半截修改"丢数据）。

---

## §6 合并后验证

合并完成后，对合并后的 baseline 执行验证：

1. **锚点格式校验**：运行 `python scripts/check_ddd_anchors.py --docs-root docs/`，校验表格标签和锚点格式
2. **锚点真实性审查**：派发匿名 subAgent（复用 [audit-prompt.md](audit-prompt.md)），审查合并后 baseline 中的代码锚点是否在代码库真实存在——重点审查 delta ADDED/MODIFIED 引入的新锚点
3. **delta 完整性校验**：确认 delta 中所有条目都已合并到 baseline（ADDED 的在 baseline 中存在、MODIFIED 的内容已更新、REMOVED 的已消失、RENAMED 的术语已更新）

任一验证失败 → STOP，修正后重验。

---

## §7 跨变更冲突处理

### 7.1 冲突检测

当多个未归档的 change 的 delta 指向**同一 baseline 产物**时 → 冲突。检测粒度是**产物文件级**（如 `features/<bc>/invariants.md`），不是行级。

### 7.2 冲突解决

借鉴 OpenSpec bulk-archive 的 agentic resolution：

1. AI 查代码库判断哪个 change 的代码真落地了
2. 只有一个落地 → 只合并那个的 delta
3. 两个都落地 → 按时间顺序合并（老的先，新的后覆盖）
4. 两个都没落地 → 跳过，警告用户

### 7.3 per-delta 决策

一个 change 可能部分 delta 合并、部分跳过（如 change A 的 invariants delta 合并了，但 contracts delta 因冲突被跳过）。决策粒度到**单个产物文件**。

---

## §8 合并执行者

### 8.1 Agent 驱动合并（主）

AI 读 delta + baseline，按本文件的算法指引执行合并。合并前做 §5 校验，合并后做 §6 验证。每次合并需用户确认。

### 8.2 脚本校验（辅）

`scripts/check_ddd_anchors.py --delta` 做合并前校验：检查 delta 文件的表格标签、锚点格式、跨区段冲突。不执行合并本身。

---

## §9 反模式

| 借口 | 现实 |
|:------|:------|
| "delta 太麻烦，直接改 baseline 文件" | 直接改 baseline 丢失变更追溯，无法审计"为什么改"。delta 是变更的审计记录 |
| "MODIFIED 只写变更的列就行" | 只写变更列会丢失未变更列的数据。MODIFIED 必须携带完整行 |
| "合并后不用验证，delta 写对了就行" | delta 写对了不代表合并对了。合并可能引入格式错误、锚点失效。必须跑校验 + 审查 |
| "多个 change 的 delta 一起合并更快" | 跨变更冲突需要逐个解决。批量合并可能覆盖彼此的变更 |
| "技术约束 delta 和业务约束 delta 一起合并" | 技术约束 delta 在编码后才补充。业务约束 delta 在编码前就位。两者合并时机不同，不能一起合并 |
| "delta 合并后就可以删了" | delta 随 change 归档保留，是审计轨迹。删除则丢失"为什么这样改"的历史 |
