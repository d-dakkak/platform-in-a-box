import unittest

from messages import render


class RenderTests(unittest.TestCase):
    def test_order_created(self):
        to, text = render("order.created", {"order_id": "1", "item_id": "s", "quantity": 2, "customer_email": "a@b.de"})
        self.assertEqual(to, "a@b.de")
        self.assertIn("2 x s", text)

    def test_reserved_and_rejected(self):
        self.assertIn("reserved", render("inventory.reserved", {"order_id": "1"})[1])
        self.assertIn("out of stock", render("inventory.rejected", {"order_id": "1", "item_id": "s"})[1])

    def test_unknown_event_is_ignored(self):
        self.assertIsNone(render("something.else", {}))

    def test_missing_email_falls_back(self):
        self.assertEqual(render("inventory.reserved", {"order_id": "1"})[0], "unknown")


if __name__ == "__main__":
    unittest.main()
