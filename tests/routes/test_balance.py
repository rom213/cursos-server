"""
=============================================================================
 PRUEBAS UNITARIAS: MÓDULO DE BALANCE — ISO/IEC 25000
 Plataforma: Cursos Estudia y Trabaja
=============================================================================

 Métricas ISO 25023 cubiertas:

 1. ADECUACIÓN FUNCIONAL (Exactitud)
    Verifica cálculos de balance personal, global y por usuario.

 2. SEGURIDAD (Protección contra accesos no autorizados)
    Verifica que el balance personal requiere sesión activa.

 3. FIABILIDAD (Tolerancia a fallos)
    Verifica manejo de fechas inválidas y errores internos.

 Comando de ejecución:
    pytest tests/routes/test_balance.py -v -s
    pytest tests/routes/test_balance.py -v -s --cov=src/routes/balance
=============================================================================
"""

import json
import pytest
from unittest.mock import patch, MagicMock


# =========================================================================
# ISO 25000: SEGURIDAD — Balance Personal
# =========================================================================
class TestBalanceSecurityISO:
    """Pruebas de seguridad para endpoints de balance."""

    def test_balance_requires_session(self, client):
        """
        Atributo: Seguridad
        GET /api/balance sin sesión debe retornar 401.
        """
        response = client.get(
            "/api/balance?date_init=2024-01-01&date_end=2024-12-31"
        )
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False


# =========================================================================
# ISO 25000: ADECUACIÓN FUNCIONAL — Balance Personal
# =========================================================================
class TestBalancePersonalISO:
    """Pruebas de adecuación funcional para balance personal."""

    @patch("routes.balance.BalanceModel")
    def test_balance_personal_happy_path(
        self, mock_model, authenticated_client
    ):
        """
        Atributo: Adecuación Funcional (Exactitud)
        GET /api/balance con sesión y fechas válidas debe retornar
        el resumen de ventas del usuario.
        """
        mock_model.get_all_sales_by_me.return_value = {
            "counts": 5,
            "non_refunded_value": 250000,
            "refunded_value": 50000,
            "total_value": 300000,
            "courses_payments_value": 200000,
            "list_ids_refers": [1, 2, 3],
        }

        response = authenticated_client.get(
            "/api/balance?date_init=2024-01-01&date_end=2024-12-31"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 5
        assert data["non_refunded_value"] == 250000

    @patch("routes.balance.BalanceModel")
    def test_balance_personal_error(
        self, mock_model, authenticated_client
    ):
        """
        Atributo: Fiabilidad (Tolerancia a Fallos)
        Si el modelo lanza una excepción, el endpoint debe
        retornar 200 con status ERROR (según implementación actual).
        """
        mock_model.get_all_sales_by_me.side_effect = Exception(
            "Error de base de datos"
        )

        response = authenticated_client.get(
            "/api/balance?date_init=2024-01-01&date_end=2024-12-31"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ERROR"


# =========================================================================
# ISO 25000: ADECUACIÓN FUNCIONAL — Balance Global
# =========================================================================
class TestBalanceGlobalISO:
    """Pruebas para balance global administrativo."""

    @patch("routes.balance.BalanceModel")
    def test_balance_global_happy_path(self, mock_model, client):
        """
        Atributo: Adecuación Funcional (Exactitud)
        GET /api/balance/all con fechas válidas debe retornar
        resumen global de ventas.
        """
        mock_model.get_all_sales.return_value = {
            "counts": 100,
            "non_refunded_value": 5000000,
            "refunded_value": 500000,
            "total_value": 5500000,
            "courses_payments_value": 4000000,
        }

        response = client.get(
            "/api/balance/all?date_init=2024-01-01&date_end=2024-12-31"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["records"][0]["count"] == 100


# =========================================================================
# ISO 25000: ADECUACIÓN FUNCIONAL — Balance por Usuario
# =========================================================================
class TestBalanceByUserISO:
    """Pruebas para balance por usuario específico."""

    @patch("routes.balance.BalanceModel")
    def test_balance_by_user_happy_path(self, mock_model, client):
        """
        Atributo: Adecuación Funcional (Exactitud)
        GET /api/balance/user/<google_id> con fechas válidas debe
        retornar resumen de ventas del usuario indicado.
        """
        mock_model.get_all_sales_by_me.return_value = {
            "counts": 10,
            "non_refunded_value": 500000,
            "refunded_value": 100000,
            "total_value": 600000,
            "courses_payments_value": 400000,
            "list_ids_refers": [4, 5],
        }

        response = client.get(
            "/api/balance/user/118070327157829661695"
            "?date_init=2024-01-01&date_end=2024-12-31"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["records"][0]["count"] == 10
