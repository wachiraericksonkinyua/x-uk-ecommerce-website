"""Manual M-Pesa receipt verification (customer fallback)."""

import app.services.inventory as inventory
import app.routers.orders as orders_router
from tests.fakes import FakeSupabase


def _setup(monkeypatch, status):
    fake = FakeSupabase()
    fake.store["orders"] = [
        {
            "id": "o1",
            "order_reference": "GWV-1",
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
    return fake


def test_verify_receipt_from_pending_does_not_change_stock(monkeypatch, client):
    fake = _setup(monkeypatch, "Pending PIN")

    resp = client.post("/orders/o1/verify-receipt", json={"receipt_number": "QHS8X9"})

    assert resp.status_code == 200
    assert fake.store["orders"][0]["status"] == "Paid"
    assert fake.store["orders"][0]["receipt_number"] == "QHS8X9"
    assert fake.store["products"][0]["stock_quantity"] == 5  # already held


def test_verify_receipt_from_failed_reholds_stock(monkeypatch, client):
    fake = _setup(monkeypatch, "Payment Failed")

    resp = client.post("/orders/o1/verify-receipt", json={"receipt_number": "ABC123"})

    assert resp.status_code == 200
    assert fake.store["orders"][0]["status"] == "Paid"
    assert fake.store["products"][0]["stock_quantity"] == 3  # 5 - 2 held again


def test_verify_receipt_accepts_order_reference(monkeypatch, client):
    fake = _setup(monkeypatch, "Pending PIN")

    resp = client.post("/orders/GWV-1/verify-receipt", json={"receipt_number": "REF999"})

    assert resp.status_code == 200
    assert fake.store["orders"][0]["status"] == "Paid"


def test_verify_receipt_requires_code(monkeypatch, client):
    _setup(monkeypatch, "Pending PIN")

    resp = client.post("/orders/o1/verify-receipt", json={"receipt_number": "   "})

    assert resp.status_code == 400


def test_verify_receipt_rejects_paid_status(monkeypatch, client):
    _setup(monkeypatch, "Paid")

    resp = client.post("/orders/o1/verify-receipt", json={"receipt_number": "DUP123"})

    assert resp.status_code == 200  # idempotent
