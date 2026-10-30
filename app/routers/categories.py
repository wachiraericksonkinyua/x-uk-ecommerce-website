from fastapi import APIRouter, HTTPException

from app.database import supabase

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("/")
def list_active_categories():
    """Public list of active categories for the storefront navigation."""
    try:
        response = (
            supabase.table("categories")
            .select("*")
            .eq("active", True)
            .order("name")
            .execute()
        )
        return {"success": True, "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
