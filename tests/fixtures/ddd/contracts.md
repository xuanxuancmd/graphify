# 订单业务契约（Contracts）

## 订单上下文对外契约

| 契约<anchor:ddd> | 对端 BC | 代码锚点<anchor:code> | 说明<anchor:desc> |
|---|---|---|---|
| CT-01 订单创建事件 | 支付 | OrderCreatedEvent.publish | 订单创建后发布事件供支付上下文消费 |
| CT-02 订单状态查询 | 库存 | OrderService.get_status | 库存上下文查询订单当前状态以决定是否补货 |
| CT-03 订单取消通知 | 支付 | OrderCancelledEvent.publish | 订单取消后通知支付上下文终止待支付流程 |

## 支付上下文对外契约

| 契约<anchor:ddd> | 对端 BC | 代码锚点<anchor:code> | 说明<anchor:desc> |
|---|---|---|---|
| CT-04 支付完成事件 | 订单 | PaymentCompletedEvent.publish | 支付完成后通知订单上下文推进状态 |
| CT-05 支付失败事件 | 订单 | PaymentFailedEvent.publish | 支付失败后通知订单上下文标记异常 |
