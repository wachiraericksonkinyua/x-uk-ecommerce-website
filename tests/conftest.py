"""Shared pytest setup.

We set dummy env vars BEFORE importing the app so `app.database` does not need a
real Supabase project. Tests never hit the network: pure functions are tested
directly and Supabase is replaced with an in-memory fake.
"""

import os

os.environ.setdefault("SUPABASE_URL", "http://localhost:1")
os.environ.setdefault("SUPABASE_KEY", "test-key")
# ensure signature verification is off by default in tests
os.environ.pop("WHATSAPP_APP_SECRET", None)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
