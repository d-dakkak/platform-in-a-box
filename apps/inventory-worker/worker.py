"""Consumes order.created, reserves stock, publishes inventory.reserved / inventory.rejected."""
import json
import logging
import os
import signal
import time

import pika
from prometheus_client import Counter, start_http_server

from inventory import get_inventory, handle_order_created
from logjson import setup

EXCHANGE = "shop.events"
DLX = "shop.dlx"
QUEUE = "inventory.order-created"
DLQ = f"{QUEUE}.dlq"
log = logging.getLogger("inventory-worker")
RESULTS = Counter("inventory_reservations_total", "Reservation outcomes", ["result"])
POISON = Counter("poison_messages_total", "Messages rejected as unprocessable (moved to the dead-letter queue)")
stop = False


def _request_stop(*_):
    global stop
    stop = True


def consume(url: str, inventory) -> None:
    connection = pika.BlockingConnection(pika.URLParameters(url))
    try:
        channel = connection.channel()
        channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
        # Rejected messages (requeue=False) go to the dead-letter queue instead of being dropped.
        channel.exchange_declare(exchange=DLX, exchange_type="direct", durable=True)
        channel.queue_declare(queue=DLQ, durable=True)
        channel.queue_bind(queue=DLQ, exchange=DLX, routing_key=QUEUE)
        channel.queue_declare(
            queue=QUEUE,
            durable=True,
            arguments={"x-dead-letter-exchange": DLX, "x-dead-letter-routing-key": QUEUE},
        )
        channel.queue_bind(queue=QUEUE, exchange=EXCHANGE, routing_key="order.created")
        channel.basic_qos(prefetch_count=10)
        log.info("consuming", extra={"ctx": {"queue": QUEUE}})
        for method, _props, body in channel.consume(QUEUE, inactivity_timeout=1):
            if stop:
                break
            if method is None:
                continue
            try:
                payload = json.loads(body)
                outcome = handle_order_created(payload, inventory)
            except (ValueError, KeyError):
                POISON.inc()
                log.error("poison message dead-lettered", extra={"ctx": {"body": body[:200].decode(errors="replace")}})
                channel.basic_nack(method.delivery_tag, requeue=False)
                continue
            except Exception:
                log.exception("processing failed, will retry")
                channel.basic_nack(method.delivery_tag, requeue=True)
                time.sleep(1)
                continue
            if outcome:
                routing_key, event, duplicate = outcome
                channel.basic_publish(
                    exchange=EXCHANGE,
                    routing_key=routing_key,
                    body=json.dumps(event).encode(),
                    properties=pika.BasicProperties(content_type="application/json", delivery_mode=2),
                )
                RESULTS.labels("duplicate" if duplicate else routing_key.split(".")[1]).inc()
                log.info("order processed", extra={"ctx": {"order_id": event["order_id"], "result": routing_key}})
            else:
                RESULTS.labels("duplicate").inc()  # legacy duplicate without a stored result
            channel.basic_ack(method.delivery_tag)
    finally:
        if connection.is_open:
            connection.close()


def main() -> None:
    setup()
    signal.signal(signal.SIGTERM, _request_stop)
    signal.signal(signal.SIGINT, _request_stop)
    start_http_server(int(os.getenv("METRICS_PORT", "8000")))
    inventory = get_inventory()
    inventory.init()
    url = os.environ["AMQP_URL"]
    while not stop:
        try:
            consume(url, inventory)
        except pika.exceptions.AMQPError:
            log.warning("broker connection lost, retrying in 3s")
            time.sleep(3)


if __name__ == "__main__":
    main()
