# 订单领域模型（Domain Model）

## 订单聚合

| 聚合根<anchor:ddd> | 代码锚点<anchor:code> | 说明<anchor:desc> |
|---|---|---|
| AG-01 订单聚合 | OrderService | 订单聚合根，负责订单生命周期管理 |
| AG-02 订单项 | OrderItem | 订单内单个商品的值对象聚合 |
| AG-03 收货地址 | ShippingAddress | 订单关联的收货地址值对象 |

## 支付聚合

| 聚合根<anchor:ddd> | 代码锚点<anchor:code> | 说明<anchor:desc> |
|---|---|---|
| AG-04 支付单 | PaymentService | 支付聚合根，负责支付发起与回调 |
| AG-05 支付明细 | PaymentDetail | 单次支付请求的明细值对象 |

## 聚合协作关系

| 聚合根<anchor:ddd> | 源聚合 | 目标聚合 | 代码锚点<anchor:code> | 说明<anchor:desc> |
|---|---|---|---|---|
| AG-06 订单-支付协作 | 订单 | 支付 | OrderService.bind_payment | 订单创建后绑定支付单 |
| AG-07 订单-库存协作 | 订单 | 库存 | OrderService.reserve_stock | 订单确认后预扣库存 |
