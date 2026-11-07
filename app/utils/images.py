"""Validation helpers for uploaded images.

Uploads are read into memory before being sent to Supabase Storage, so the API
must reject oversized or non-image payloads itself — filename/content-type
headers alone are attacker-controlled.
"""

from __future__ import annotations

from typing import Optional

from fastapi import HTTPException

MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB

# Canonical MIME -> file extension written to storage.
IMAGE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

_CONTENT_TYPE_ALIASES = {
    "image/jpg": "image/jpeg",
    "image/pjpeg": "image/jpeg",
    "image/x-png": "image/png",
}


def _normalize_content_type(content_type: Optional[str]) -> Optional[str]:
    if not content_type:
        return None
    value = content_type.split(";", 1)[0].strip().lower()
    return _CONTENT_TYPE_ALIASES.get(value, value)


def sniff_image_mime(data: bytes) -> Optional[str]:
    """Return the MIME type detected from magic bytes, or None."""
    if not data:
        return None
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def validate_image_bytes(data: bytes, content_type: Optional[str]) -> str:
    """Validate an in-memory image and return its canonical MIME type.

    Raises ``HTTPException(400)`` when the payload is empty, too large, not an
    allowed image format, or when the declared content type disagrees with the
    actual bytes.
    """
    if not data:
        raise HTTPException(status_code=400, detail="The uploaded file is empty")

    if len(data) > MAX_IMAGE_BYTES:
        limit_mb = MAX_IMAGE_BYTES // (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"Images must be {limit_mb} MB or smaller",
        )

    detected = sniff_image_mime(data)
    if detected is None:
        raise HTTPException(
            status_code=400,
            detail="Only JPEG, PNG or WebP images are supported",
        )

    declared = _normalize_content_type(content_type)
    if declared is not None and declared not in IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only JPEG, PNG or WebP images are supported",
        )
    if declared is not None and declared != detected:
        raise HTTPException(
            status_code=400,
            detail="The image content does not match its declared file type",
        )

    return detected
