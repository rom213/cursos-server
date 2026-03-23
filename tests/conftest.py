"""
=============================================================================
 FIXTURES COMPARTIDOS PARA PYTEST — ISO/IEC 25000
 Plataforma: Cursos Estudia y Trabaja
=============================================================================

 Este módulo centraliza los fixtures de pytest para evitar duplicación
 de configuración entre los archivos de prueba. Provee:

 - Aplicación Flask configurada para testing
 - Cliente HTTP de pruebas
 - Sesiones de usuario simuladas (autenticado / admin)
 - Mocks comunes para DB, PayPal, Google OAuth

 Métrica ISO 25023 relacionada:
 COMPLETITUD FUNCIONAL (Functional Suitability - Completeness)
    C = (L_probadas / L_totales) × 100
    Este conftest facilita la maximización de L_probadas.
=============================================================================
"""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch
from flask import Flask

# Configurar PYTHONPATH para acceder a los módulos del proyecto
project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../")
)
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))


# =========================================================================
# FIXTURE: Aplicación Flask de pruebas
# =========================================================================
@pytest.fixture
def app():
    """
    Crea una instancia de Flask con todos los blueprints registrados
    en modo testing. Usa una base de datos SQLite en memoria para
    aislar las pruebas de la BD de producción.
    """
    from src.routes.payments import payments_bp
    from src.routes.users import users_bp
    from src.routes.category import category_bp
    from src.routes.groups import group_bp
    from src.routes.messages import message_bp
    from src.routes.account import account_bp
    from src.routes.balance import balance_bp
    from src.routes.managmentAdmin import managmentAdmin_bp

    test_app = Flask(__name__)
    test_app.secret_key = "test_secret_key_iso25000"
    test_app.testing = True

    # Registrar blueprints con los mismos prefijos que producción
    test_app.register_blueprint(users_bp, url_prefix="")
    test_app.register_blueprint(payments_bp, url_prefix="")
    test_app.register_blueprint(category_bp, url_prefix="/api/category")
    test_app.register_blueprint(group_bp, url_prefix="/api/groups")
    test_app.register_blueprint(message_bp, url_prefix="")
    test_app.register_blueprint(account_bp, url_prefix="/account")
    test_app.register_blueprint(balance_bp, url_prefix="/api")
    test_app.register_blueprint(
        managmentAdmin_bp, url_prefix="/api/managment"
    )

    return test_app


# =========================================================================
# FIXTURE: Cliente HTTP de pruebas
# =========================================================================
@pytest.fixture
def client(app):
    """Cliente de pruebas Flask para realizar peticiones HTTP."""
    return app.test_client()


# =========================================================================
# FIXTURE: Sesión de usuario autenticado
# =========================================================================
@pytest.fixture
def authenticated_client(client):
    """
    Cliente con sesión de usuario autenticado simulada.
    Inyecta datos de sesión similares a los que genera verify-token.
    """
    with client.session_transaction() as sess:
        sess["user"] = {
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
    return client


# =========================================================================
# FIXTURE: Sesión de usuario vendedor
# =========================================================================
@pytest.fixture
def seller_client(client):
    """
    Cliente con sesión de usuario que ya ha comprado (vendedor).
    Útil para probar restricciones de acceso.
    """
    with client.session_transaction() as sess:
        sess["user"] = {
            "google_id": "seller_google_id_999",
            "email": "seller@gmail.com",
            "name": "Seller User",
            "given_name": "Seller",
            "picture": "https://lh3.googleusercontent.com/a/default-user",
            "accounts": [],
            "prefix": "+57",
            "num_whatsapp": "",
            "is_bought": True,
            "country": "CO",
            "tasa_de_cambio": "4000",
        }
    return client


# =========================================================================
# DATOS DE PRUEBA REUTILIZABLES
# =========================================================================
@pytest.fixture
def sample_payu_payload():
    """Payload estándar para webhook de confirmación PayU."""
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
    """Payload estándar para webhook de PayPal."""
    return {
        "event_type": "PAYMENTS.PAYMENT.CREATED",
        "resource": {
            "id": "PAY-TEST-001",
            "payer": {
                "payer_info": {
                    "payer_id": "PAYER-TEST-001"
                }
            },
            "transactions": [
                {"description": "REF-CODE-001"}
            ],
        },
    }


@pytest.fixture
def sample_categories_payload():
    """Payload estándar para generación de firmas."""
    return {
        "categories": [
            {"id_category": 1},
            {"id_category": 2},
        ]
    }
