"""Event publishing. RabbitMQ when AMQP_URL is set, in-memory otherwise (tests/dev)."""
import json
import logging
import os

log = logging.getLogger("orders-api.events")
EXCHANGE = "shop.events"


def order_created_payload(order: dict) -> dict:
    """The event contract for `order.created` (shared by the API and the relay)."""
    return {
        "order_id": order["id"],
        "item_id": order["item_id"],
        "quantity": order["quantity"],
        "customer_email": order["customer_email"],
        "created_at": order["created_at"],
    }


class MemoryPublisher:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict]] = []

    def publish(self, routing_key: str, payload: dict) -> None:
        self.events.append((routing_key, payload))
        log.info("event (memory)", extra={"ctx": {"routing_key": routing_key}})


class RabbitPublisher:
    """Publishes with broker confirms. One short-lived connection per event (simple, robust)."""

    def __init__(self, url: str, exchange: str = EXCHANGE) -> None:
        self.url = url
        self.exchange = exchange

    def publish(self, routing_key: str, payload: dict) -> None:
        import pika

        params = pika.URLParameters(self.url)
        params.socket_timeout = 3
        params.blocked_connection_timeout = 3
        connection = pika.BlockingConnection(params)
        try:
            channel = connection.channel()
            channel.confirm_delivery()
            channel.exchange_declare(exchange=self.exchange, exchange_type="topic", durable=True)
            channel.basic_publish(
                exchange=self.exchange,
                routing_key=routing_key,
                body=json.dumps(payload).encode(),
                properties=pika.BasicProperties(content_type="application/json", delivery_mode=2),
            )
        finally:
            connection.close()


def get_publisher():
    url = os.getenv("AMQP_URL")
    return RabbitPublisher(url) if url else MemoryPublisher()
