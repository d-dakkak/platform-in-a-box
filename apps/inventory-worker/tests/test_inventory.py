import unittest

from inventory import InMemoryInventory, handle_order_created


def payload(order_id="o-1", item="sku-1001", qty=2):
    return {"order_id": order_id, "item_id": item, "quantity": qty, "customer_email": "a@b.de"}


class InventoryTests(unittest.TestCase):
    def test_reserves_when_stock_available(self):
        inv = InMemoryInventory({"sku-1001": 5})
        key, event, duplicate = handle_order_created(payload(qty=3), inv)
        self.assertEqual(key, "inventory.reserved")
        self.assertEqual(inv.stock["sku-1001"], 2)
        self.assertEqual(event["customer_email"], "a@b.de")

    def test_rejects_when_stock_insufficient(self):
        inv = InMemoryInventory({"sku-1001": 1})
        key, event, duplicate = handle_order_created(payload(qty=3), inv)
        self.assertEqual(key, "inventory.rejected")
        self.assertEqual(event["reason"], "insufficient_stock")
        self.assertEqual(inv.stock["sku-1001"], 1)

    def test_rejects_unknown_item(self):
        key, _, _ = handle_order_created(payload(item="nope"), InMemoryInventory())
        self.assertEqual(key, "inventory.rejected")

    def test_duplicate_delivery_changes_state_once_but_republishes(self):
        inv = InMemoryInventory({"sku-1001": 10})
        first = handle_order_created(payload(), inv)
        second = handle_order_created(payload(), inv)
        self.assertEqual(first[0], "inventory.reserved")
        self.assertFalse(first[2])
        self.assertEqual(second[0], "inventory.reserved")  # same event again, so a lost publish is recovered
        self.assertTrue(second[2])
        self.assertEqual(inv.stock["sku-1001"], 8)  # stock was reserved only once

    def test_duplicate_of_rejected_order_stays_rejected(self):
        inv = InMemoryInventory({"sku-1001": 1})
        handle_order_created(payload(qty=3), inv)
        inv.stock["sku-1001"] = 100  # stock appears later; the original decision must not flip
        again = handle_order_created(payload(qty=3), inv)
        self.assertEqual(again[0], "inventory.rejected")
        self.assertEqual(inv.stock["sku-1001"], 100)

    def test_missing_field_raises_key_error(self):
        with self.assertRaises(KeyError):
            handle_order_created({"order_id": "x"}, InMemoryInventory())


if __name__ == "__main__":
    unittest.main()
