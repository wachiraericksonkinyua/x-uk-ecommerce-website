from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field

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


class ResetPasswordRequest(BaseModel):
    """Complete a password reset.

    A Supabase recovery email can arrive in two shapes:

    * an implicit-flow link with ``access_token`` + ``refresh_token`` in the URL
      fragment (older projects / default templates), or
    * a ``token_hash`` query parameter (newer email templates using OTP links).

    The client forwards whichever it received; we verify it server-side and
    then set the new password. The password is never trusted from a bare email
    address, so an attacker cannot reset an account they do not own.
    """

    new_password: str = Field(min_length=8, max_length=72)
    access_token: str | None = None
    refresh_token: str | None = None
    token_hash: str | None = None


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


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest):
    """Finish the reset flow started by ``/auth/forgot-password``.

    The recovery token proves the caller controls the email inbox; only then do
    we update the password. A missing/invalid/expired token is rejected.
    """
    try:
        access_token = payload.access_token
        refresh_token = payload.refresh_token

        if payload.token_hash:
            # Newer Supabase templates send a token_hash instead of raw tokens.
            verified = supabase.auth.verify_otp(
                {"token_hash": payload.token_hash, "type": "recovery"}
            )
            session = getattr(verified, "session", None)
            access_token = getattr(session, "access_token", None) or access_token
            refresh_token = getattr(session, "refresh_token", None) or refresh_token

        if not access_token:
            raise HTTPException(
                status_code=400,
                detail="This reset link is invalid or has expired. Request a new one.",
            )

        # Make the recovery session the active one, then update the password.
        supabase.auth.set_session(access_token, refresh_token or "")
        supabase.auth.update_user({"password": payload.new_password})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "success": True,
        "message": "Password updated. You can now sign in with your new password.",
    }
