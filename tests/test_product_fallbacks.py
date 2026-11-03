"""Product schema fallbacks for partially-applied migrations."""

from types import SimpleNamespace

import app.routers.products as products_router


def test_product_list_falls_back_when_images_relation_is_missing(monkeypatch, client):
    def fake_query(select_clause, **filters):
        if "product_images" in select_clause:
            raise RuntimeError("relation product_images does not exist")
        return SimpleNamespace(
            data=[{"id": "p1", "name": "USB-C Charger", "price": 2500}]
        )

    monkeypatch.setattr(products_router, "_product_query", fake_query)

    resp = client.get("/products/")

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    assert payload["degraded"] is True
    assert payload["data"][0]["name"] == "USB-C Charger"


def test_product_list_returns_safe_empty_state_when_database_fails(monkeypatch, client):
    def failing_query(select_clause, **filters):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(products_router, "_product_query", failing_query)

    resp = client.get("/products/")

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is False
    assert payload["data"] == []


def test_insert_retries_without_optional_columns(monkeypatch):
    inserted = []

    class Table:
        def insert(self, data):
            if "specs" in data or "compatibility" in data:
                raise RuntimeError(
                    "Could not find the 'specs' column of 'products' in the schema cache"
                )
            inserted.append(data)
            return self

        def execute(self):
            return SimpleNamespace(data=inserted)

    monkeypatch.setattr(
        products_router, "supabase", SimpleNamespace(table=lambda name: Table())
    )

    products_router.insert_product_record(
        {
            "name": "65W GaN Charger",
            "price": 4500,
            "specs": {"wattage": "65W"},
            "compatibility": "USB-C",
        }
    )

    assert inserted
    assert "specs" not in inserted[0]
    assert "compatibility" not in inserted[0]
    assert inserted[0]["name"] == "65W GaN Charger"


def test_update_retries_without_optional_columns(monkeypatch):
    updates = []

    class Table:
        def update(self, data):
            if "specs" in data:
                raise RuntimeError(
                    "column products.specs does not exist"
                )
            updates.append(data)
            return self

        def eq(self, *args):
            return self

        def execute(self):
            return SimpleNamespace(data=[{"id": "p1", **updates[-1]}])

    monkeypatch.setattr(
        products_router, "supabase", SimpleNamespace(table=lambda name: Table())
    )

    products_router.update_product_record("p1", {"name": "Updated", "specs": {}})

    assert updates
    assert "specs" not in updates[0]
    assert updates[0]["name"] == "Updated"
