"""Manual M-Pesa receipt verification (customer fallback)."""

from types import SimpleNamespace

import pytest

import app.services.inventory as inventory
import app.routers.orders as orders_router
from app.dependencies import get_current_user
from app.main import app
from tests.fakes import FakeSupabase


@pytest.fixture
def auth_user():
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id="user-1", email="buyer@example.com"
    )
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def _setup(monkeypatch, status):
    fake = FakeSupabase()
    fake.store["orders"] = [
        {
            "id": "o1",
            "order_reference": "GWV-1",
            "user_id": "user-1",
            "status": status,
            "total_amount": 100,
            "customer_email": "buyer@example.com",
            "items": [{"id": "p1", "qty": 2, "name": "Phone", "price": 50}],
        }
    ]
    fake.store["products"] = [{"id": "p1", "stock_quantity": 5}]
    monkeypatch.setattr(orders_router, "supabase", fake)
    monkeypatch.setattr(inventory, "supabase", fake)
    monkeypatch.setattr(orders_router, "send_receipt_email", lambda *a: None)
    monkeypatch.setattr(orders_router, "user_is_admin", lambda user: False)
    return fake


def test_verify_receipt_from_pending_does_not_change_stock(monkeypatch, client, auth_user):
    fake = _setup(monkeypatch, "Pending PIN")

    resp = client.post("/orders/o1/verify-receipt", json={"receipt_number": "QHS8X9ABCD"})

    assert resp.status_code == 200
    assert fake.store["orders"][0]["status"] == "Paid"
    assert fake.store["orders"][0]["receipt_number"] == "QHS8X9ABCD"
    assert fake.store["products"][0]["stock_quantity"] == 5  # already held


def test_verify_receipt_from_failed_reholds_stock(monkeypatch, client, auth_user):
    fake = _setup(monkeypatch, "Payment Failed")

    resp = client.post("/orders/o1/verify-receipt", json={"receipt_number": "ABC123DEF4"})

    assert resp.status_code == 200
    assert fake.store["orders"][0]["status"] == "Paid"
    assert fake.store["products"][0]["stock_quantity"] == 3  # 5 - 2 held again


def test_verify_receipt_accepts_order_reference(monkeypatch, client, auth_user):
    fake = _setup(monkeypatch, "Pending PIN")

    resp = client.post("/orders/GWV-1/verify-receipt", json={"receipt_number": "REF999ABCD"})

    assert resp.status_code == 200
    assert fake.store["orders"][0]["status"] == "Paid"


def test_verify_receipt_requires_auth(monkeypatch, client):
    _setup(monkeypatch, "Pending PIN")

    resp = client.post("/orders/o1/verify-receipt", json={"receipt_number": "QHS8X9ABCD"})

    assert resp.status_code in (401, 403)


def test_verify_receipt_requires_code(monkeypatch, client, auth_user):
    _setup(monkeypatch, "Pending PIN")

    resp = client.post("/orders/o1/verify-receipt", json={"receipt_number": "   "})

    assert resp.status_code == 400


def test_verify_receipt_requires_ten_character_code(monkeypatch, client, auth_user):
    _setup(monkeypatch, "Pending PIN")

    resp = client.post("/orders/o1/verify-receipt", json={"receipt_number": "SHORT"})

    assert resp.status_code == 400


def test_verify_receipt_rejects_paid_status(monkeypatch, client, auth_user):
    _setup(monkeypatch, "Paid")

    resp = client.post("/orders/o1/verify-receipt", json={"receipt_number": "DUP123ABCD"})

    assert resp.status_code == 200  # idempotent


def test_verify_receipt_rejects_other_users_order(monkeypatch, client, auth_user):
    _setup(monkeypatch, "Pending PIN")

    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id="someone-else", email="other@example.com"
    )
    try:
        resp = client.post(
            "/orders/o1/verify-receipt", json={"receipt_number": "QHS8X9ABCD"}
        )
    finally:
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
            id="user-1", email="buyer@example.com"
        )

    assert resp.status_code == 403


def test_verify_receipt_rejects_reused_receipt(monkeypatch, client, auth_user):
    fake = _setup(monkeypatch, "Pending PIN")
    fake.store["orders"].append(
        {
            "id": "o2",
            "order_reference": "GWV-2",
            "user_id": "user-2",
            "status": "Paid",
            "receipt_number": "USED123456",
            "total_amount": 50,
            "items": [],
        }
    )

    resp = client.post("/orders/o1/verify-receipt", json={"receipt_number": "USED123456"})

    assert resp.status_code == 409
    assert fake.store["orders"][0]["status"] == "Pending PIN"
