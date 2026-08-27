# 技术约束（Technical Constraints）

### TC-001: 消息中间件选型

**代码锚点**: `order_service.rs` · `payment_consumer.rs`

**适用范围**: BC-01, BC-02

**选型理由**: 采用 Kafka 因为最终一致性可接受，且消费者水平扩展能力优于 RabbitMQ。

### TC-002: 数据库分库策略

**代码锚点**: `OrderRepository.create`

**适用范围**: 全局

**选型理由**: 按订单 ID 哈希分库，避免单一库写入瓶颈。

### TC-003: API 网关选型

**代码锚点**: `POST /api/orders`

**适用范围**: BC-01

**选型理由**: 采用 Kong 因为插件生态成熟，支持限流、鉴权、可观测性开箱即用。
