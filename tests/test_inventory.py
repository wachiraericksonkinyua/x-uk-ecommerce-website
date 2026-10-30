"""Stock helpers must add inventory back exactly once."""

import app.services.inventory as inventory
from tests.fakes import FakeSupabase


def _store():
    fake = FakeSupabase()
    fake.store["orders"] = [
        {
            "id": "o1",
            "status": "Pending PIN",
            "items": [{"id": "p1", "qty": 2}, {"id": "p2", "qty": 1}],
        }
    ]
    fake.store["products"] = [
        {"id": "p1", "stock_quantity": 3},
        {"id": "p2", "stock_quantity": 0},
    ]
    return fake


def test_restore_order_stock_adds_each_item(monkeypatch):
    fake = _store()
    monkeypatch.setattr(inventory, "supabase", fake)

    inventory.restore_order_stock(fake.store["orders"][0])

    assert fake.store["products"][0]["stock_quantity"] == 5  # 3 + 2
    assert fake.store["products"][1]["stock_quantity"] == 1  # 0 + 1


def test_release_stock_once_flips_status_and_restores(monkeypatch):
    fake = _store()
    monkeypatch.setattr(inventory, "supabase", fake)
    order = fake.store["orders"][0]

    assert inventory.release_stock_once(order, "Cancelled") is True
    assert fake.store["orders"][0]["status"] == "Cancelled"
    assert fake.store["products"][0]["stock_quantity"] == 5


def test_release_stock_once_is_idempotent(monkeypatch):
    fake = _store()
    monkeypatch.setattr(inventory, "supabase", fake)
    order = fake.store["orders"][0]

    assert inventory.release_stock_once(order, "Cancelled") is True
    # Second call with the same (now stale) order object must not double-add stock.
    assert inventory.release_stock_once(order, "Cancelled") is False
    assert fake.store["products"][0]["stock_quantity"] == 5


def test_release_stock_once_ignores_paid_orders(monkeypatch):
    fake = _store()
    fake.store["orders"][0]["status"] = "Paid"
    monkeypatch.setattr(inventory, "supabase", fake)

    assert inventory.release_stock_once(fake.store["orders"][0], "Cancelled") is False
    assert fake.store["products"][0]["stock_quantity"] == 3  # untouched
