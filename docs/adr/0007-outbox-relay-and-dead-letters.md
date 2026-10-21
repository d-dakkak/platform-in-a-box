# ADR 0007: Outbox relay, replayable results and dead-letter queues

Status: accepted

## Problem
Three ways to lose or poison events:
1. `orders-api` stores an order, then the broker is down: the order stays `pending` and no event is sent.
2. `inventory-worker` commits the stock change, then fails to publish its result. The redelivered message hits the idempotency marker and used to be acknowledged silently, so the result event was lost.
3. An unparsable message was dropped (nack without requeue) and only logged.

## Decision
1. **Relay instead of manual repair.** The `orders` table is the outbox. A background loop in `orders-api` (`app/relay.py`, every 10 s, orders older than 5 s) publishes `pending` orders and marks them `created`. Failures count into `orders_publish_failures_total`, so the existing alert fires during an outage and resolves after recovery.
2. **Idempotent state, replayable events.** The worker stores the outcome per `order_id` in the same transaction as the stock update. A redelivered message changes nothing but republishes the same event. Delivery is at-least-once; consumers must tolerate duplicates.
3. **Dead-letter queues.** Both consumers declare a dead-letter exchange `shop.dlx` and a `<queue>.dlq` queue. Rejected messages land there. The counter `poison_messages_total` drives the alert `ShopPoisonMessages`.

## Consequences
+ A broker outage no longer needs manual repair; the game-day scenario shows detection and automatic recovery.
+ Several `orders-api` replicas may publish the same pending order. That is harmless because consumers are idempotent. A `SELECT ... FOR UPDATE SKIP LOCKED` claim would avoid the duplicates.
- Not a full transactional outbox: the order insert and the first publish attempt are still two steps, and the relay polls instead of reacting.
- **Migration:** adding `x-dead-letter-*` arguments to an existing queue fails with `PRECONDITION_FAILED`. Recreate the environment (`docker compose down -v`, or delete the queues) once after updating.
