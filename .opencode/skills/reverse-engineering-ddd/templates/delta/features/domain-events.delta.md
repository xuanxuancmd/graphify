# DDD Delta — 业务事件 — {BC 名称}

> 模式二（`--changes`）产物。记录本次变更新增/修改/删除的业务事件。
> 格式规范见 [references/incremental-merge.md](../../references/incremental-merge.md)。

## ADDED

### 业务事件表

| 领域事件<anchor:ddd> | 代码锚点<anchor:code> | 触发命令 | 业务触发场景<anchor:desc> | 参与者 | 载荷业务含义 | 失败/补偿语义 |
|--------|---------|---------|------------|--------|------------|-------------|
| {EventName} | `{ClassName}.{method}` | {CommandName} | {什么业务情况下触发} | {用户/系统/BC} | {事件携带什么业务信息} | {补偿事件及语义，无则—} |

## MODIFIED

### 业务事件表

| 领域事件<anchor:ddd> | 代码锚点<anchor:code> | 触发命令 | 业务触发场景<anchor:desc> | 参与者 | 载荷业务含义 | 失败/补偿语义 |
|--------|---------|---------|------------|--------|------------|-------------|
| {EventName} | `{ClassName}.{method}` | {修改后的触发命令} | {修改后的触发场景} | {参与者} | {修改后的载荷含义} | {修改后的补偿语义} |

## REMOVED

### 业务事件表

| 领域事件 |
|--------|
| {EventName} |

## RENAMED

### 业务事件表

| 旧事件名 | 新事件名 |
|----------|----------|
| {OldEventName} | {NewEventName} |
