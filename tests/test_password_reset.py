"""Password reset completion (POST /auth/reset-password)."""

from types import SimpleNamespace

import app.routers.auth as auth_router


class FakeAuth:
    def __init__(self, *, session=None, error=None):
        self.session = session
        self.error = error
        self.verified = []
        self.sessions = []
        self.updated = []

    def verify_otp(self, params):
        if self.error:
            raise RuntimeError(self.error)
        self.verified.append(params)
        return SimpleNamespace(session=self.session)

    def set_session(self, access_token, refresh_token):
        if self.error:
            raise RuntimeError(self.error)
        self.sessions.append((access_token, refresh_token))

    def update_user(self, attributes):
        if self.error:
            raise RuntimeError(self.error)
        self.updated.append(attributes)


class FakeSupabase:
    def __init__(self, auth):
        self.auth = auth


def test_reset_requires_a_token(monkeypatch, client):
    monkeypatch.setattr(auth_router, "supabase", FakeSupabase(FakeAuth()))

    resp = client.post("/auth/reset-password", json={"new_password": "newpass123"})

    assert resp.status_code == 400
    assert "invalid or has expired" in resp.json()["detail"].lower()


def test_reset_with_access_token_updates_password(monkeypatch, client):
    auth = FakeAuth()
    monkeypatch.setattr(auth_router, "supabase", FakeSupabase(auth))

    resp = client.post(
        "/auth/reset-password",
        json={
            "new_password": "newpass123",
            "access_token": "recovery-access",
            "refresh_token": "recovery-refresh",
        },
    )

    assert resp.status_code == 200
    assert auth.sessions == [("recovery-access", "recovery-refresh")]
    assert auth.updated == [{"password": "newpass123"}]


def test_reset_with_token_hash_verifies_recovery_otp(monkeypatch, client):
    session = SimpleNamespace(access_token="from-otp", refresh_token="refresh-otp")
    auth = FakeAuth(session=session)
    monkeypatch.setattr(auth_router, "supabase", FakeSupabase(auth))

    resp = client.post(
        "/auth/reset-password",
        json={"new_password": "newpass123", "token_hash": "hash-123"},
    )

    assert resp.status_code == 200
    assert auth.verified == [{"token_hash": "hash-123", "type": "recovery"}]
    assert auth.sessions == [("from-otp", "refresh-otp")]
    assert auth.updated == [{"password": "newpass123"}]


def test_reset_rejects_short_password(monkeypatch, client):
    auth = FakeAuth()
    monkeypatch.setattr(auth_router, "supabase", FakeSupabase(auth))

    resp = client.post(
        "/auth/reset-password",
        json={"new_password": "short", "access_token": "recovery-access"},
    )

    assert resp.status_code == 422
    assert auth.updated == []


def test_reset_surfaces_supabase_errors(monkeypatch, client):
    auth = FakeAuth(error="Token has expired or is invalid")
    monkeypatch.setattr(auth_router, "supabase", FakeSupabase(auth))

    resp = client.post(
        "/auth/reset-password",
        json={"new_password": "newpass123", "access_token": "expired"},
    )

    assert resp.status_code == 400
    assert "expired" in resp.json()["detail"].lower()
