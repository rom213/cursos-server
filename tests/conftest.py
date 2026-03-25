"""
Fixtures compartidos — FastAPI + TestClient + JWT (reemplazo de sesión Flask).
"""
from __future__ import annotations

import os
import sys

import pytest
from fastapi.testclient import TestClient

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))

os.environ.setdefault("SECRET_KEY", "test_secret_key_iso25000")
os.environ.setdefault("SECURITY_PASSWORD_SALT", "test_salt_iso25000")
os.environ.setdefault("MYSQL_HOST", "localhost")
os.environ.setdefault("MYSQL_USER", "test")
os.environ.setdefault("MYSQL_PASSWORD", "test")
os.environ.setdefault("MYSQL_DB", "test")
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")
os.environ.setdefault("MAIL_USERNAME", "test@test.com")
os.environ.setdefault("MAIL_PASSWORD", "test")
os.environ.setdefault("MAIL_DEFAULT_SENDER", "test@test.com")
os.environ.setdefault("ADMIN_EMAIL", "admin@test.com")
os.environ.setdefault("PAYPAL_CLIENT_ID", "test")
os.environ.setdefault("PAYPAL_CLIENT_SECRET", "test")


@pytest.fixture
def app():
    from main import app as fastapi_app

    return fastapi_app


@pytest.fixture
def client(app):
    return TestClient(app)


def _user_token_payload():
    return {
        "sub": "118070327157829661695",
        "google_id": "118070327157829661695",
        "email": "testuser@gmail.com",
        "name": "Test User",
        "given_name": "Test",
        "picture": "https://lh3.googleusercontent.com/a/default-user",
        "accounts": [],
        "prefix": "+57",
        "num_whatsapp": "",
        "is_bought": False,
        "country": "CO",
        "tasa_de_cambio": "4000",
    }


@pytest.fixture
def authenticated_client(client):
    from utils.auth import create_access_token

    token = create_access_token(_user_token_payload())
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


@pytest.fixture
def seller_client(client):
    from utils.auth import create_access_token

    payload = _user_token_payload()
    payload["google_id"] = "seller_google_id_999"
    payload["sub"] = "seller_google_id_999"
    payload["is_bought"] = True
    token = create_access_token(payload)
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


@pytest.fixture
def sample_payu_payload():
    return {
        "merchant_id": "508029",
        "reference_sale": "TEST-REF-001",
        "value": "150000.00",
        "currency": "COP",
        "state_pol": "4",
        "sign": "firma_hash_valida",
        "extra1": "|1,118070327157829661695",
    }


@pytest.fixture
def sample_paypal_webhook():
    return {
        "event_type": "PAYMENTS.PAYMENT.CREATED",
        "resource": {
            "id": "PAY-TEST-001",
            "payer": {"payer_info": {"payer_id": "PAYER-TEST-001"}},
            "transactions": [{"description": "REF-CODE-001"}],
        },
    }


@pytest.fixture
def sample_categories_payload():
    return {"categories": [{"id_category": 1}, {"id_category": 2}]}
