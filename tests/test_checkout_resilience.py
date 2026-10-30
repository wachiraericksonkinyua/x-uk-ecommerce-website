"""Checkout must never fail/ release stock when Daraja is slow or unreachable."""

from types import SimpleNamespace

import httpx

import app.routers.orders as orders_router
from app.dependencies import get_current_user
from app.main import app
from tests.fakes import FakeSupabase


class _RaisingDaraja:
    """Stands in for DarajaService when Safaricom times out."""

    async def send_stk_push(self, **kwargs):
        raise httpx.TimeoutException("simulated Daraja timeout")


def test_checkout_stays_pending_when_daraja_times_out(monkeypatch, client):
    fake = FakeSupabase()
    fake.store["products"] = [
        {"id": "p1", "name": "Phone", "price": 100, "stock_quantity": 5}
    ]
    monkeypatch.setattr(orders_router, "supabase", fake)
    monkeypatch.setattr(orders_router, "DarajaService", _RaisingDaraja)

    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id="user-1")
    try:
        resp = client.post(
            "/orders/checkout",
            json={
                "phone": "0712345678",
                "email": "buyer@example.com",
                "fulfillment": "Pickup",
                "payment_method": "M-Pesa",
                "items": [{"id": "p1", "name": "Phone", "price": 100, "qty": 1}],
                "total": 100,
            },
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert resp.status_code == 201, resp.text
    assert fake.store["orders"][0]["status"] == "Pending PIN"
    assert fake.store["products"][0]["stock_quantity"] == 4  # stock still held
