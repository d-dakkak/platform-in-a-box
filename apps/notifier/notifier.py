"""Consumes order and inventory events and 'sends' notifications (logged, no real e-mail)."""
import json
import logging
import os
import signal
import time

import pika
from prometheus_client import Counter, start_http_server

from logjson import setup
from messages import render

EXCHANGE = "shop.events"
DLX = "shop.dlx"
QUEUE = "notifier.events"
DLQ = f"{QUEUE}.dlq"
BINDINGS = ["order.created", "inventory.*"]
log = logging.getLogger("notifier")
SENT = Counter("notifications_sent_total", "Notifications sent", ["event"])
POISON = Counter("poison_messages_total", "Messages rejected as unprocessable (moved to the dead-letter queue)")
stop = False


def _request_stop(*_):
    global stop
    stop = True


def consume(url: str) -> None:
    connection = pika.BlockingConnection(pika.URLParameters(url))
    try:
        channel = connection.channel()
        channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
        channel.exchange_declare(exchange=DLX, exchange_type="direct", durable=True)
        channel.queue_declare(queue=DLQ, durable=True)
        channel.queue_bind(queue=DLQ, exchange=DLX, routing_key=QUEUE)
        channel.queue_declare(
            queue=QUEUE,
            durable=True,
            arguments={"x-dead-letter-exchange": DLX, "x-dead-letter-routing-key": QUEUE},
        )
        for key in BINDINGS:
            channel.queue_bind(queue=QUEUE, exchange=EXCHANGE, routing_key=key)
        channel.basic_qos(prefetch_count=10)
        for method, _props, body in channel.consume(QUEUE, inactivity_timeout=1):
            if stop:
                break
            if method is None:
                continue
            try:
                result = render(method.routing_key, json.loads(body))
            except ValueError:
                POISON.inc()
                channel.basic_nack(method.delivery_tag, requeue=False)
                continue
            if result:
                recipient, text = result
                SENT.labels(method.routing_key).inc()
                log.info("notification sent", extra={"ctx": {"to": recipient, "text": text}})
            channel.basic_ack(method.delivery_tag)
    finally:
        if connection.is_open:
            connection.close()


def main() -> None:
    setup()
    signal.signal(signal.SIGTERM, _request_stop)
    signal.signal(signal.SIGINT, _request_stop)
    start_http_server(int(os.getenv("METRICS_PORT", "8000")))
    url = os.environ["AMQP_URL"]
    while not stop:
        try:
            consume(url)
        except pika.exceptions.AMQPError:
            log.warning("broker connection lost, retrying in 3s")
            time.sleep(3)


if __name__ == "__main__":
    main()
