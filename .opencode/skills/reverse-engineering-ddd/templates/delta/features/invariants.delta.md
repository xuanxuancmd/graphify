# DDD Delta — 业务不变式 — {BC 名称}

> 模式二（`--changes`）产物。记录本次变更新增/修改/删除的业务不变式。
> 格式规范见 [references/incremental-merge.md](../../references/incremental-merge.md)。

## ADDED

### 不变式目录

| ID | 业务不变式<anchor:ddd> | 代码锚点<anchor:code> | 业务理由<anchor:desc> | 违反后果 |
|----|--------|---------|---------|---------|
| INV-{NNN} | {规则陈述} | `{ClassName}.{method}` | {为什么必须为真} | {业务上意味着什么} |

## MODIFIED

### 不变式目录

| ID | 业务不变式<anchor:ddd> | 代码锚点<anchor:code> | 业务理由<anchor:desc> | 违反后果 |
|----|--------|---------|---------|---------|
| INV-{NNN} | {修改后的规则陈述} | `{ClassName}.{method}` | {修改后的理由} | {修改后的后果} |

## REMOVED

### 不变式目录

| ID |
|----|
| INV-{NNN} |

## RENAMED

### 不变式目录

| ID | 旧术语 | 新术语 |
|----|--------|--------|
| INV-{NNN} | {旧业务术语} | {新业务术语} |
