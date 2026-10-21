"""Stock logic (stdlib only, easy to unit-test) with in-memory and PostgreSQL backends."""
import os
import time

SEED_STOCK = {"sku-1001": 100, "sku-1002": 50, "sku-1003": 10}

DDL = [
    """CREATE TABLE IF NOT EXISTS inventory (
           item_id TEXT PRIMARY KEY,
           stock   INTEGER NOT NULL CHECK (stock >= 0))""",
    "CREATE TABLE IF NOT EXISTS processed_orders (order_id TEXT PRIMARY KEY)",
    # The outcome is stored so that a redelivered message can republish the same event (see docs/adr/0007).
    "ALTER TABLE processed_orders ADD COLUMN IF NOT EXISTS result TEXT",
]


class InMemoryInventory:
    def __init__(self, stock: dict[str, int] | None = None) -> None:
        self.stock = dict(SEED_STOCK if stock is None else stock)
        self._results: dict[str, str] = {}

    def init(self) -> None:
        pass

    def reserve(self, order_id: str, item_id: str, qty: int) -> tuple[str | None, bool]:
        """Returns (result, duplicate). Idempotent per order_id: a repeat returns the stored result."""
        if order_id in self._results:
            return self._results[order_id], True
        if self.stock.get(item_id, 0) >= qty:
            self.stock[item_id] -= qty
            result = "reserved"
        else:
            result = "rejected"
        self._results[order_id] = result
        return result, False


class PostgresInventory:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def _connect(self):
        import psycopg

        return psycopg.connect(self.dsn, connect_timeout=3)

    def init(self, retries: int = 30, delay: float = 2.0) -> None:
        last: Exception | None = None
        for _ in range(retries):
            try:
                with self._connect() as conn:
                    for stmt in DDL:
                        conn.execute(stmt)
                    for item, stock in SEED_STOCK.items():
                        conn.execute(
                            "INSERT INTO inventory (item_id, stock) VALUES (%s, %s) "
                            "ON CONFLICT DO NOTHING",
                            (item, stock),
                        )
                return
            except Exception as exc:
                last = exc
                time.sleep(delay)
        raise RuntimeError(f"database not reachable: {last}")

    def reserve(self, order_id: str, item_id: str, qty: int) -> tuple[str | None, bool]:
        # One transaction: idempotency marker, stock update and stored result commit (or roll back) together.
        with self._connect() as conn:
            marker = conn.execute(
                "INSERT INTO processed_orders (order_id) VALUES (%s) ON CONFLICT DO NOTHING",
                (order_id,),
            )
            if marker.rowcount == 0:
                row = conn.execute("SELECT result FROM processed_orders WHERE order_id = %s", (order_id,)).fetchone()
                return (row[0] if row else None), True  # None = legacy row without a stored result
            updated = conn.execute(
                "UPDATE inventory SET stock = stock - %s WHERE item_id = %s AND stock >= %s",
                (qty, item_id, qty),
            )
            result = "reserved" if updated.rowcount == 1 else "rejected"
            conn.execute("UPDATE processed_orders SET result = %s WHERE order_id = %s", (result, order_id))
            return result, False


def get_inventory():
    dsn = os.getenv("DATABASE_URL")
    return PostgresInventory(dsn) if dsn else InMemoryInventory()


def handle_order_created(payload: dict, inventory) -> tuple[str, dict, bool] | None:
    """Maps an order.created payload to (routing_key, event, duplicate).

    A redelivered message yields the same event again (duplicate=True): state changes happen once, but the
    event is republished, so a failed publish on the first attempt is not lost. Consumers must be idempotent.
    Returns None only for legacy duplicates that have no stored result.
    """
    order_id, item_id, qty = payload["order_id"], payload["item_id"], int(payload["quantity"])
    result, duplicate = inventory.reserve(order_id, item_id, qty)
    if result is None:
        return None
    event = {
        "order_id": order_id,
        "item_id": item_id,
        "quantity": qty,
        "customer_email": payload.get("customer_email"),
    }
    if result == "reserved":
        return "inventory.reserved", event, duplicate
    return "inventory.rejected", {**event, "reason": "insufficient_stock"}, duplicate
