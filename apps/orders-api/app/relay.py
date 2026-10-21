"""Re-publishes orders whose `order.created` event was not published (a small outbox).

The `orders` table is the outbox: an order with status `pending` has been stored but its event has not been
confirmed by the broker. The relay retries those orders. Delivery is at-least-once; consumers are idempotent
per `order_id`, so two replicas publishing the same order is harmless.
"""
import logging
from datetime import UTC, datetime, timedelta

from .events import order_created_payload

log = logging.getLogger("orders-api.relay")


def publish_pending(storage, publisher, min_age_seconds: float = 5.0, limit: int = 50) -> tuple[int, int]:
    """Publishes pending orders older than `min_age_seconds`. Returns (published, failed)."""
    cutoff = (datetime.now(UTC) - timedelta(seconds=min_age_seconds)).isoformat()
    published = failed = 0
    for order in storage.pending(cutoff, limit):
        try:
            publisher.publish("order.created", order_created_payload(order))
        except Exception:
            failed += 1
            log.warning("relay: publish failed", extra={"ctx": {"order_id": order["id"]}})
            break  # the broker is probably down; try again on the next run
        storage.set_status(order["id"], "created")
        published += 1
        log.info("relay: order published", extra={"ctx": {"order_id": order["id"]}})
    return published, failed
