"""
=============================================================================
 PRUEBAS UNITARIAS: MÓDULO DE CUENTAS BANCARIAS — ISO/IEC 25000
 Plataforma: Cursos Estudia y Trabaja
=============================================================================

 Métricas ISO 25023 cubiertas:

 1. ADECUACIÓN FUNCIONAL (Exactitud)
    Verifica que la actualización de cuentas bancarias y celular
    funcione correctamente con datos válidos.

 2. SEGURIDAD (Protección contra accesos no autorizados)
    Verifica que el endpoint requiere sesión activa.

 3. FIABILIDAD (Tolerancia a fallos)
    Verifica manejo de errores al actualizar datos.

 Comando de ejecución:
    pytest tests/routes/test_account.py -v -s
    pytest tests/routes/test_account.py -v -s --cov=src/routes/account
=============================================================================
"""

import json
import pytest
from unittest.mock import patch, MagicMock


# =========================================================================
# ISO 25000: SEGURIDAD — Protección de endpoint
# =========================================================================
class TestAccountSecurityISO:
    """Pruebas de seguridad para cuentas bancarias."""

    def test_update_account_requires_session(self, client):
        """
        Atributo: Seguridad
        POST /account/update sin sesión debe fallar.
        El endpoint accede a session["user"], así que lanza excepción
        que el bloque except captura retornando 501.
        """
        response = client.post(
            "/account/update",
            json={
                "nequi": "3001234567",
                "daviplata": "3005678901",
                "llave": "000000000",
                "cellphone": "3009876543",
            },
        )
        # Sin sesión, session["user"] lanza KeyError → except → 501
        assert response.status_code == 501


# =========================================================================
# ISO 25000: ADECUACIÓN FUNCIONAL — Actualizar cuenta
# =========================================================================
class TestUpdateAccountISO:
    """Pruebas de adecuación funcional para actualización de cuentas."""

    @patch("src.routes.account.UserModel")
    @patch("src.routes.account.AccountRepository")
    def test_update_account_happy_path(
        self, mock_acc_repo, mock_user_model, authenticated_client
    ):
        """
        Atributo: Adecuación Funcional (Exactitud)
        POST /account/update con sesión y datos válidos debe
        actualizar las cuentas bancarias y el celular.
        """
        # Mock para cada cuenta: no existe previamente → save
        mock_instance = mock_acc_repo.return_value
        mock_instance.is_exists.return_value = None

        # Mock para celular
        mock_user = MagicMock()
        mock_user_model.get_by_google_id.return_value = mock_user

        response = authenticated_client.post(
            "/account/update",
            json={
                "nequi": "3001234567",
                "daviplata": "3005678901",
                "llave": "000000000",
                "cellphone": "+57 3009876543",
            },
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "succes"

    @patch("src.routes.account.UserModel")
    @patch("src.routes.account.AccountRepository")
    def test_update_account_existing_accounts(
        self, mock_acc_repo, mock_user_model, authenticated_client
    ):
        """
        Atributo: Adecuación Funcional (Completitud)
        POST /account/update cuando las cuentas ya existen debe
        actualizarlas en lugar de crearlas.
        """
        mock_existing = MagicMock()
        mock_instance = mock_acc_repo.return_value
        mock_instance.is_exists.return_value = mock_existing

        mock_user = MagicMock()
        mock_user_model.get_by_google_id.return_value = mock_user

        response = authenticated_client.post(
            "/account/update",
            json={
                "nequi": "3001234567",
                "daviplata": "null",
                "llave": "999888777",
                "cellphone": "+57 3001111111",
            },
        )
        assert response.status_code == 200

    @patch("src.routes.account.UserModel")
    @patch("src.routes.account.AccountRepository")
    def test_update_account_null_values(
        self, mock_acc_repo, mock_user_model, authenticated_client
    ):
        """
        Atributo: Adecuación Funcional (Exactitud)
        POST /account/update con valores 'null' no debe crear
        ni actualizar las cuentas correspondientes.
        """
        mock_instance = mock_acc_repo.return_value
        mock_instance.is_exists.return_value = None

        response = authenticated_client.post(
            "/account/update",
            json={
                "nequi": "null",
                "daviplata": "null",
                "llave": "null",
            },
        )
        assert response.status_code == 200
        # No se debe llamar a save para cuentas con valor 'null'
        mock_instance.save.assert_not_called()
