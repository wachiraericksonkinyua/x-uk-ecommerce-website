"""Admin product category synchronisation and backfill."""

from types import SimpleNamespace

import app.routers.admin.products as admin_products
import app.routers.products as products_router
import app.services.product_images as product_images
from app.dependencies import require_admin
from app.main import app
from tests.fakes import FakeSupabase


def _categories():
    return [
        {"id": "cat-1", "name": "Smartphones", "slug": "smartphones"},
        {"id": "cat-2", "name": "Chargers & Cables", "slug": "chargers-cables"},
        {"id": "cat-3", "name": "Power Banks", "slug": "power-banks"},
    ]


def test_resolve_category_by_id(monkeypatch):
    fake = FakeSupabase()
    fake.store["categories"] = _categories()
    monkeypatch.setattr(products_router, "supabase", fake)

    category_id, category_name = products_router.resolve_product_category("cat-2")

    assert category_id == "cat-2"
    assert category_name == "Chargers & Cables"


def test_resolve_category_by_name(monkeypatch):
    fake = FakeSupabase()
    fake.store["categories"] = _categories()
    monkeypatch.setattr(products_router, "supabase", fake)

    category_id, category_name = products_router.resolve_product_category(
        None, "Power Banks"
    )

    assert category_id == "cat-3"
    assert category_name == "Power Banks"


def test_admin_create_syncs_category_from_name(monkeypatch, client):
    fake = FakeSupabase()
    fake.store["categories"] = _categories()
    fake.store["products"] = []
    monkeypatch.setattr(products_router, "supabase", fake)
    monkeypatch.setattr(admin_products, "supabase", fake)
    monkeypatch.setattr(product_images, "supabase", fake)

    app.dependency_overrides[require_admin] = lambda: SimpleNamespace(id="admin-1")
    try:
        resp = client.post(
            "/admin/products",
            data={
                "name": "20,000mAh Power Bank",
                "price": "4500",
                "brand": "Anker",
                "description": "Fast-charging portable battery",
                "color": "Black",
                "category": "Power Banks",
                "stock_quantity": "12",
                "specs": '{"capacity":"20000mAh"}',
                "image_url": "https://example.com/power-bank.png",
            },
        )
    finally:
        app.dependency_overrides.pop(require_admin, None)

    assert resp.status_code == 201, resp.text
    created = fake.store["products"][0]
    assert created["category_id"] == "cat-3"
    assert created["category"] == "Power Banks"
    assert created["image_url"] == "https://example.com/power-bank.png"
    assert created["specs"] == {"capacity": "20000mAh"}


def test_admin_update_syncs_category_id_and_name(monkeypatch, client):
    fake = FakeSupabase()
    fake.store["categories"] = _categories()
    fake.store["products"] = [
        {
            "id": "p1",
            "name": "65W Charger",
            "category": None,
            "category_id": None,
            "stock_quantity": 10,
        }
    ]
    monkeypatch.setattr(products_router, "supabase", fake)
    monkeypatch.setattr(admin_products, "supabase", fake)

    app.dependency_overrides[require_admin] = lambda: SimpleNamespace(id="admin-1")
    try:
        resp = client.patch(
            "/admin/products/p1",
            json={"category": "Chargers & Cables"},
        )
    finally:
        app.dependency_overrides.pop(require_admin, None)

    assert resp.status_code == 200, resp.text
    assert fake.store["products"][0]["category_id"] == "cat-2"
    assert fake.store["products"][0]["category"] == "Chargers & Cables"


def test_backfill_maps_phone_and_named_categories(monkeypatch):
    fake = FakeSupabase()
    fake.store["categories"] = _categories()
    fake.store["products"] = [
        {
            "id": "p1",
            "name": "iPhone 13",
            "category": "phones",
            "category_id": None,
        },
        {
            "id": "p2",
            "name": "20,000mAh Power Bank",
            "category": "Power Banks",
            "category_id": None,
        },
        {
            "id": "p3",
            "name": "Already categorised",
            "category": "Smartphones",
            "category_id": "cat-1",
        },
    ]
    monkeypatch.setattr(products_router, "supabase", fake)

    updated = products_router.backfill_product_categories()

    assert updated == 2
    assert fake.store["products"][0]["category_id"] == "cat-1"
    assert fake.store["products"][0]["category"] == "Smartphones"
    assert fake.store["products"][1]["category_id"] == "cat-3"
    assert fake.store["products"][1]["category"] == "Power Banks"
