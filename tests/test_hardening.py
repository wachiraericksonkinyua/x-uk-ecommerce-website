"""Regression tests for the P0/P1 security hardening work."""

from types import SimpleNamespace

import app.routers.admin.analytics as admin_analytics
import app.routers.admin.orders as admin_orders
import app.routers.orders as orders_router
import app.services.inventory as inventory
from app.dependencies import get_current_user, require_admin
from app.main import app
from app.utils.search import sanitize_search_term
from tests.fakes import FakeSupabase


def _order(status="Paid"):
    return {
        "id": "o1",
        "order_reference": "GWV-1",
        "user_id": "user-1",
        "status": status,
        "total_amount": 100,
        "customer_email": "buyer@example.com",
        "customer_phone": "254712345678",
        "delivery_address": "Kilimani, Wood Avenue, Apt 4B",
        "receipt_number": "SECRET1234",
        "checkout_request_id": "ws_CO_secret",
        "items": [{"id": "p1", "qty": 2, "name": "Phone", "price": 50}],
        "created_at": "2026-01-01T10:00:00",
    }


def test_public_tracking_never_exposes_raw_pii(monkeypatch, client):
    fake = FakeSupabase()
    fake.store["orders"] = [_order()]
    monkeypatch.setattr(orders_router, "supabase", fake)

    resp = client.get("/orders/track/GWV-1")

    assert resp.status_code == 200
    payload = resp.json()["data"]
    body = resp.text
    assert "buyer@example.com" not in body
    assert "254712345678" not in body
    assert "Wood Avenue" not in body
    assert "SECRET1234" not in body
    assert "ws_CO_secret" not in body
    assert payload["customer_email"] == "b***@example.com"
    assert payload["customer_phone"].endswith("5678")
    assert "user_id" not in payload
    assert "receipt_number" not in payload


def test_checkout_rejects_non_mpesa_payment(monkeypatch, client):
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id="user-1", email="buyer@example.com"
    )
    try:
        resp = client.post(
            "/orders/checkout",
            json={
                "phone": "0712345678",
                "email": "buyer@example.com",
                "fulfillment": "Pickup",
                "payment_method": "Cash on Delivery",
                "items": [{"id": "p1", "name": "Phone", "price": 1, "qty": 1}],
                "total": 1,
            },
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert resp.status_code == 400
    assert "M-Pesa" in resp.json()["detail"]


def test_search_terms_strip_postgrest_syntax():
    raw = "iphone),or(id.eq.1),name.ilike.%*"
    clean = sanitize_search_term(raw)

    for character in (",", "(", ")", "*", '"'):
        assert character not in clean
    assert clean.startswith("iphone")


def test_admin_refund_restores_stock_and_marks_refunded(monkeypatch, client):
    fake = FakeSupabase()
    fake.store["orders"] = [_order(status="Paid")]
    fake.store["products"] = [{"id": "p1", "stock_quantity": 5}]
    monkeypatch.setattr(admin_orders, "supabase", fake)
    monkeypatch.setattr(inventory, "supabase", fake)

    app.dependency_overrides[require_admin] = lambda: SimpleNamespace(id="admin-1")
    try:
        resp = client.post(
            "/admin/orders/o1/refund",
            json={"reason": "Customer returned the item"},
        )
    finally:
        app.dependency_overrides.pop(require_admin, None)

    assert resp.status_code == 200, resp.text
    assert fake.store["orders"][0]["status"] == "Refunded"
    assert fake.store["orders"][0]["refund_reason"] == "Customer returned the item"
    assert fake.store["products"][0]["stock_quantity"] == 7


def test_admin_refund_is_idempotent(monkeypatch, client):
    fake = FakeSupabase()
    fake.store["orders"] = [_order(status="Refunded")]
    fake.store["products"] = [{"id": "p1", "stock_quantity": 5}]
    monkeypatch.setattr(admin_orders, "supabase", fake)
    monkeypatch.setattr(inventory, "supabase", fake)

    app.dependency_overrides[require_admin] = lambda: SimpleNamespace(id="admin-1")
    try:
        resp = client.post("/admin/orders/o1/refund", json={})
    finally:
        app.dependency_overrides.pop(require_admin, None)

    assert resp.status_code == 200
    assert fake.store["products"][0]["stock_quantity"] == 5


def test_sales_analytics_reports_revenue_and_stock_alerts(monkeypatch, client):
    fake = FakeSupabase()
    fake.store["orders"] = [
        {
            **_order(status="Paid"),
            "created_at": "2026-11-03T09:00:00",
            "items": [{"id": "p1", "qty": 2, "name": "Charger", "price": 50}],
        },
        {
            **_order(status="Refunded"),
            "id": "o2",
            "order_reference": "GWV-2",
            "total_amount": 80,
            "refund_amount": 80,
            "created_at": "2026-11-03T10:00:00",
            "items": [{"id": "p1", "qty": 1, "name": "Charger", "price": 80}],
        },
    ]
    fake.store["products"] = [
        {"id": "p1", "name": "Charger", "stock_quantity": 2, "price": 50}
    ]
    fake.store["inventory_movements"] = [
        {
            "id": "m1",
            "product_id": "p1",
            "change_qty": -2,
            "reason": "sale",
            "created_at": "2026-11-03T09:00:00",
        }
    ]
    monkeypatch.setattr(admin_analytics, "supabase", fake)

    app.dependency_overrides[require_admin] = lambda: SimpleNamespace(id="admin-1")
    try:
        resp = client.get("/admin/analytics/sales?days=14")
    finally:
        app.dependency_overrides.pop(require_admin, None)

    assert resp.status_code == 200, resp.text
    payload = resp.json()
    assert payload["revenue"]["gross"] == 100
    assert payload["revenue"]["refunded"] == 80
    assert payload["revenue"]["net"] == 20
    assert payload["units_sold"] == 2
    assert payload["stock_alerts"][0]["name"] == "Charger"
    assert payload["movements"][0]["product_name"] == "Charger"


def test_admin_can_verify_suspicious_order(monkeypatch, client):
    fake = FakeSupabase()
    fake.store["orders"] = [_order(status="Paid")]
    monkeypatch.setattr(admin_orders, "supabase", fake)

    app.dependency_overrides[require_admin] = lambda: SimpleNamespace(id="admin-1")
    try:
        resp = client.post(
            "/admin/orders/o1/verify",
            json={"verified": True, "note": "Called customer and confirmed"},
        )
    finally:
        app.dependency_overrides.pop(require_admin, None)

    assert resp.status_code == 200, resp.text
    assert fake.store["orders"][0]["is_verified"] is True
    assert fake.store["orders"][0]["verification_note"] == "Called customer and confirmed"
