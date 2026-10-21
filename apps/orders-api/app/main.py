"""Orders API: accepts orders, persists them and publishes `order.created` events."""
import asyncio
import contextlib
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI, HTTPException, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pydantic import BaseModel, Field

from .events import get_publisher, order_created_payload
from .logjson import setup as setup_logging
from .relay import publish_pending
from .storage import get_storage

log = logging.getLogger("orders-api")

HTTP_REQUESTS = Counter("http_requests_total", "HTTP requests", ["method", "path", "status"])
HTTP_LATENCY = Histogram("http_request_duration_seconds", "HTTP latency", ["method", "path"])
ORDERS_CREATED = Counter("orders_created_total", "Orders accepted")
PUBLISH_FAILURES = Counter("orders_publish_failures_total", "order.created events not published")
RELAY_PUBLISHED = Counter("orders_relay_published_total", "Pending orders published later by the relay")


class OrderIn(BaseModel):
    item_id: str = Field(min_length=1, max_length=64, examples=["sku-1001"])
    quantity: int = Field(gt=0, le=100, examples=[2])
    customer_email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", examples=["ada@example.com"])


class Order(OrderIn):
    id: str
    status: str = Field(description="pending = stored, event not yet published; created = event published")
    created_at: str


def create_app(storage=None, publisher=None) -> FastAPI:
    setup_logging()
    storage = storage or get_storage()
    publisher = publisher or get_publisher()

    relay_interval = float(os.getenv("RELAY_INTERVAL_SECONDS", "10"))  # 0 disables the relay

    async def relay_loop():
        while True:
            await asyncio.sleep(relay_interval)
            try:
                published, failed = await asyncio.to_thread(publish_pending, storage, publisher)
            except Exception:
                log.exception("relay run failed")
                continue
            RELAY_PUBLISHED.inc(published)
            PUBLISH_FAILURES.inc(failed)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        storage.init()
        task = asyncio.create_task(relay_loop()) if relay_interval > 0 else None
        try:
            yield
        finally:
            if task:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task

    app = FastAPI(
        title="Orders API",
        version="1.0.0",
        description="API-first order intake. Emits `order.created` on the `shop.events` exchange.",
        lifespan=lifespan,
    )

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        start = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            route = request.scope.get("route")
            path = route.path if route else "unmatched"
            HTTP_REQUESTS.labels(request.method, path, str(status)).inc()
            HTTP_LATENCY.labels(request.method, path).observe(time.perf_counter() - start)

    @app.get("/healthz", tags=["ops"])
    def healthz():
        return {"status": "ok"}

    @app.get("/readyz", tags=["ops"])
    def readyz():
        if not storage.ping():
            raise HTTPException(status_code=503, detail="storage unavailable")
        return {"status": "ready"}

    @app.get("/metrics", include_in_schema=False)
    def metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.post("/orders", response_model=Order, status_code=201, tags=["orders"])
    def create_order(body: OrderIn):
        order = {
            "id": str(uuid.uuid4()),
            **body.model_dump(),
            "status": "pending",
            "created_at": datetime.now(UTC).isoformat(),
        }
        storage.add(order)
        ORDERS_CREATED.inc()
        try:
            publisher.publish("order.created", order_created_payload(order))
            storage.set_status(order["id"], "created")
            order["status"] = "created"
        except Exception:
            # Order stays `pending`; the relay publishes it once the broker is back (see relay.py).
            PUBLISH_FAILURES.inc()
            log.exception("failed to publish order.created", extra={"ctx": {"order_id": order["id"]}})
        log.info("order accepted", extra={"ctx": {"order_id": order["id"], "status": order["status"]}})
        return order

    @app.get("/orders/{order_id}", response_model=Order, tags=["orders"])
    def get_order(order_id: str):
        order = storage.get(order_id)
        if order is None:
            raise HTTPException(status_code=404, detail="order not found")
        return order

    @app.get("/orders", response_model=list[Order], tags=["orders"])
    def list_orders(limit: int = 50):
        return storage.list(limit=min(max(limit, 1), 200))

    return app


app = create_app()
