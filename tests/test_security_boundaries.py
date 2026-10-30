"""The security fixes must stay fixed.

These tests call the app WITHOUT a token and assert protected routes refuse,
while public routes stay open. No database is touched.
"""

from app.main import app


def test_health_is_public(client):
    assert client.get("/health").status_code == 200


def test_root_is_public(client):
    assert client.get("/").status_code == 200


def test_admin_routes_require_auth(client):
    assert client.get("/admin/orders").status_code in (401, 403)
    assert client.get("/admin/dashboard/summary").status_code in (401, 403)


def test_cart_requires_auth(client):
    assert client.get("/cart/").status_code in (401, 403)


def test_wishlist_requires_auth(client):
    assert client.get("/wishlist/").status_code in (401, 403)


def test_checkout_requires_auth(client):
    # a guest can browse but must NOT be able to pay
    resp = client.post("/orders/checkout", json={})
    assert resp.status_code in (401, 403)


def test_create_product_requires_auth(client):
    resp = client.post("/products/")
    assert resp.status_code in (401, 403, 422)


def test_public_routes_are_not_secured():
    schema = app.openapi()
    for path in ("/products/", "/categories/", "/delivery/locations", "/health"):
        get_op = schema["paths"][path].get("get", {})
        assert "security" not in get_op, f"{path} should be public"


def test_whatsapp_webhook_accepts_when_signature_not_configured(client):
    # WHATSAPP_APP_SECRET is unset in tests, so the check is skipped
    resp = client.post("/webhooks/whatsapp", json={"entry": []})
    assert resp.status_code == 200
