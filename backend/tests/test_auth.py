"""
Integration tests for /auth endpoints.
Contract:
  POST /auth/register  → 201 {id, email, created_at}
  POST /auth/login     → 200 {access_token, token_type}
  GET  /auth/me        → 200 {id, email, created_at}  (valid Bearer)
                       → 401                           (invalid/missing token)
  POST /auth/register  → 409                           (duplicate email)
  POST /auth/register  → 422                           (bad email / short password)
  POST /auth/login     → 401                           (wrong password)
"""
import pytest

REGISTER_URL = "/auth/register"
LOGIN_URL = "/auth/login"
ME_URL = "/auth/me"

VALID_EMAIL = "user@example.com"
VALID_PASSWORD = "securepassword1"


# ---------------------------------------------------------------------------
# register
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_register_success(client):
    resp = await client.post(REGISTER_URL, json={"email": VALID_EMAIL, "password": VALID_PASSWORD})
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == VALID_EMAIL
    assert "id" in body
    assert "created_at" in body
    assert "hashed_password" not in body


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_409(client):
    payload = {"email": VALID_EMAIL, "password": VALID_PASSWORD}
    await client.post(REGISTER_URL, json=payload)
    resp = await client.post(REGISTER_URL, json=payload)
    assert resp.status_code == 409
    assert "already registered" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_invalid_email_returns_422(client):
    resp = await client.post(REGISTER_URL, json={"email": "not-an-email", "password": VALID_PASSWORD})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_short_password_returns_422(client):
    resp = await client.post(REGISTER_URL, json={"email": VALID_EMAIL, "password": "short"})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# login
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_login_success(client):
    await client.post(REGISTER_URL, json={"email": VALID_EMAIL, "password": VALID_PASSWORD})
    resp = await client.post(LOGIN_URL, json={"email": VALID_EMAIL, "password": VALID_PASSWORD})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(client):
    await client.post(REGISTER_URL, json={"email": VALID_EMAIL, "password": VALID_PASSWORD})
    resp = await client.post(LOGIN_URL, json={"email": VALID_EMAIL, "password": "wrongpassword"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email_returns_401(client):
    resp = await client.post(LOGIN_URL, json={"email": "ghost@example.com", "password": VALID_PASSWORD})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# /me
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_me_with_valid_token(client):
    await client.post(REGISTER_URL, json={"email": VALID_EMAIL, "password": VALID_PASSWORD})
    login_resp = await client.post(LOGIN_URL, json={"email": VALID_EMAIL, "password": VALID_PASSWORD})
    token = login_resp.json()["access_token"]

    resp = await client.get(ME_URL, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == VALID_EMAIL
    assert "id" in body
    assert "created_at" in body


@pytest.mark.asyncio
async def test_me_with_invalid_token_returns_401(client):
    resp = await client.get(ME_URL, headers={"Authorization": "Bearer this.is.garbage"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_with_no_token_returns_401(client):
    resp = await client.get(ME_URL)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_with_expired_token_returns_401(client):
    """Craft a token that expired in the past."""
    from datetime import datetime, timedelta, timezone
    from jose import jwt
    from app.config import settings

    expired_payload = {
        "sub": "00000000-0000-0000-0000-000000000000",
        "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
    }
    expired_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    resp = await client.get(ME_URL, headers={"Authorization": f"Bearer {expired_token}"})
    assert resp.status_code == 401
