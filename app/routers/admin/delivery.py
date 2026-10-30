from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import supabase

router = APIRouter(prefix="/delivery-locations", tags=["Admin · Delivery"])


class LocationCreate(BaseModel):
    name: str
    cost: float
    active: bool = True


class LocationUpdate(BaseModel):
    name: Optional[str] = None
    cost: Optional[float] = None
    active: Optional[bool] = None


@router.get("")
def list_locations():
    try:
        response = supabase.table("delivery_locations").select("*").order("name").execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("", status_code=201)
def create_location(payload: LocationCreate):
    try:
        response = supabase.table("delivery_locations").insert(payload.dict()).execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{location_id}")
def update_location(location_id: str, payload: LocationUpdate):
    data = payload.dict(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
    try:
        response = (
            supabase.table("delivery_locations")
            .update(data)
            .eq("id", location_id)
            .execute()
        )
        if not response.data:
            raise HTTPException(status_code=404, detail="Location not found")
        return {"success": True, "data": response.data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{location_id}")
def delete_location(location_id: str):
    try:
        response = (
            supabase.table("delivery_locations")
            .delete()
            .eq("id", location_id)
            .execute()
        )
        if not response.data:
            raise HTTPException(status_code=404, detail="Location not found")
        return {"success": True, "message": "Location deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
