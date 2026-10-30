from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import date
from app.database import supabase
from app.dependencies import get_current_user

router = APIRouter(prefix="/profiles", tags=["Profiles"])

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    avatar_url: Optional[str] = None
    banner_url: Optional[str] = None
    date_of_birth: Optional[date] = None

@router.get("/me")
def get_my_profile(current_user = Depends(get_current_user)):
    try:
        # Access the ID directly from the validated token, not the URL
        res = supabase.table("profiles").select("*").eq("user_id", current_user.id).single().execute()
        return {"success": True, "data": res.data}
    except Exception:
        raise HTTPException(status_code=404, detail="Profile not found")

@router.post("/me")
def upsert_my_profile(payload: ProfileUpdate, current_user = Depends(get_current_user)):
    try:
        data = payload.dict(exclude_unset=True)
        # Convert date to string for JSON serialization if present
        if "date_of_birth" in data and isinstance(data["date_of_birth"], date):
            data["date_of_birth"] = data["date_of_birth"].isoformat()
        
        data["user_id"] = current_user.id # Force ID to be the authenticated user
        res = supabase.table("profiles").upsert(data, on_conflict="user_id").execute()
        return {"success": True, "data": res.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/me")
async def update_user_profile(profile_data: ProfileUpdate, current_user = Depends(get_current_user)):
    # Exclude empty fields so we don't accidentally overwrite existing data with nulls
    data_to_update = profile_data.dict(exclude_unset=True)
    
    # Convert date to string for JSON serialization if present
    if "date_of_birth" in data_to_update and isinstance(data_to_update["date_of_birth"], date):
        data_to_update["date_of_birth"] = data_to_update["date_of_birth"].isoformat()
    
    # Push the fresh data straight to the profiles table matching the authenticated user
    response = supabase.table("profiles").update(data_to_update).eq("user_id", current_user.id).execute()
    
    return {"message": "Profile updated!", "data": response.data}
