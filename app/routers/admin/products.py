import uuid
from typing import List, Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel

from app.database import supabase
from app.utils.pagination import page_range

router = APIRouter(prefix="/products", tags=["Admin · Products"])

IMAGE_BUCKET = "product-images"


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    brand: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    category: Optional[str] = None
    category_id: Optional[str] = None
    stock_quantity: Optional[int] = None


def _storage_path_from_url(url: str) -> Optional[str]:
    """Best-effort extraction of the object path from a Supabase public URL."""
    marker = f"/{IMAGE_BUCKET}/"
    if isinstance(url, str) and marker in url:
        return url.split(marker, 1)[1].split("?")[0]
    return None


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
            query = query.ilike("name", f"%{search}%")
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
    data = payload.dict(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
    try:
        response = supabase.table("products").update(data).eq("id", product_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Product not found")
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

        paths = [p for p in (_storage_path_from_url(i.get("image_url", "")) for i in images) if p]
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


@router.post("/{product_id}/images", status_code=201)
async def add_product_images(product_id: str, files: List[UploadFile] = File(...)):
    existing = supabase.table("products").select("id").eq("id", product_id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Product not found")

    saved = []
    for file in files:
        file_bytes = await file.read()
        extension = ".jpg"
        if file.filename and "." in file.filename:
            extension = f".{file.filename.rsplit('.', 1)[-1]}"
        path = f"phones/{uuid.uuid4()}{extension}"

        supabase.storage.from_(IMAGE_BUCKET).upload(path, file_bytes)
        image_url = supabase.storage.from_(IMAGE_BUCKET).get_public_url(path)

        inserted = (
            supabase.table("product_images")
            .insert({"product_id": product_id, "image_url": image_url})
            .execute()
        )
        saved.extend(inserted.data or [])

    return {"success": True, "data": saved}


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

        path = _storage_path_from_url(image_res.data[0].get("image_url", ""))
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
