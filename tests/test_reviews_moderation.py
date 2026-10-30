"""Product reviews are hidden until an admin approves them."""

import app.routers.admin.reviews as admin_reviews
import app.routers.reviews as reviews_router
from app.dependencies import require_admin
from app.main import app
from tests.fakes import FakeSupabase


def _store():
    fake = FakeSupabase()
    fake.store["reviews"] = [
        {"id": "r1", "product_id": "p1", "rating": 5, "comment": "Great", "is_approved": True},
        {"id": "r2", "product_id": "p1", "rating": 1, "comment": "Bad", "is_approved": False},
    ]
    return fake


def test_public_reviews_only_return_approved(monkeypatch, client):
    fake = _store()
    monkeypatch.setattr(reviews_router, "supabase", fake)

    resp = client.get("/reviews/p1")

    assert resp.status_code == 200
    assert [r["id"] for r in resp.json()["data"]] == ["r1"]


def test_products_alias_only_returns_approved(monkeypatch, client):
    fake = _store()
    monkeypatch.setattr(reviews_router, "supabase", fake)

    resp = client.get("/products/p1/reviews")

    assert resp.status_code == 200
    assert [r["id"] for r in resp.json()["data"]] == ["r1"]


def test_admin_can_approve_review(monkeypatch, client):
    fake = _store()
    monkeypatch.setattr(admin_reviews, "supabase", fake)
    app.dependency_overrides[require_admin] = lambda: object()
    try:
        resp = client.patch("/admin/reviews/r2/approve", json={"is_approved": True})
    finally:
        app.dependency_overrides.pop(require_admin, None)

    assert resp.status_code == 200
    assert fake.store["reviews"][1]["is_approved"] is True


def test_admin_can_hide_review(monkeypatch, client):
    fake = _store()
    monkeypatch.setattr(admin_reviews, "supabase", fake)
    app.dependency_overrides[require_admin] = lambda: object()
    try:
        resp = client.patch("/admin/reviews/r1/approve", json={"is_approved": False})
    finally:
        app.dependency_overrides.pop(require_admin, None)

    assert resp.status_code == 200
    assert fake.store["reviews"][0]["is_approved"] is False
