"""Order persistence. PostgreSQL when DATABASE_URL is set, in-memory otherwise (tests/dev)."""
from __future__ import annotations

import os
import time

DDL = """
CREATE TABLE IF NOT EXISTS orders (
    id             TEXT PRIMARY KEY,
    item_id        TEXT NOT NULL,
    quantity       INTEGER NOT NULL CHECK (quantity > 0),
    customer_email TEXT NOT NULL,
    status         TEXT NOT NULL,
    created_at     TEXT NOT NULL
)
"""
COLUMNS = "id, item_id, quantity, customer_email, status, created_at"


class MemoryStorage:
    def __init__(self) -> None:
        self._orders: dict[str, dict] = {}

    def init(self) -> None:
        pass

    def ping(self) -> bool:
        return True

    def add(self, order: dict) -> None:
        self._orders[order["id"]] = dict(order)

    def get(self, order_id: str) -> dict | None:
        order = self._orders.get(order_id)
        return dict(order) if order else None

    def list(self, limit: int = 50) -> list[dict]:
        orders = sorted(self._orders.values(), key=lambda o: o["created_at"], reverse=True)
        return [dict(o) for o in orders[:limit]]

    def set_status(self, order_id: str, status: str) -> None:
        if order_id in self._orders:
            self._orders[order_id]["status"] = status

    def pending(self, created_before: str, limit: int = 50) -> list[dict]:
        orders = [o for o in self._orders.values() if o["status"] == "pending" and o["created_at"] <= created_before]
        return [dict(o) for o in sorted(orders, key=lambda o: o["created_at"])[:limit]]


class PostgresStorage:
    """Opens one short-lived connection per call. Simple on purpose; see docs/adr/0006."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def _connect(self):
        import psycopg
        from psycopg.rows import dict_row

        return psycopg.connect(self.dsn, row_factory=dict_row, connect_timeout=3)

    def init(self, retries: int = 30, delay: float = 2.0) -> None:
        last: Exception | None = None
        for _ in range(retries):
            try:
                with self._connect() as conn:
                    conn.execute(DDL)
                return
            except Exception as exc:  # DB may still be starting
                last = exc
                time.sleep(delay)
        raise RuntimeError(f"database not reachable: {last}")

    def ping(self) -> bool:
        try:
            with self._connect() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception:
            return False

    def add(self, order: dict) -> None:
        with self._connect() as conn:
            conn.execute(
                f"INSERT INTO orders ({COLUMNS}) VALUES (%s, %s, %s, %s, %s, %s)",
                tuple(order[c.strip()] for c in COLUMNS.split(",")),
            )

    def get(self, order_id: str) -> dict | None:
        with self._connect() as conn:
            return conn.execute(
                f"SELECT {COLUMNS} FROM orders WHERE id = %s", (order_id,)
            ).fetchone()

    def list(self, limit: int = 50) -> list[dict]:
        with self._connect() as conn:
            return conn.execute(
                f"SELECT {COLUMNS} FROM orders ORDER BY created_at DESC LIMIT %s", (limit,)
            ).fetchall()

    def set_status(self, order_id: str, status: str) -> None:
        with self._connect() as conn:
            conn.execute("UPDATE orders SET status = %s WHERE id = %s", (status, order_id))

    def pending(self, created_before: str, limit: int = 50) -> list[dict]:
        with self._connect() as conn:
            return conn.execute(
                f"SELECT {COLUMNS} FROM orders WHERE status = 'pending' AND created_at <= %s "
                "ORDER BY created_at ASC LIMIT %s",
                (created_before, limit),
            ).fetchall()


def get_storage():
    dsn = os.getenv("DATABASE_URL")
    return PostgresStorage(dsn) if dsn else MemoryStorage()
