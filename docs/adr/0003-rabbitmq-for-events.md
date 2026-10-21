# ADR 0003: RabbitMQ with a topic exchange for domain events

Status: accepted

## Decision
Services communicate through the durable topic exchange `shop.events`. `orders-api` publishes `order.created`; `inventory-worker` answers with `inventory.reserved` or `inventory.rejected`; `notifier` subscribes to `order.created` and `inventory.*`. Each consumer owns a durable queue.

## Consequences
+ Producers do not know their consumers; new consumers need no producer change.
+ At-least-once delivery: the worker is idempotent per `order_id` (marker table, same transaction as the stock update).
- Outbox relay, replayable results and dead-letter queues are covered in ADR 0007.
- Production alternative: Azure Service Bus; the event contract stays the same.
