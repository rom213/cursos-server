"""
Pruebas unitarias — rutas de pago (FastAPI).
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def payments_client(client):
    return client


@patch("routes.payments.calculate_total_price")
@patch("routes.payments.PaymentRespository")
def test_payu_firm_functional_suitability_happy_path(
    mock_payment_repo, mock_calc_price, authenticated_client
):
    mock_calc_price.return_value = 15000
    mock_instance = mock_payment_repo.return_value
    mock_instance.signature = "firma_secreta_falsa_123"
    mock_instance.reference_code = "REFERENCIA-TEST-001"
    mock_instance.price = 15000

    payload = {"categories": [{"id_category": 1}]}
    response = authenticated_client.post("/payu-firm", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["signature"] == "firma_secreta_falsa_123"
    assert data["reference_code"] == "REFERENCIA-TEST-001"
    assert data["price"] == 15000


def test_payu_firm_security_unauthorized(client):
    response = client.post("/payu-firm", json={"categories": [{"id_category": 1}]})
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False


@patch("routes.payments.process_payu_transaction")
def test_payu_confirmation_functional_suitability(mock_process, client):
    payload = {
        "merchant_id": "123",
        "reference_sale": "test_ref",
        "value": "20.50",
        "currency": "USD",
        "state_pol": "4",
        "sign": "firma_validada",
    }
    response = client.post("/payu-confirmation", data=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Confirmation received"
    assert data["transaction_status"] == "approved"
    assert mock_process.called


def test_payu_confirmation_reliability_missing_params(client):
    payload = {"merchant_id": "solo_tengo_esto"}
    response = client.post("/payu-confirmation", data=payload)
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data or "error" in data


@patch("routes.payments.calculate_total_price")
def test_payu_firm_reliability_internal_error(mock_calc_price, authenticated_client):
    mock_calc_price.side_effect = Exception("Fallo catastrófico de Base de Datos")
    payload = {"categories": [{"id_category": 1}]}
    response = authenticated_client.post("/payu-firm", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "posible error" in data.get("message", "").lower()


@patch("routes.payments.paypalrestsdk.Payment.find")
@patch("routes.payments.PaymentRegisterRepository.getItemsPayment")
def test_paypal_webhook_event_error_handling(mock_get_items, mock_payment_find, client):
    payload = [{"invalid": "data_type"}]
    response = client.post("/paypal/webhook", json=payload)
    assert response.status_code in (500, 422)
