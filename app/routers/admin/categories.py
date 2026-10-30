import re
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import supabase

router = APIRouter(prefix="/categories", tags=["Admin · Categories"])


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


class CategoryCreate(BaseModel):
    name: str
    slug: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    active: bool = True


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    active: Optional[bool] = None


@router.get("")
def list_categories():
    try:
        response = supabase.table("categories").select("*").order("name").execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("", status_code=201)
def create_category(payload: CategoryCreate):
    data = payload.dict()
    if not data.get("slug"):
        data["slug"] = _slugify(payload.name)
    try:
        response = supabase.table("categories").insert(data).execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{category_id}")
def update_category(category_id: str, payload: CategoryUpdate):
    data = payload.dict(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
    if "name" in data and not data.get("slug"):
        data.setdefault("slug", _slugify(data["name"]))
    try:
        response = supabase.table("categories").update(data).eq("id", category_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Category not found")
        return {"success": True, "data": response.data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{category_id}")
def delete_category(category_id: str):
    try:
        response = supabase.table("categories").delete().eq("id", category_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Category not found")
        return {"success": True, "message": "Category deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
