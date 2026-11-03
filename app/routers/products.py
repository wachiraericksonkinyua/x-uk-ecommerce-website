import json
from typing import Any, List, Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Query

from app.database import supabase
from app.dependencies import require_admin, get_optional_user
from app.routers.reviews import list_product_reviews
from app.services.product_images import (
    add_product_image_row,
    save_product_images,
    upload_product_file,
)
from app.utils.search import sanitize_search_term

router = APIRouter(prefix="/products", tags=["products"])


OPTIONAL_PRODUCT_FIELDS = ("specs", "compatibility")


def parse_specs_json(raw: Optional[str]) -> dict:
    """Parse an admin-supplied JSON object of technical specs."""
    if not raw or not raw.strip():
        return {}
    try:
        value: Any = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Specs must be valid JSON")
    if not isinstance(value, dict):
        raise HTTPException(status_code=400, detail="Specs must be a JSON object")
    return value


def resolve_product_category(
    category_id: Optional[str] = None,
    category: Optional[str] = None,
) -> tuple[Optional[str], Optional[str]]:
    """Resolve a category UUID and human-readable name from either input.

    - ``category_id`` wins when it matches a row in ``public.categories``.
    - Otherwise a name/slug is looked up case-insensitively.
    - If the schema/table is unavailable, the caller's values are preserved.
    """
    raw_id = (category_id or "").strip() or None
    raw_name = (category or "").strip() or None

    if raw_id:
        try:
            res = (
                supabase.table("categories")
                .select("id, name")
                .eq("id", raw_id)
                .limit(1)
                .execute()
            )
            if res.data and isinstance(res.data[0], dict):
                row = res.data[0]
                return str(row.get("id") or raw_id), row.get("name") or raw_name
        except Exception as exc:
            print(f"[products] category id lookup failed: {exc}")

    if raw_name:
        term = sanitize_search_term(raw_name)
        if term:
            try:
                res = (
                    supabase.table("categories")
                    .select("id, name")
                    .or_(f"name.ilike.%{term}%,slug.ilike.%{term}%")
                    .limit(1)
                    .execute()
                )
                if res.data and isinstance(res.data[0], dict):
                    row = res.data[0]
                    return str(row.get("id") or ""), row.get("name") or raw_name
            except Exception as exc:
                print(f"[products] category name lookup failed: {exc}")

    return raw_id, raw_name


def backfill_product_categories() -> int:
    """Map products without category_id to a real category row.

    This is a runtime safety net for deployments that cannot run migration 008;
    the SQL migration remains the primary one-time backfill.
    """
    try:
        categories = (
            supabase.table("categories").select("id, name, slug").execute().data or []
        )
        products = (
            supabase.table("products")
            .select("id, name, category, category_id")
            .execute()
            .data
            or []
        )
    except Exception as exc:
        print(f"[products] category backfill skipped: {exc}")
        return 0

    by_name = {}
    smartphone_id = None
    for row in categories:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or "").strip().lower()
        slug = str(row.get("slug") or "").strip().lower()
        if name:
            by_name[name] = row
        if slug:
            by_name[slug] = row
        if name == "smartphones" or slug == "smartphones":
            smartphone_id = row.get("id")

    updated = 0
    for product in products:
        if not isinstance(product, dict) or product.get("category_id"):
            continue

        text = str(product.get("category") or "").strip().lower()
        match = by_name.get(text)
        if not match and (
            not text
            or "phone" in text
            or "mobile" in text
            or "smartphone" in text
        ) and smartphone_id:
            match = {"id": smartphone_id, "name": "Smartphones"}
        if not match:
            continue

        try:
            supabase.table("products").update(
                {"category_id": match.get("id"), "category": match.get("name")}
            ).eq("id", product.get("id")).execute()
            updated += 1
        except Exception as exc:
            print(f"[products] category backfill update failed: {exc}")
    return updated


def _is_optional_column_error(exc: Exception) -> bool:
    """True when PostgREST reports a missing specs/compatibility column."""
    message = str(exc).lower()
    mentions_column = any(
        token in message
        for token in ("column", "schema cache", "does not exist", "pgrst204")
    )
    mentions_optional = any(field in message for field in OPTIONAL_PRODUCT_FIELDS)
    return mentions_column and mentions_optional


def insert_product_record(data: dict):
    """Insert a product, degrading gracefully if migration 007 is incomplete."""
    try:
        return supabase.table("products").insert(data).execute()
    except Exception as exc:
        if not _is_optional_column_error(exc):
            raise
        fallback = {
            key: value
            for key, value in data.items()
            if key not in OPTIONAL_PRODUCT_FIELDS
        }
        print(f"[products] optional columns unavailable; retrying without them: {exc}")
        return supabase.table("products").insert(fallback).execute()


def update_product_record(product_id: str, data: dict):
    """Update a product, dropping optional fields if the schema is incomplete."""
    try:
        return supabase.table("products").update(data).eq("id", product_id).execute()
    except Exception as exc:
        if not _is_optional_column_error(exc):
            raise
        fallback = {
            key: value
            for key, value in data.items()
            if key not in OPTIONAL_PRODUCT_FIELDS
        }
        print(f"[products] optional columns unavailable; retrying without them: {exc}")
        return (
            supabase.table("products")
            .update(fallback)
            .eq("id", product_id)
            .execute()
        )


def _apply_product_filters(
    query,
    *,
    search: Optional[str],
    category: Optional[str],
    brand: Optional[str],
    color: Optional[str],
    min_price: Optional[float],
    max_price: Optional[float],
    sort_by: Optional[str],
    order: Optional[str],
):
    if search:
        term = sanitize_search_term(search)
        if term:
            query = query.or_(
                f"name.ilike.%{term}%,brand.ilike.%{term}%,description.ilike.%{term}%"
            )
    if category:
        term = sanitize_search_term(category)
        matched_id = None
        if term:
            try:
                category_match = (
                    supabase.table("categories")
                    .select("id")
                    .or_(f"slug.ilike.%{term}%,name.ilike.%{term}%")
                    .limit(1)
                    .execute()
                )
                if category_match.data:
                    matched_id = category_match.data[0].get("id")
            except Exception:
                matched_id = None
        if matched_id:
            query = query.or_(
                f"category.ilike.%{term}%,category_id.eq.{matched_id}"
            )
        elif term:
            query = query.ilike("category", f"%{term}%")
    if brand:
        term = sanitize_search_term(brand)
        if term:
            query = query.ilike("brand", f"%{term}%")
    if color:
        term = sanitize_search_term(color)
        if term:
            query = query.ilike("color", f"%{term}%")
    if min_price is not None:
        query = query.gte("price", min_price)
    if max_price is not None:
        query = query.lte("price", max_price)

    sort_field = sort_by or "created_at"
    order_value = (order or "desc").lower()
    query = query.order(sort_field, desc=order_value == "desc")
    return query


def _product_query(select_clause: str, **filters):
    query = supabase.table("products").select(select_clause)
    return _apply_product_filters(query, **filters).execute()


# @router.get("/")
# async def get_products():
#     response = supabase.table("products").select("*").execute()
#     return {"data": response.data}
@router.get("/")
def get_products(
    search: Optional[str] = Query(None, description="Search by name"),
    category: Optional[str] = Query(None, description="Filter by category"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    color: Optional[str] = Query(None, description="Filter by color"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    sort_by: Optional[str] = Query("created_at", description="Sort field: price or created_at"),
    order: Optional[str] = Query("desc", description="Sort order: asc or desc")
):
    filters = {
        "search": search,
        "category": category,
        "brand": brand,
        "color": color,
        "min_price": min_price,
        "max_price": max_price,
        "sort_by": sort_by,
        "order": order,
    }

    try:
        response = _product_query("*, product_images(image_url)", **filters)
        return {"success": True, "data": response.data}
    except Exception as exc:
        # A partially-applied schema (missing product_images / optional columns)
        # must not take the storefront down. Retry with the base product table.
        print(f"[products] relationship query failed; using fallback: {exc}")
        try:
            response = _product_query("*", **filters)
            return {
                "success": True,
                "data": response.data,
                "degraded": True,
                "warning": "Product images are temporarily unavailable.",
            }
        except Exception as fallback_exc:
            print(f"[products] product list unavailable: {fallback_exc}")
            return {
                "success": False,
                "data": [],
                "message": "Products are temporarily unavailable. Please try again.",
            }

@router.post("/")
async def create_product(
    name: str = Form(...),
    price: float = Form(...),
    brand: str = Form(...),
    images: List[UploadFile] = File(default=[]),
    description: str = Form(...),
    color: str = Form(...),
    category_id: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    stock_quantity: int = Form(0),
    compatibility: Optional[str] = Form(None),
    specs: Optional[str] = Form(None),
    image_url: Optional[str] = Form(None),
    primary_image: Optional[UploadFile] = File(None),
    admin_user = Depends(require_admin)
):
    resolved_id, resolved_name = resolve_product_category(category_id, category)
    primary_url = upload_product_file(primary_image) if primary_image else None
    new_product = {
        "name": name,
        "price": price,
        "brand": brand,
        "description": description,
        "color": color,
        "category_id": resolved_id,
        "category": resolved_name,
        "stock_quantity": max(0, stock_quantity),
        "compatibility": compatibility or None,
        "specs": parse_specs_json(specs),
        "image_url": primary_url or (image_url or "").strip() or None,
    }
    product_response = insert_product_record(new_product)

    # Safely extract the ID from the response data
    product_data = product_response.data
    if not isinstance(product_data, list) or len(product_data) == 0:
        return {"error": "Failed to create product"}

    created_product = product_data[0]
    if not isinstance(created_product, dict):
        return {"error": "Failed to create product"}

    product_id = created_product.get("id")
    if product_id is None:
        return {"error": "Failed to create product"}

    saved_images = []
    try:
        if primary_url:
            saved_images.append(add_product_image_row(product_id, primary_url))
        elif new_product["image_url"]:
            saved_images.append(add_product_image_row(product_id, new_product["image_url"]))
        saved_images.extend(save_product_images(product_id, images or []))
    except Exception as image_exc:
        print(f"[products] gallery persistence skipped: {image_exc}")

    return {
        "success": True,
        "message": "Product and images added successfully",
        "data": {**created_product, "product_images": saved_images},
    }


@router.patch("/{product_id}")
async def update_product(
    product_id: str,
    name: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    brand: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    color: Optional[str] = Form(None),
    category_id: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    stock_quantity: Optional[int] = Form(None),
    compatibility: Optional[str] = Form(None),
    specs: Optional[str] = Form(None),
    image_url: Optional[str] = Form(None),
    admin_user = Depends(require_admin)
):
    # 1. Build a dictionary containing only the fields the user actually provided
    update_data = {}
    if name: update_data["name"] = name
    if price: update_data["price"] = price
    if brand: update_data["brand"] = brand
    if description: update_data["description"] = description
    if color: update_data["color"] = color
    if category_id is not None or category is not None:
        resolved_id, resolved_name = resolve_product_category(category_id, category)
        update_data["category_id"] = resolved_id
        update_data["category"] = resolved_name
    if stock_quantity is not None: update_data["stock_quantity"] = stock_quantity
    if compatibility is not None: update_data["compatibility"] = compatibility or None
    if specs is not None: update_data["specs"] = parse_specs_json(specs)
    if image_url is not None:
        update_data["image_url"] = image_url.strip() or None

    # 2. Stop the function if they didn't send anything to update
    if not update_data:
        return {"error": "No new data provided"}

    # 3. Push the changes to the exact product row
    update_product_record(product_id, update_data)
    
    return {"message": f"Product {product_id} updated perfectly!"}


@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    admin_user = Depends(require_admin)
                               ):
    # Note: To avoid paying for dead storage, you should ideally write a quick loop here 
    # to fetch the image URLs and delete them from the Supabase storage bucket first!
    
    # Delete the main product record from the database
    supabase.table("products").delete().eq("id", product_id).execute()
    
    return {"message": f"Product {product_id} is completely gone."}

@router.get("/{product_id}/reviews")
def get_product_reviews_alias(product_id: str, current_user = Depends(get_optional_user)):
    """Public reviews for a product (approved only unless fetched by an admin)."""
    return list_product_reviews(product_id, current_user)


@router.get("/{product_id}")
async def get_single_product(product_id: str):
    # Fetch the product and its related images simultaneously. If the images
    # relationship is not available yet, retry without it instead of failing.
    try:
        response = (
            supabase.table("products")
            .select("*, product_images(image_url)")
            .eq("id", product_id)
            .execute()
        )
    except Exception as exc:
        print(f"[products] product detail relationship failed; retrying base: {exc}")
        try:
            response = (
                supabase.table("products")
                .select("*")
                .eq("id", product_id)
                .execute()
            )
        except Exception as fallback_exc:
            print(f"[products] product detail unavailable: {fallback_exc}")
            return {
                "success": False,
                "data": None,
                "message": "Product is temporarily unavailable. Please try again.",
            }

    if not response.data or len(response.data) == 0:
        raise HTTPException(status_code=404, detail="Product not found")

    return {"success": True, "data": response.data[0]}

