"""
Phase 6 — Admin / Internal API Tests
Tests session-authenticated dashboard endpoints (/api/*).
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.org import Org
from app.models.user import User
from app.core.security import create_access_token, hash_password


@pytest.fixture
def admin_setup(db_session: Session):
    org = Org(name="Dashboard Test Org")
    db_session.add(org)
    db_session.flush()

    user = User(
        org_id=org.id,
        email=f"admin_{org.id[:8]}@dashboard.com",
        password_hash=hash_password("password123"),
        role="admin",
    )
    db_session.add(user)
    db_session.commit()

    token = create_access_token({"sub": user.id, "org_id": org.id})
    return {"org": org, "user": user, "token": token}


def test_list_integrations(client: TestClient, admin_setup: dict):
    headers = {"Authorization": f"Bearer {admin_setup['token']}"}
    res = client.get("/api/integrations", headers=headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_connect_integration(client: TestClient, admin_setup: dict):
    headers = {"Authorization": f"Bearer {admin_setup['token']}"}
    res = client.post(
        "/api/integrations/connect",
        headers=headers,
        json={"provider": "stripe", "api_key": "sk_test_mock"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["provider"] == "stripe"


def test_save_and_deploy_ruleset(client: TestClient, admin_setup: dict):
    headers = {"Authorization": f"Bearer {admin_setup['token']}"}
    res = client.post(
        "/api/rules",
        headers=headers,
        json={
            "currencies": ["EUR", "GBP", "JPY"],
            "regulation_profile": "EU_VAT_GDPR",
            "tax_mode": "inclusive",
            "rounding_strategy": "nearest_99",
            "psychological_pricing": True,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_active"] is True
    assert data["version"] == 1
    assert "EUR" in data["currencies"]

    # Verify GET active ruleset
    res_active = client.get("/api/rules/active", headers=headers)
    assert res_active.status_code == 200
    assert res_active.json()["version"] == 1


def test_preview_translation(client: TestClient, admin_setup: dict):
    headers = {"Authorization": f"Bearer {admin_setup['token']}"}
    res = client.post(
        "/api/preview",
        headers=headers,
        json={
            "amount": "49.00",
            "base_currency": "USD",
            "target_currency": "EUR",
            "target_country": "DE",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["original_currency"] == "USD"
    assert data["target_currency"] == "EUR"
    assert "translated_amount" in data


def test_api_keys_lifecycle(client: TestClient, admin_setup: dict):
    headers = {"Authorization": f"Bearer {admin_setup['token']}"}

    # 1. Create key
    res_create = client.post(
        "/api/keys",
        headers=headers,
        json={"label": "Production Mobile App"},
    )
    assert res_create.status_code == 200
    key_data = res_create.json()
    assert key_data["label"] == "Production Mobile App"
    assert "raw_key" in key_data
    key_id = key_data["id"]

    # 2. List keys
    res_list = client.get("/api/keys", headers=headers)
    assert res_list.status_code == 200
    assert any(k["id"] == key_id for k in res_list.json())

    # 3. Revoke key
    res_del = client.delete(f"/api/keys/{key_id}", headers=headers)
    assert res_del.status_code == 204


def test_activity_logs(client: TestClient, admin_setup: dict):
    headers = {"Authorization": f"Bearer {admin_setup['token']}"}
    res = client.get("/api/activity", headers=headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)
