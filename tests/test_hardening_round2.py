"""Regression tests for the second hardening pass (checkout, cart, uploads)."""

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

import app.routers.cart as cart_router
import app.routers.orders as orders_router
import app.routers.reviews as reviews_router
import app.services.inventory as inventory
import app.services.mpesa as mpesa
import app.utils.images as images
from app.dependencies import get_current_user
from app.main import app
from tests.fakes import FakeSupabase


def _auth(monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id="user-1", email="buyer@example.com"
    )


def _clear_auth():
    app.dependency_overrides.pop(get_current_user, None)


# --------------------------------------------------------------------------- #
# Stock
# --------------------------------------------------------------------------- #
def test_restore_items_only_touches_applied_lines(monkeypatch):
    fake = FakeSupabase()
    fake.store["products"] = [
        {"id": "p1", "stock_quantity": 3},
        {"id": "p2", "stock_quantity": 5},
    ]
    monkeypatch.setattr(inventory, "supabase", fake)

    inventory.restore_items(
        [{"id": "p1", "qty": 2}], order_id="o1", reason="checkout_rollback"
    )

    assert fake.store["products"][0]["stock_quantity"] == 5
    # p2 was never decremented, so it must be untouched.
    assert fake.store["products"][1]["stock_quantity"] == 5


def test_checkout_rollback_restores_only_decremented_lines(monkeypatch):
    fake = FakeSupabase()
    fake.store["products"] = [
        {"id": "p1", "name": "Phone", "price": 100, "stock_quantity": 5},
        {"id": "p2", "name": "Case", "price": 20, "stock_quantity": 5},
    ]

    # Make the second product update fail after the first one succeeded.
    original_table = fake.table

    def table(name):
        table_obj = original_table(name)
        if name == "products":
            original_execute = table_obj.execute

            def execute():
                if table_obj._update is not None and table_obj._conditions.get("id") == "p2":
                    raise RuntimeError("simulated products update failure")
                return original_execute()

            table_obj.execute = execute
        return table_obj

    fake.table = table
    monkeypatch.setattr(orders_router, "supabase", fake)
    monkeypatch.setattr(inventory, "supabase", fake)
    monkeypatch.setattr(orders_router, "record_inventory_movement", lambda **_: None)

    _auth(monkeypatch)
    try:
        resp = client_post_checkout()
    finally:
        _clear_auth()

    assert resp.status_code == 500
    assert fake.store["orders"] == []  # dangling order removed
    assert fake.store["products"][0]["stock_quantity"] == 5  # p1 rolled back
    assert fake.store["products"][1]["stock_quantity"] == 5  # p2 never touched


def client_post_checkout():
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        return client.post(
            "/orders/checkout",
            json={
                "phone": "0712345678",
                "email": "buyer@example.com",
                "fulfillment": "Pickup",
                "payment_method": "M-Pesa",
                "items": [
                    {"id": "p1", "name": "Phone", "price": 100, "qty": 1},
                    {"id": "p2", "name": "Case", "price": 20, "qty": 1},
                ],
                "total": 120,
            },
        )


def test_late_success_reholds_released_stock(monkeypatch):
    fake = FakeSupabase()
    fake.store["orders"] = [
        {
            "id": "o1",
            "order_reference": "GWV-1",
            "checkout_request_id": "ws_CO_1",
            "status": "Payment Failed",
            "total_amount": 100,
            "customer_email": "buyer@example.com",
            "items": [{"id": "p1", "qty": 2}],
        }
    ]
    fake.store["products"] = [{"id": "p1", "stock_quantity": 8}]
    monkeypatch.setattr(mpesa, "supabase", fake)
    monkeypatch.setattr(inventory, "supabase", fake)
    monkeypatch.setattr(mpesa, "send_receipt_email", lambda *a: None)

    status = mpesa.apply_stk_result("ws_CO_1", "0")

    assert status == "Paid"
    assert fake.store["orders"][0]["status"] == "Paid"
    assert fake.store["products"][0]["stock_quantity"] == 6  # re-held 2 units


def test_order_reference_has_collision_safe_entropy():
    reference = orders_router.generate_order_reference()
    assert reference.startswith("GWV-")
    assert len(reference) == 12  # GWV- + 8 hex characters
    int(reference.split("-")[1], 16)  # valid hex


# --------------------------------------------------------------------------- #
# Cart
# --------------------------------------------------------------------------- #
def test_cart_add_rejects_unknown_product(monkeypatch):
    fake = FakeSupabase()
    fake.store["products"] = []
    monkeypatch.setattr(cart_router, "supabase", fake)

    _auth(monkeypatch)
    try:
        resp = client_post("/cart/add", {"product_id": "missing", "quantity": 1})
    finally:
        _clear_auth()

    assert resp.status_code == 404


def test_cart_add_rejects_more_than_stock(monkeypatch):
    fake = FakeSupabase()
    fake.store["products"] = [{"id": "p1", "name": "Phone", "stock_quantity": 1}]
    monkeypatch.setattr(cart_router, "supabase", fake)

    _auth(monkeypatch)
    try:
        resp = client_post("/cart/add", {"product_id": "p1", "quantity": 2})
    finally:
        _clear_auth()

    assert resp.status_code == 400


def test_cart_add_increments_existing_within_stock(monkeypatch):
    fake = FakeSupabase()
    fake.store["products"] = [{"id": "p1", "name": "Phone", "stock_quantity": 5}]
    fake.store["cart_items"] = [
        {"id": "c1", "user_id": "user-1", "product_id": "p1", "quantity": 1}
    ]
    monkeypatch.setattr(cart_router, "supabase", fake)

    _auth(monkeypatch)
    try:
        resp = client_post("/cart/add", {"product_id": "p1", "quantity": 2})
    finally:
        _clear_auth()

    assert resp.status_code == 200
    assert fake.store["cart_items"][0]["quantity"] == 3


# --------------------------------------------------------------------------- #
# Reviews
# --------------------------------------------------------------------------- #
def test_review_rejects_cancelled_order(monkeypatch):
    fake = FakeSupabase()
    fake.store["orders"] = [
        {"id": "o1", "user_id": "user-1", "status": "Cancelled", "items": [{"id": "p1"}]}
    ]
    fake.store["reviews"] = []
    monkeypatch.setattr(reviews_router, "supabase", fake)

    _auth(monkeypatch)
    try:
        resp = client_post("/reviews/", {"product_id": "p1", "rating": 5, "comment": "Nice"})
    finally:
        _clear_auth()

    assert resp.status_code == 403


def test_review_accepts_paid_order(monkeypatch):
    fake = FakeSupabase()
    fake.store["orders"] = [
        {"id": "o1", "user_id": "user-1", "status": "Paid", "items": [{"id": "p1"}]}
    ]
    fake.store["reviews"] = []
    monkeypatch.setattr(reviews_router, "supabase", fake)

    _auth(monkeypatch)
    try:
        resp = client_post("/reviews/", {"product_id": "p1", "rating": 5, "comment": "Nice"})
    finally:
        _clear_auth()

    assert resp.status_code == 200
    assert fake.store["reviews"][0]["is_approved"] is False


# --------------------------------------------------------------------------- #
# Uploads
# --------------------------------------------------------------------------- #
def test_image_validation_accepts_real_jpeg():
    assert images.validate_image_bytes(b"\xff\xd8\xff\xe0rest", "image/jpeg") == "image/jpeg"


def test_image_validation_rejects_non_image():
    with pytest.raises(HTTPException) as exc:
        images.validate_image_bytes(b"<script>alert(1)</script>", "image/png")
    assert exc.value.status_code == 400


def test_image_validation_rejects_oversized_files():
    payload = b"\xff\xd8\xff" + b"0" * images.MAX_IMAGE_BYTES
    with pytest.raises(HTTPException) as exc:
        images.validate_image_bytes(payload, "image/jpeg")
    assert exc.value.status_code == 400


def client_post(path, payload):
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        return client.post(path, json=payload)
