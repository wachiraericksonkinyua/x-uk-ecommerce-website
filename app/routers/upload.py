from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from app.database import supabase
from app.dependencies import get_current_user
from app.utils.images import IMAGE_EXTENSIONS, validate_image_bytes
import uuid

router = APIRouter(prefix="/upload", tags=["Uploads"])

@router.post("/profile-picture")
async def upload_profile_picture(file: UploadFile = File(...), current_user = Depends(get_current_user)):
    """
    Receives an image, validates it, generates a secure unique name,
    and uploads it directly to Supabase Storage.
    """
    try:
        # 1. Read the raw image data into memory and validate size/type/magic bytes
        file_bytes = await file.read()
        mime = validate_image_bytes(file_bytes, file.content_type)

        # 2. Use the detected type for a safe extension
        file_extension = IMAGE_EXTENSIONS[mime]

        # 3. Create a unique folder path matching our SQL policy
        unique_filename = f"{current_user.id}/{uuid.uuid4()}{file_extension}"

        # 4. Push the file straight into your Supabase bucket
        supabase.storage.from_("profile-assets").upload(
            path=unique_filename,
            file=file_bytes,
            file_options={"cache-control": "3600", "content-type": mime}
        )

        # 5. Grab the public link so the frontend can actually display it
        public_url = supabase.storage.from_("profile-assets").get_public_url(unique_filename)

        return {"success": True, "url": public_url}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
