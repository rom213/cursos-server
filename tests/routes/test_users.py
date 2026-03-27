"""
=============================================================================
 PRUEBAS UNITARIAS: MÓDULO DE USUARIOS — ISO/IEC 25000
 Plataforma: Cursos Estudia y Trabaja
=============================================================================

 Métricas ISO 25023 cubiertas:

 1. ADECUACIÓN FUNCIONAL (Exactitud / Completitud)
    Verifica que cada endpoint retorna los datos correctos según spec.

 2. SEGURIDAD (Protección contra accesos no autorizados)
    Verifica que endpoints protegidos rechacen peticiones sin sesión.

 3. FIABILIDAD (Tolerancia a fallos)
    Verifica que el sistema maneje gracefully tokens inválidos,
    emails malformados y errores internos.

 Comando de ejecución:
    pytest tests/routes/test_users.py -v -s
    pytest tests/routes/test_users.py -v -s --cov=src/routes/users
=============================================================================
"""

import json
import pytest
from unittest.mock import patch, MagicMock


# =========================================================================
# ISO 25000: SEGURIDAD — Protección de endpoints con sesión
# =========================================================================
class TestUsersSecurityISO:
    """Pruebas de seguridad: accesos no autorizados."""

    def test_profile_requires_session(self, client):
        """
        Atributo: Seguridad
        POST /profile sin sesión debe retornar 401.
        """
        response = client.post("/profile")
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False

    def test_user_by_google_id_requires_session(self, client):
        """
        Atributo: Seguridad
        GET /user/<googleid> sin sesión debe retornar 401.
        """
        response = client.get("/user/118070327157829661695")
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False

    def test_user_by_google_id_seller_blocked(self, seller_client):
        """
        Atributo: Seguridad
        Un usuario vendedor (is_bought=True) no puede acceder a
        GET /user/<googleid> — debe retornar 403.
        """
        response = seller_client.get("/user/some_other_google_id")
        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False


# =========================================================================
# ISO 25000: ADECUACIÓN FUNCIONAL — Verify Token
# =========================================================================
class TestVerifyTokenISO:
    """Pruebas de adecuación funcional para autenticación."""

    def test_verify_token_missing_token(self, client):
        """
        Atributo: Adecuación Funcional (Completitud)
        POST /verify-token sin token debe retornar 400.
        """
        response = client.post(
            "/verify-token",
            json={},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "Token missing" in data["error"]

    def test_verify_token_empty_token(self, client):
        """
        Atributo: Fiabilidad (Tolerancia a Fallos)
        POST /verify-token con token vacío debe retornar 400.
        """
        response = client.post(
            "/verify-token",
            json={"token": ""},
        )
        assert response.status_code == 400

    @patch("routes.users.auth_service")
    def test_verify_token_invalid_token(self, mock_auth, client):
        """
        Atributo: Fiabilidad (Madurez)
        POST /verify-token con token inválido debe retornar 401
        sin exponer datos internos.
        """
        mock_auth.authenticate.return_value = (
            {"error": "Invalid token: could not verify"},
            False
        )

        response = client.post(
            "/verify-token",
            json={"token": "token_invalido_completamente"},
        )
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False

    @patch("routes.users.SystemVariable")
    @patch("routes.users.UserModel")
    @patch("routes.users.auth_service")
    def test_verify_token_happy_path(
        self, mock_auth, mock_user_model, mock_sys_var, client
    ):
        """
        Atributo: Adecuación Funcional (Exactitud)
        POST /verify-token con token válido debe retornar 200
        con datos del usuario y sesión configurada.
        """
        # Mock del usuario
        mock_user = MagicMock()
        mock_user.google_id = "test_google_id_123"
        mock_user.email = "test@gmail.com"
        mock_user.name = "Test User"
        mock_user.picture = "https://example.com/pic.jpg"
        mock_user.country = "CO"
        mock_user.accounts = []
        mock_user.num_whatsapp = "+57 3001234567"

        mock_auth.authenticate.return_value = (
            {"user_data": mock_user, "is_new_user": False},
            True
        )
        mock_user_model.is_vendedor.return_value = False

        # Mock SystemVariable
        mock_tasa = MagicMock()
        mock_tasa.dato = "4000"
        mock_sys_var.query.filter_by.return_value.first.return_value = (
            mock_tasa
        )

        response = client.post(
            "/verify-token",
            json={"token": "token_google_valido"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["user"]["email"] == "test@gmail.com"
        assert data["user"]["google_id"] == "test_google_id_123"


# =========================================================================
# ISO 25000: ADECUACIÓN FUNCIONAL — Logout
# =========================================================================
class TestLogoutISO:
    """Pruebas de adecuación funcional para cierre de sesión."""

    def test_logout_clears_session(self, authenticated_client):
        """
        Atributo: Adecuación Funcional (Exactitud)
        POST /logout debe limpiar la sesión y retornar éxito.
        """
        response = authenticated_client.post("/logout")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Sesión cerrada" in data["message"]


# =========================================================================
# ISO 25000: ADECUACIÓN FUNCIONAL — Validate Email
# =========================================================================
class TestValidateEmailISO:
    """Pruebas de adecuación funcional para validación de email."""

    def test_validate_email_missing(self, client):
        """
        Atributo: Fiabilidad
        POST /validate-email sin email debe retornar 400.
        """
        response = client.post(
            "/validate-email",
            json={},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["status"] == "error"

    def test_validate_email_non_gmail(self, client):
        """
        Atributo: Adecuación Funcional (Exactitud)
        POST /validate-email con email que no sea Gmail debe retornar 400.
        """
        response = client.post(
            "/validate-email",
            json={"email": "usuario@hotmail.com"},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["status"] == "error"
        assert "Gmail" in data["message"]

    @patch("routes.users.user_repository")
    def test_validate_email_creates_user(self, mock_repo, client):
        """
        Atributo: Adecuación Funcional (Completitud)
        POST /validate-email con Gmail válido que no existe en BD
        debe crear el usuario y retornar 200.
        """
        mock_repo.get_by_email.return_value = None
        mock_user = MagicMock()
        mock_user.to_dict.return_value = {
            "google_id": "generated_uuid",
            "email": "nuevo@gmail.com",
            "name": "nuevo",
        }
        mock_repo.create_with_generated_id.return_value = mock_user

        response = client.post(
            "/validate-email",
            json={"email": "nuevo@gmail.com"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["records"]) == 1

    @patch("routes.users.user_repository")
    def test_validate_email_existing_user(self, mock_repo, client):
        """
        Atributo: Adecuación Funcional (Exactitud)
        POST /validate-email con email existente en BD debe
        retornar el usuario existente sin crear duplicado.
        """
        mock_user = MagicMock()
        mock_user.to_dict.return_value = {
            "google_id": "existing_id",
            "email": "existente@gmail.com",
            "name": "Existente",
        }
        mock_repo.get_by_email.return_value = mock_user

        response = client.post(
            "/validate-email",
            json={"email": "existente@gmail.com"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        mock_repo.create_with_generated_id.assert_not_called()


# =========================================================================
# ISO 25000: ADECUACIÓN FUNCIONAL — Profile
# =========================================================================
class TestProfileISO:
    """Pruebas de adecuación funcional para perfil de usuario."""

    @patch("routes.users.SystemVariable")
    @patch("routes.users.UserModel")
    @patch("routes.users.user_repository")
    def test_profile_returns_user_data(
        self, mock_repo, mock_user_model, mock_sys_var,
        authenticated_client
    ):
        """
        Atributo: Adecuación Funcional (Exactitud)
        POST /profile con sesión activa debe retornar datos actualizados.
        """
        mock_user = MagicMock()
        mock_user.google_id = "118070327157829661695"
        mock_user.email = "testuser@gmail.com"
        mock_user.name = "Test User"
        mock_user.picture = "https://example.com/pic.jpg"
        mock_user.country = "CO"
        mock_user.accounts = []
        mock_user.num_whatsapp = ""
        mock_repo.get_by_google_id.return_value = mock_user
        mock_user_model.is_vendedor.return_value = False

        mock_tasa = MagicMock()
        mock_tasa.dato = "4000"
        mock_sys_var.query.filter_by.return_value.first.return_value = (
            mock_tasa
        )

        response = authenticated_client.post("/profile")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @patch("routes.users.user_repository")
    def test_profile_user_not_found(self, mock_repo, authenticated_client):
        """
        Atributo: Fiabilidad (Recuperabilidad)
        POST /profile cuando el usuario ya no existe en BD
        debe retornar 404 sin caer.
        """
        mock_repo.get_by_google_id.return_value = None

        response = authenticated_client.post("/profile")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
