from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from app.database import supabase
from app.dependencies import get_current_user
import uuid
import mimetypes

router = APIRouter(prefix="/upload", tags=["Uploads"])

@router.post("/profile-picture")
async def upload_profile_picture(file: UploadFile = File(...), current_user = Depends(get_current_user)):
    """
    Receives an image, generates a secure unique name, 
    and uploads it directly to Supabase Storage.
    """
    try:
        # 1. Read the raw image data into memory
        file_bytes = await file.read()
        
        # 2. Figure out the file extension (like .jpg or .png) securely
        file_extension = mimetypes.guess_extension(file.content_type or ".jpg")
        
        # 3. Create a unique folder path matching our SQL policy
        unique_filename = f"{current_user.id}/{uuid.uuid4()}{file_extension}"
        
        # 4. Push the file straight into your Supabase bucket
        supabase.storage.from_("profile-assets").upload(
            path=unique_filename,
            file=file_bytes,
            file_options={"cache-control": "3600", "content-type": file.content_type or "image/jpeg"}
        )
        
        # 5. Grab the public link so the frontend can actually display it
        public_url = supabase.storage.from_("profile-assets").get_public_url(unique_filename)
        
        return {"success": True, "url": public_url}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
