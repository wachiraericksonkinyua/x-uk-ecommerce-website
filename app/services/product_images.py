"""Shared product-image helpers for the public and admin product routers."""

from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import UploadFile

from app.database import supabase
from app.utils.images import IMAGE_EXTENSIONS, validate_image_bytes

IMAGE_BUCKET = "product-images"


def upload_product_file(file: UploadFile) -> str:
    """Validate, upload an image to Supabase Storage and return its public URL."""
    file_bytes = file.file.read()
    mime = validate_image_bytes(file_bytes, file.content_type)
    # Use the detected MIME (not the filename) so spoofed extensions cannot
    # create misleading or dangerous objects in the bucket.
    path = f"products/{uuid.uuid4()}{IMAGE_EXTENSIONS[mime]}"
    supabase.storage.from_(IMAGE_BUCKET).upload(
        path,
        file_bytes,
        file_options={"content-type": mime, "cache-control": "3600"},
    )
    return supabase.storage.from_(IMAGE_BUCKET).get_public_url(path)


def add_product_image_row(product_id: str, image_url: str) -> dict:
    """Persist a gallery row, returning a best-effort representation."""
    inserted = (
        supabase.table("product_images")
        .insert({"product_id": product_id, "image_url": image_url})
        .execute()
    )
    rows = inserted.data or []
    if rows and isinstance(rows[0], dict):
        return rows[0]
    return {"product_id": product_id, "image_url": image_url}


def save_product_images(product_id: str, files: List[UploadFile]) -> List[dict]:
    saved: List[dict] = []
    for file in files or []:
        image_url = upload_product_file(file)
        saved.append(add_product_image_row(product_id, image_url))
    return saved


def storage_path_from_url(url: str) -> Optional[str]:
    """Extract the Supabase storage object path from a public URL."""
    marker = f"/{IMAGE_BUCKET}/"
    if isinstance(url, str) and marker in url:
        return url.split(marker, 1)[1].split("?")[0]
    return None
