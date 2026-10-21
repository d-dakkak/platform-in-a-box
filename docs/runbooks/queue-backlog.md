# Runbook: ShopQueueBacklog / ShopOrderEventsNotPublished

**Impact:** orders are accepted but stock reservation and notifications are delayed.

## 1. Check
```bash
python tools/pctl/pctl.py queues --url http://localhost:15672 --user shop --password '<from Key Vault>'
kubectl -n shop port-forward svc/rabbitmq 15672:15672
kubectl -n shop get deploy inventory-worker notifier
kubectl -n shop logs deploy/inventory-worker --tail=50
```

## 2. Causes
- **Worker down or crashlooping:** see pod-crashloop runbook. Messages are durable, they are processed after recovery.
- **Worker slow:** database slow or lock contention. Scale `inventory-worker` replicas (safe, the worker is idempotent per order).
- **`ShopOrderEventsNotPublished`:** the API cannot reach RabbitMQ. Orders stay `pending` and the relay in `orders-api` retries every 10 s. Fix the broker; the alert resolves once the relay has published everything. Check `kubectl -n shop logs deploy/orders-api | grep relay`.
- **`ShopPoisonMessages`:** a consumer rejected an unprocessable message. Inspect the dead-letter queues (`inventory.order-created.dlq`, `notifier.events.dlq`) in the RabbitMQ UI, find the producer bug, fix it, then move the messages back (shovel/republish) or purge them.

## 3. Verify recovery
Queue depth falls to zero, `ShopQueueBacklog` resolves, new orders reach status `created`.
