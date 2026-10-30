from fastapi import APIRouter
from app.database import supabase

router = APIRouter(prefix="/delivery", tags=["Delivery"])

@router.get("/locations")
async def get_delivery_locations():
    """Fetch all active delivery locations."""
    try:
        res = supabase.table("delivery_locations").select("*").eq("active", True).execute()
        return {"data": res.data}
    except Exception as e:
        return {"data": [], "error": str(e)}
