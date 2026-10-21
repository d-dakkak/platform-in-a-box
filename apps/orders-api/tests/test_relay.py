import unittest
from datetime import UTC, datetime, timedelta

from app.events import MemoryPublisher
from app.relay import publish_pending
from app.storage import MemoryStorage


def order(order_id: str, age_seconds: float, status: str = "pending") -> dict:
    created = (datetime.now(UTC) - timedelta(seconds=age_seconds)).isoformat()
    return {
        "id": order_id,
        "item_id": "sku-1001",
        "quantity": 1,
        "customer_email": "a@b.de",
        "status": status,
        "created_at": created,
    }


class BrokenPublisher:
    def publish(self, routing_key, payload):
        raise ConnectionError("broker down")


class RelayTests(unittest.TestCase):
    def test_publishes_old_pending_orders_and_marks_them_created(self):
        storage, publisher = MemoryStorage(), MemoryPublisher()
        storage.add(order("o-1", 60))
        self.assertEqual(publish_pending(storage, publisher), (1, 0))
        self.assertEqual(storage.get("o-1")["status"], "created")
        self.assertEqual(publisher.events[0][0], "order.created")
        self.assertEqual(publisher.events[0][1]["order_id"], "o-1")

    def test_skips_fresh_orders_and_already_created_ones(self):
        storage, publisher = MemoryStorage(), MemoryPublisher()
        storage.add(order("fresh", 1))
        storage.add(order("done", 60, status="created"))
        self.assertEqual(publish_pending(storage, publisher), (0, 0))
        self.assertEqual(publisher.events, [])

    def test_broker_down_keeps_orders_pending_and_stops_early(self):
        storage = MemoryStorage()
        storage.add(order("o-1", 60))
        storage.add(order("o-2", 50))
        self.assertEqual(publish_pending(storage, BrokenPublisher()), (0, 1))
        self.assertEqual(storage.get("o-1")["status"], "pending")
        self.assertEqual(storage.get("o-2")["status"], "pending")

    def test_recovers_after_the_broker_is_back(self):
        storage, publisher = MemoryStorage(), MemoryPublisher()
        storage.add(order("o-1", 60))
        publish_pending(storage, BrokenPublisher())
        self.assertEqual(publish_pending(storage, publisher), (1, 0))
        self.assertEqual(storage.get("o-1")["status"], "created")


if __name__ == "__main__":
    unittest.main()
