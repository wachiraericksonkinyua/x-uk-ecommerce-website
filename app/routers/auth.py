from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr

from app.database import supabase
from app.dependencies import get_current_user, security

router = APIRouter(prefix="/auth", tags=["Authentication"])


class SignUpRequest(BaseModel):  # expected JSON body for signup
    email: EmailStr
    password: str


class LoginRequest(BaseModel):  # expected JSON body for login
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


@router.post("/signup")
def sign_up(payload: SignUpRequest):
    try:
        response = supabase.auth.sign_up({
            "email": payload.email,
            "password": payload.password,
        })
        return {"success": True, "data": response}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
def log_in(payload: LoginRequest):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": payload.email,
            "password": payload.password,
        })
        # session holds the access_token (JWT) + refresh_token the client stores
        return {"success": True, "session": response.session, "user": response.user}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/me")
def current_user_info(current_user=Depends(get_current_user)):
    """Return the authenticated user's basic identity."""
    return {
        "success": True,
        "user": {"id": current_user.id, "email": current_user.email},
    }


@router.post("/refresh")
def refresh_session(payload: RefreshRequest):
    """Exchange a refresh token for a brand new session (new access token)."""
    try:
        response = supabase.auth.refresh_session(payload.refresh_token)
        return {"success": True, "session": response.session, "user": response.user}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/logout")
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user=Depends(get_current_user),
):
    """Revoke the current token server-side (best effort)."""
    try:
        supabase.auth.admin.sign_out(credentials.credentials)
    except Exception:
        pass  # JWTs are stateless; the client discarding the token is enough
    return {"success": True, "message": "Logged out"}


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest):
    """Send a password-reset email.

    We always return success so an attacker cannot probe which emails exist.
    """
    try:
        supabase.auth.reset_password_email(payload.email)
    except Exception:
        pass
    return {
        "success": True,
        "message": "If that email is registered, a reset link has been sent.",
    }
