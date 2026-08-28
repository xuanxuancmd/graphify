# 订单业务不变式（Invariants）

## 订单聚合不变式

| 不变式<anchor:ddd> | 归属聚合 | 代码锚点<anchor:code> | 说明<anchor:desc> |
|---|---|---|---|
| INV-01 金额非负 | 订单 | OrderService.validate_amount | 订单金额必须大于等于零 |
| INV-02 状态有序 | 订单 | OrderStateMachine.transition | 订单状态只能单向前进不能回退 |
| INV-03 唯一订单号 | 订单 | OrderRepository.create | 同一用户同一时刻不能有重复订单号 |

## 支付聚合不变式

| 不变式<anchor:ddd> | 归属聚合 | 代码锚点<anchor:code> | 说明<anchor:desc> |
|---|---|---|---|
| INV-04 支付金额匹配 | 支付 | PaymentService.verify | 支付金额必须与订单金额一致 |
| INV-05 幂等回调 | 支付 | PaymentCallbackHandler.handle | 同一支付单的回调只能处理一次 |
