"""Turns domain events into customer notifications (stdlib only)."""


def render(routing_key: str, payload: dict) -> tuple[str, str] | None:
    """Returns (recipient, text) or None if the event needs no notification."""
    to = payload.get("customer_email") or "unknown"
    order_id = payload.get("order_id", "?")
    item = payload.get("item_id", "?")
    if routing_key == "order.created":
        return to, f"Order {order_id}: we received your order for {payload.get('quantity')} x {item}."
    if routing_key == "inventory.reserved":
        return to, f"Order {order_id}: your items are reserved and will ship soon."
    if routing_key == "inventory.rejected":
        return to, f"Order {order_id}: sorry, {item} is currently out of stock."
    return None
