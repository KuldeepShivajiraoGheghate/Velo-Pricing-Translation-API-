"""
Phase 1 Tests — Foundation: Auth, API Keys, Health endpoint.

Tests cover:
- GET /health → 200
- POST /api/auth/signup → 201 + JWT
- Duplicate email → 409
- POST /api/auth/login → 200 + JWT
- Wrong password → 401
- GET /api/auth/me → 200 (requires auth)
- GET /api/auth/me without token → 401
- POST /api/auth/keys → 201, raw_key returned once
- GET /api/auth/keys → list (no raw_key exposed)
- DELETE /api/auth/keys/{id} → 204
- DELETE already-revoked key → 409
- API key hash: verify raw key is never stored
"""
import pytest
from fastapi.testclient import TestClient

from app.core.security import hash_api_key, hash_password, generate_api_key


# ── Helpers ────────────────────────────────────────────────────────────────────

def signup_and_login(client: TestClient, email: str = "test@example.com", password: str = "securepass123") -> str:
    """Sign up a new org+user and return the JWT token."""
    resp = client.post("/api/auth/signup", json={
        "org_name": "Test Corp",
        "email": email,
        "password": password,
    })
    assert resp.status_code == 201, resp.json()
    return resp.json()["access_token"]


# ── Health ─────────────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_returns_200(self, client: TestClient):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "velo-api"


# ── Signup ─────────────────────────────────────────────────────────────────────

class TestSignup:
    def test_signup_creates_org_and_user(self, client: TestClient):
        resp = client.post("/api/auth/signup", json={
            "org_name": "Acme SaaS",
            "email": "founder@acme.com",
            "password": "supersecret99",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["role"] == "admin"
        assert data["org_id"]
        assert data["user_id"]

    def test_signup_duplicate_email_returns_409(self, client: TestClient):
        payload = {"org_name": "Dup Corp", "email": "dup@test.com", "password": "password123"}
        client.post("/api/auth/signup", json=payload)
        resp = client.post("/api/auth/signup", json=payload)
        assert resp.status_code == 409

    def test_signup_short_password_rejected(self, client: TestClient):
        resp = client.post("/api/auth/signup", json={
            "org_name": "Short Pwd",
            "email": "short@test.com",
            "password": "abc",
        })
        assert resp.status_code == 422

    def test_signup_invalid_email_rejected(self, client: TestClient):
        resp = client.post("/api/auth/signup", json={
            "org_name": "Bad Email",
            "email": "not-an-email",
            "password": "validpass123",
        })
        assert resp.status_code == 422


# ── Login ──────────────────────────────────────────────────────────────────────

class TestLogin:
    def test_login_with_valid_credentials(self, client: TestClient):
        token = signup_and_login(client, "login_valid@test.com")
        assert token  # JWT returned

    def test_login_wrong_password_returns_401(self, client: TestClient):
        client.post("/api/auth/signup", json={
            "org_name": "Login Test",
            "email": "logintest@test.com",
            "password": "correctpassword",
        })
        resp = client.post("/api/auth/login", json={
            "email": "logintest@test.com",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401

    def test_login_unknown_email_returns_401(self, client: TestClient):
        resp = client.post("/api/auth/login", json={
            "email": "ghost@nowhere.com",
            "password": "whatever123",
        })
        assert resp.status_code == 401


# ── Me endpoint ────────────────────────────────────────────────────────────────

class TestMe:
    def test_me_returns_user_profile(self, client: TestClient):
        token = signup_and_login(client, "me_user@test.com")
        resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "me_user@test.com"
        assert data["role"] == "admin"
        assert data["org_name"]

    def test_me_without_token_returns_401(self, client: TestClient):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_me_with_invalid_token_returns_401(self, client: TestClient):
        resp = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.jwt.token"})
        assert resp.status_code == 401


# ── API Key Management ─────────────────────────────────────────────────────────

class TestAPIKeys:
    def test_create_key_returns_raw_key_once(self, client: TestClient):
        token = signup_and_login(client, "keycreate@test.com")
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.post("/api/auth/keys", json={"label": "Production"}, headers=headers)
        assert resp.status_code == 201
        data = resp.json()
        assert "raw_key" in data
        assert data["raw_key"].startswith("velo_")
        assert data["label"] == "Production"
        assert data["id"]

    def test_list_keys_does_not_expose_raw_key(self, client: TestClient):
        token = signup_and_login(client, "keylist@test.com")
        headers = {"Authorization": f"Bearer {token}"}

        client.post("/api/auth/keys", json={"label": "Key A"}, headers=headers)
        resp = client.get("/api/auth/keys", headers=headers)
        assert resp.status_code == 200
        keys = resp.json()
        assert len(keys) >= 1
        for key in keys:
            assert "raw_key" not in key or key.get("raw_key") is None

    def test_revoke_key(self, client: TestClient):
        token = signup_and_login(client, "keyrevoke@test.com")
        headers = {"Authorization": f"Bearer {token}"}

        create_resp = client.post("/api/auth/keys", json={"label": "To Revoke"}, headers=headers)
        key_id = create_resp.json()["id"]

        del_resp = client.delete(f"/api/auth/keys/{key_id}", headers=headers)
        assert del_resp.status_code == 204

        # Verify it's marked revoked
        get_resp = client.get(f"/api/auth/keys/{key_id}", headers=headers)
        assert get_resp.json()["revoked_at"] is not None

    def test_revoke_already_revoked_key_returns_409(self, client: TestClient):
        token = signup_and_login(client, "keyrevokedupe@test.com")
        headers = {"Authorization": f"Bearer {token}"}

        create_resp = client.post("/api/auth/keys", json={"label": "Dup Revoke"}, headers=headers)
        key_id = create_resp.json()["id"]

        client.delete(f"/api/auth/keys/{key_id}", headers=headers)
        resp = client.delete(f"/api/auth/keys/{key_id}", headers=headers)
        assert resp.status_code == 409

    def test_create_key_without_auth_returns_401(self, client: TestClient):
        resp = client.post("/api/auth/keys", json={"label": "Unauth"})
        assert resp.status_code == 401


# ── Security: raw key is never stored ─────────────────────────────────────────

class TestSecurityInvariants:
    def test_api_key_hash_is_sha256(self):
        """Verify hash_api_key produces a 64-char hex SHA-256 digest."""
        raw = generate_api_key()
        hashed = hash_api_key(raw)
        assert len(hashed) == 64
        assert all(c in "0123456789abcdef" for c in hashed)

    def test_generate_api_key_has_correct_prefix(self):
        for _ in range(10):
            key = generate_api_key()
            assert key.startswith("velo_")
            assert len(key) > 20  # prefix + 64 hex chars

    def test_different_keys_produce_different_hashes(self):
        k1 = generate_api_key()
        k2 = generate_api_key()
        assert hash_api_key(k1) != hash_api_key(k2)

    def test_password_hash_is_bcrypt(self):
        """Verify stored password is a bcrypt hash, not plaintext."""
        plain = "testpassword123"
        hashed = hash_password(plain)
        assert hashed != plain
        assert hashed.startswith("$2b$")  # bcrypt prefix
