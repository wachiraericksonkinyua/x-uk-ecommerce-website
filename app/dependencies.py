import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database import supabase

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)

# Comma-separated allowlist, e.g. ADMIN_EMAILS="owner@x-uk.com,manager@x-uk.com"
_ADMIN_EMAILS = {
    email.strip().lower()
    for email in os.environ.get("ADMIN_EMAILS", "").split(",")
    if email.strip()
}

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Validates the JWT token and returns the user object from Supabase.
    This replaces trusting user_id from the URL.
    """
    token = credentials.credentials
    try:
        # Supabase validates the token and returns the user
        user_response = supabase.auth.get_user(token)
        return user_response.user
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(credentials: HTTPAuthorizationCredentials = Depends(optional_security)):
    """Like ``get_current_user`` but never raises — returns ``None`` for guests."""
    if credentials is None:
        return None
    try:
        user_response = supabase.auth.get_user(credentials.credentials)
        return user_response.user
    except Exception:
        return None


def user_is_admin(current_user) -> bool:
    """Return True when the user is an admin (email allowlist or profile flag).

    A user is an admin when either:
      1. Their email is in the ADMIN_EMAILS environment allowlist, or
      2. Their profile is flagged admin — supported by BOTH the migration
         schema (`profiles.role == "admin"`) and the legacy/actual schema
         (`profiles.is_admin == true`).

    The profile lookup tries `user_id` first (migrations) and falls back to
    `id` (older tables where `profiles.id` is the auth user id).
    """
    if current_user is None:
        return False

    email = (getattr(current_user, "email", None) or "").lower()
    if email and email in _ADMIN_EMAILS:
        return True

    for column in ("user_id", "id"):
        try:
            res = (
                supabase.table("profiles")
                .select("*")
                .eq(column, current_user.id)
                .limit(1)
                .execute()
            )
        except Exception:
            continue

        row = res.data[0] if res.data else None
        if not isinstance(row, dict):
            continue

        role = row.get("role")
        if isinstance(role, str) and role.strip().lower() == "admin":
            return True
        if row.get("is_admin") is True:
            return True

    return False


async def require_admin(current_user = Depends(get_current_user)):
    """Authorizes admin access; raises 403 for everyone else."""
    if user_is_admin(current_user):
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Admin privileges required",
    )
