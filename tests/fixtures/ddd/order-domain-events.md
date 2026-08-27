# 订单领域事件（Domain Events）

## 订单上下文事件

| 领域事件<anchor:ddd> | 代码锚点<anchor:code> | 说明<anchor:desc> |
|---|---|---|
| DE-01 订单已创建 | OrderCreatedEvent.publish | 订单创建完成时发布 |
| DE-02 订单已支付 | OrderPaidEvent.publish | 订单收到支付确认时发布 |
| DE-03 订单已发货 | OrderShippedEvent.publish | 订单关联发货单创建后发布 |
| DE-04 订单已取消 | OrderCancelledEvent.publish | 订单被用户或系统取消时发布 |
| DE-05 订单已完成 | OrderCompletedEvent.publish | 订单走完全部流程后发布 |

## 支付上下文事件

| 领域事件<anchor:ddd> | 代码锚点<anchor:code> | 说明<anchor:desc> |
|---|---|---|
| DE-06 支付已发起 | PaymentInitiatedEvent.publish | 调用支付渠道后发布 |
| DE-07 支付已成功 | PaymentSucceededEvent.publish | 支付渠道回调成功后发布 |
| DE-08 支付已失败 | PaymentFailedEvent.publish | 支付渠道回调失败或超时后发布 |
