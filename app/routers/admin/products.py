from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from app.database import supabase
from app.routers.products import (
    backfill_product_categories,
    insert_product_record,
    parse_specs_json,
    resolve_product_category,
    update_product_record,
)
from app.services.inventory import record_inventory_movement
from app.services.product_images import (
    add_product_image_row,
    save_product_images,
    storage_path_from_url,
    upload_product_file,
)
from app.utils.pagination import page_range
from app.utils.search import sanitize_search_term

router = APIRouter(prefix="/products", tags=["Admin · Products"])

IMAGE_BUCKET = "product-images"


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    brand: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    category: Optional[str] = None
    category_id: Optional[str] = None
    stock_quantity: Optional[int] = Field(None, ge=0)
    compatibility: Optional[str] = None
    specs: Optional[Dict[str, Any]] = None
    image_url: Optional[str] = None


@router.post("", status_code=201)
async def create_product(
    name: str = Form(...),
    price: float = Form(...),
    brand: str = Form("General"),
    description: str = Form(""),
    color: str = Form(""),
    category_id: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    stock_quantity: int = Form(0),
    compatibility: Optional[str] = Form(None),
    specs: Optional[str] = Form(None),
    image_url: Optional[str] = Form(None),
    primary_image: Optional[UploadFile] = File(None),
    images: List[UploadFile] = File(default=[]),
):
    """Create a product with category sync and primary/gallery images."""
    try:
        resolved_id, resolved_name = resolve_product_category(category_id, category)
        primary_url = upload_product_file(primary_image) if primary_image else None
        data = {
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
        response = insert_product_record(data)
        if not response.data or not isinstance(response.data[0], dict):
            raise HTTPException(status_code=400, detail="Failed to create product")
        product = response.data[0]

        saved_images = []
        try:
            if primary_url:
                saved_images.append(add_product_image_row(product["id"], primary_url))
            elif data["image_url"]:
                saved_images.append(
                    add_product_image_row(product["id"], data["image_url"])
                )
            saved_images.extend(save_product_images(product["id"], images or []))
        except Exception as image_exc:
            # The product (and primary URL) are already saved; a gallery-table
            # problem must not turn a successful create into a 400.
            print(f"[admin-products] gallery persistence skipped: {image_exc}")

        return {
            "success": True,
            "data": {**product, "product_images": saved_images},
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/backfill-categories")
def backfill_categories():
    """One-time/manual helper: map products with no category_id."""
    updated = backfill_product_categories()
    return {
        "success": True,
        "updated": updated,
        "message": f"Backfilled {updated} product(s)",
    }


@router.get("")
def list_products(
    search: Optional[str] = Query(None),
    category_id: Optional[str] = Query(None),
    low_stock: Optional[bool] = Query(None, description="Only products with stock < 5"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    try:
        query = supabase.table("products").select("*", count="exact")
        if search:
            term = sanitize_search_term(search)
            if term:
                query = query.ilike("name", f"%{term}%")
        if category_id:
            query = query.eq("category_id", category_id)
        if low_stock:
            query = query.lt("stock_quantity", 5)
        start, end = page_range(page, page_size)
        response = query.order("created_at", desc=True).range(start, end).execute()
        return {
            "success": True,
            "page": page,
            "page_size": page_size,
            "total": response.count if response.count is not None else len(response.data or []),
            "data": response.data,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{product_id}")
def get_product(product_id: str):
    try:
        response = (
            supabase.table("products")
            .select("*, product_images(id, image_url)")
            .eq("id", product_id)
            .single()
            .execute()
        )
        if not response.data:
            raise HTTPException(status_code=404, detail="Product not found")
        return {"success": True, "data": response.data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{product_id}")
def update_product(product_id: str, payload: ProductUpdate):
    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
    try:
        current_res = (
            supabase.table("products")
            .select("id, name, stock_quantity")
            .eq("id", product_id)
            .execute()
        )
        if not current_res.data or not isinstance(current_res.data[0], dict):
            raise HTTPException(status_code=404, detail="Product not found")
        current = current_res.data[0]

        if "category_id" in data or "category" in data:
            resolved_id, resolved_name = resolve_product_category(
                data.get("category_id"), data.get("category")
            )
            data["category_id"] = resolved_id
            data["category"] = resolved_name

        response = update_product_record(product_id, data)
        if not response.data:
            raise HTTPException(status_code=404, detail="Product not found")

        if "stock_quantity" in data:
            try:
                before = int(current.get("stock_quantity") or 0)
                after = int(data["stock_quantity"] or 0)
                record_inventory_movement(
                    product_id=product_id,
                    change_qty=after - before,
                    quantity_before=before,
                    quantity_after=after,
                    reason="adjustment",
                    note="Admin product edit",
                )
            except (TypeError, ValueError):
                pass

        return {"success": True, "data": response.data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{product_id}")
def delete_product(product_id: str):
    """Delete a product, its image rows, and the underlying stored files."""
    try:
        images_res = (
            supabase.table("product_images")
            .select("id, image_url")
            .eq("product_id", product_id)
            .execute()
        )
        images = images_res.data or []

        paths = [p for p in (storage_path_from_url(i.get("image_url", "")) for i in images) if p]
        if paths:
            try:
                supabase.storage.from_(IMAGE_BUCKET).remove(paths)
            except Exception:
                pass  # never let storage cleanup block the DB delete

        supabase.table("product_images").delete().eq("product_id", product_id).execute()
        response = supabase.table("products").delete().eq("id", product_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Product not found")
        return {"success": True, "message": "Product deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{product_id}/primary-image", status_code=201)
async def set_primary_image(
    product_id: str,
    file: UploadFile = File(...),
):
    """Upload a primary image and mirror it into the gallery."""
    existing = supabase.table("products").select("id").eq("id", product_id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Product not found")

    try:
        image_url = upload_product_file(file)
        update_product_record(product_id, {"image_url": image_url})
        try:
            row = add_product_image_row(product_id, image_url)
        except Exception as image_exc:
            print(f"[admin-products] primary gallery row skipped: {image_exc}")
            row = {"product_id": product_id, "image_url": image_url}
        return {"success": True, "url": image_url, "data": row}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{product_id}/images", status_code=201)
async def add_product_images(product_id: str, files: List[UploadFile] = File(...)):
    existing = supabase.table("products").select("id").eq("id", product_id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Product not found")

    try:
        saved = save_product_images(product_id, files or [])
        return {"success": True, "data": saved}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{product_id}/images/{image_id}")
def delete_product_image(product_id: str, image_id: str):
    try:
        image_res = (
            supabase.table("product_images")
            .select("image_url")
            .eq("id", image_id)
            .eq("product_id", product_id)
            .execute()
        )
        if not image_res.data:
            raise HTTPException(status_code=404, detail="Image not found")

        path = storage_path_from_url(image_res.data[0].get("image_url", ""))
        if path:
            try:
                supabase.storage.from_(IMAGE_BUCKET).remove([path])
            except Exception:
                pass

        supabase.table("product_images").delete().eq("id", image_id).execute()
        return {"success": True, "message": "Image deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
