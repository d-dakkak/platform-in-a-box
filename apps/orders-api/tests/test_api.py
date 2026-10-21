import pytest
from fastapi.testclient import TestClient

from app.events import MemoryPublisher
from app.main import create_app
from app.storage import MemoryStorage

VALID = {"item_id": "sku-1001", "quantity": 2, "customer_email": "ada@example.com"}


class BrokenPublisher:
    def publish(self, routing_key, payload):
        raise ConnectionError("broker down")


@pytest.fixture
def publisher():
    return MemoryPublisher()


@pytest.fixture
def client(publisher):
    with TestClient(create_app(MemoryStorage(), publisher)) as c:
        yield c


def test_create_and_get_order(client, publisher):
    res = client.post("/orders", json=VALID)
    assert res.status_code == 201
    body = res.json()
    assert body["status"] == "created"
    assert publisher.events[0][0] == "order.created"
    assert publisher.events[0][1]["order_id"] == body["id"]
    assert client.get(f"/orders/{body['id']}").json()["item_id"] == "sku-1001"


def test_list_orders(client):
    client.post("/orders", json=VALID)
    client.post("/orders", json=VALID)
    assert len(client.get("/orders").json()) == 2


@pytest.mark.parametrize(
    "patch",
    [{"quantity": 0}, {"quantity": 101}, {"item_id": ""}, {"customer_email": "not-an-email"}],
)
def test_validation_rejects_bad_input(client, patch):
    assert client.post("/orders", json={**VALID, **patch}).status_code == 422


def test_unknown_order_is_404(client):
    assert client.get("/orders/does-not-exist").status_code == 404


def test_order_is_kept_pending_when_broker_is_down():
    with TestClient(create_app(MemoryStorage(), BrokenPublisher())) as c:
        res = c.post("/orders", json=VALID)
        assert res.status_code == 201
        assert res.json()["status"] == "pending"


def test_health_ready_and_metrics(client):
    assert client.get("/healthz").status_code == 200
    assert client.get("/readyz").status_code == 200
    client.post("/orders", json=VALID)
    text = client.get("/metrics").text
    assert "orders_created_total" in text
    assert "http_requests_total" in text


def test_readyz_fails_when_storage_down():
    class DownStorage(MemoryStorage):
        def ping(self):
            return False

    with TestClient(create_app(DownStorage(), MemoryPublisher())) as c:
        assert c.get("/readyz").status_code == 503
