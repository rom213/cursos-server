"""
Pruebas unitarias para las rutas de pago (pagos.py) enfocadas en atributos ISO/IEC 25000:
- Adecuación Funcional
- Fiabilidad (Manejo de Errores)
- Seguridad

Comando exacto de terminal para ejecutar estas pruebas (con -s para ver mensajes):
pytest tests/routes/test_payments.py -v -s
"""

import pytest
import json
import sys
import os
from unittest.mock import patch, MagicMock
from flask import Flask

# Asegurarse de que el directorio raíz de la aplicación (cursos-server) y la carpeta src estén en el PYTHONPATH
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))



# Fixture principal para configurar la aplicación y el blueprint a testear
@pytest.fixture
def app():
    from src.routes.payments import payments_bp
    
    app = Flask(__name__)
    app.secret_key = "test_key_for_security"
    app.register_blueprint(payments_bp)
    app.testing = True
    return app

@pytest.fixture
def client(app):
    """Cliente de pruebas para realizar peticiones a los endpoints"""
    return app.test_client()

# =========================================================================
# ISO 25000: Seguridad (Protección contra accesos no autorizados)
# =========================================================================
def test_payu_firm_security_unauthorized(client):
    """
    Atributo: Seguridad
    Asegura que las URLs de generación de firmas requieran una sesión activa.
    Se espera: Retorno HTTP 401 y un mensaje de error explícito de falta de sesión.
    """
    response = client.post('/payu-firm', json={"categories": [{"id_category": 1}]})
    assert response.status_code == 401
    
    data = json.loads(response.data)
    assert data["success"] is False
    assert "No ha iniciado sesión" in data["error"]
    print("\n[OK] [EXITO] Seguridad: Acceso no autorizado a API de firmas bloqueado correctamente.")

# =========================================================================
# ISO 25000: Adecuación Funcional (Exactitud) - Camino Feliz
# =========================================================================
@patch('src.routes.payments.calculate_total_price')
@patch('src.routes.payments.PaymentRespository')
def test_payu_firm_functional_suitability_happy_path(mock_payment_repo, mock_calc_price, app, client):
    """
    Atributo: Adecuación Funcional (Camino Feliz)
    Verifica que, al contar con los datos correctos y sesión, se firma correctamente
    y devuelve la estructura esperada: signature, reference_code y price.
    """
    # Configurar Mocks para no golpear base de datos ni lógicas complejas de negocio (Aislamiento)
    mock_calc_price.return_value = 15000  # un precio de ejemplo
    mock_instance = mock_payment_repo.return_value
    mock_instance.signature = "firma_secreta_falsa_123"
    mock_instance.reference_code = "REFERENCIA-TEST-001"
    mock_instance.price = 15000
    
    # Inyectar una sesión falsa simulando un usuario logueado
    with client.session_transaction() as sess:
        sess['user'] = {'google_id': 'usuario_prueba_123'}

    payload = {"categories": [{"id_category": 1}]}
    response = client.post('/payu-firm', json=payload)
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert data["signature"] == "firma_secreta_falsa_123"
    assert data["reference_code"] == "REFERENCIA-TEST-001"
    assert data["price"] == 15000
    print("\n[OK] [EXITO] Funcionalidad: Firma PayU generada correctamente bajo parametros validos.")

@patch('src.routes.payments.executor.submit')
def test_payu_confirmation_functional_suitability(mock_submit, client):
    """
    Atributo: Adecuación Funcional
    Verifica el procesamiento asíncrono exitoso de un webhook (confirmación) de PayU.
    """
    payload = {
        "merchant_id": "123",
        "reference_sale": "test_ref",
        "value": "20.50",
        "currency": "USD",
        "state_pol": "4",
        "sign": "firma_validada"
    }
    response = client.post('/payu-confirmation', data=payload)
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert data["message"] == "Confirmation received"
    assert data["transaction_status"] == "approved"
    # Verifica que la invocación para procesar la venta de forma asíncrona ocurrió
    mock_submit.assert_called_once()
    print("\n[OK] [EXITO] Funcionalidad: Webhook de confirmacion PayU procesado exitosamente en segundo plano.")

# =========================================================================
# ISO 25000: Fiabilidad (Madurez, Tolerancia a fallos, Recuperabilidad)
# =========================================================================
def test_payu_confirmation_reliability_missing_params(client):
    """
    Atributo: Fiabilidad (Madurez de la interfaz)
    Fallo inducido para validar el control de entradas del Webhook. Faltan datos críticos.
    Se espera: Retorno HTTP 400 sin desencadenar excepciones internas (crashes).
    """
    payload = {"merchant_id": "solo_tengo_esto"}
    response = client.post('/payu-confirmation', data=payload)
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data["error"] == "Missing parameters"
    print("\n[OK] [EXITO] Fiabilidad: Peticion incompleta detectada y manejada con HTTP 400 sin sufrir crash.")

@patch('src.routes.payments.calculate_total_price')
def test_payu_firm_reliability_internal_error(mock_calc_price, app, client):
    """
    Atributo: Fiabilidad (Tolerancia a Fallos)
    Simula una excepción no manejada proveniente del cálculo de precio para 
    validar que el sistema lo atrapa y no exuda datos sensibles.
    """
    mock_calc_price.side_effect = Exception("Fallo catastrófico de Base de Datos")
    
    with client.session_transaction() as sess:
        sess['user'] = {'google_id': 'usuario_prueba_123'}

    payload = {"categories": [{"id_category": 1}]}
    response = client.post('/payu-firm', json=payload)
    
    assert response.status_code == 500
    data = json.loads(response.data)
    assert "posible error" in data["message"].lower()
    print("\n[OK] [EXITO] Fiabilidad: Error interno simulado fue atrapado de manera segura con HTTP 500.")

@patch('src.routes.payments.paypalrestsdk.Payment.find')
@patch('src.routes.payments.PaymentRegisterRepository.getItemsPayment')
def test_paypal_webhook_event_error_handling(mock_get_items, mock_payment_find, client):
    """
    Atributo: Fiabilidad (Capacidad de recuperación)
    Asegura que, si llegan datos incorrectos en el webhook de PayPal, el servidor no caiga,
    si no que devuelva un código HTTP 500 bajo un escenario controlado por el bloque except.
    """
    # Al enviarle una lista en vez de un diccionario, `data.get("event_type")` arrojará un AttributeError,
    # lo que simula un fallo inesperado que debe ser atrapado por el bloque except general retornando HTTP 500
    payload = [{"invalid": "data_type"}]
    response = client.post('/paypal/webhook', json=payload)
    
    assert response.status_code == 500
    data = json.loads(response.data)
    assert "error" in data
    print("\n[OK] [EXITO] Fiabilidad: Webhook de PayPal con payload basura fue tolerado respondiendo HTTP 500.")
