"""Shared product-image helpers for the public and admin product routers."""

from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import UploadFile

from app.database import supabase

IMAGE_BUCKET = "product-images"


def _extension_for(file: UploadFile) -> str:
    if file.filename and "." in file.filename:
        suffix = file.filename.rsplit(".", 1)[-1].lower()
        if suffix:
            return f".{suffix}"
    return ".jpg"


def upload_product_file(file: UploadFile) -> str:
    """Upload an image to Supabase Storage and return its public URL."""
    file_bytes = file.file.read()
    path = f"phones/{uuid.uuid4()}{_extension_for(file)}"
    supabase.storage.from_(IMAGE_BUCKET).upload(path, file_bytes)
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
