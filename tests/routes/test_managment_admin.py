"""
=============================================================================
 PRUEBAS UNITARIAS: MÓDULO DE GESTIÓN ADMINISTRATIVA — ISO/IEC 25000
 Plataforma: Cursos Estudia y Trabaja
=============================================================================

 Métricas ISO 25023 cubiertas:

 1. ADECUACIÓN FUNCIONAL (Exactitud / Completitud)
    Verifica CRUD de reembolsos, referidos, pago masivo y cuentas.

 2. SEGURIDAD (Protección contra accesos no autorizados)
    Verifica que operaciones críticas requieren código de verificación.

 3. FIABILIDAD (Tolerancia a fallos)
    Verifica manejo de parámetros faltantes, fechas inválidas,
    IDs inexistentes y errores internos.

 Comando de ejecución:
    pytest tests/routes/test_managment_admin.py -v -s
    pytest tests/routes/test_managment_admin.py -v -s --cov=src/routes/managmentAdmin
=============================================================================
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO


# =========================================================================
# ISO 25000: ADECUACIÓN FUNCIONAL — Obtener Reembolsos
# =========================================================================
class TestGetRefundsISO:
    """Pruebas para obtener reembolsos con paginación."""

    @patch("src.routes.managmentAdmin.refund_model")
    def test_get_refunds_happy_path(self, mock_refund_model, client):
        """
        Atributo: Adecuación Funcional (Exactitud)
        GET /api/managment/refunds con fechas válidas debe retornar
        resultados paginados.
        """
        mock_refund_model.RefundQueryService.search_refunds.return_value = {
            "records": [],
            "total": 0,
            "pages": 0,
            "current_page": 1,
            "per_page": 10,
            "has_next": False,
            "has_prev": False,
        }

        response = client.get(
            "/api/managment/refunds"
            "?date_init=2024-01-01&date_end=2024-12-31"
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert "pagination" in data

    def test_get_refunds_missing_dates(self, client):
        """
        Atributo: Fiabilidad (Madurez)
        GET /api/managment/refunds sin fechas debe retornar 400.
        """
        response = client.get("/api/managment/refunds")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"

    def test_get_refunds_invalid_date_format(self, client):
        """
        Atributo: Fiabilidad (Tolerancia a Fallos)
        GET /api/managment/refunds con formato de fecha inválido
        debe retornar 400.
        """
        response = client.get(
            "/api/managment/refunds"
            "?date_init=31-12-2024&date_end=2024-12-31"
        )
        assert response.status_code == 400

    def test_get_refunds_invalid_pagination(self, client):
        """
        Atributo: Fiabilidad (Madurez)
        GET /api/managment/refunds con page < 1 debe retornar 400.
        """
        response = client.get(
            "/api/managment/refunds"
            "?date_init=2024-01-01&date_end=2024-12-31&page=0"
        )
        assert response.status_code == 400

    def test_get_refunds_date_range_inverted(self, client):
        """
        Atributo: Fiabilidad (Tolerancia a Fallos)
        GET /api/managment/refunds con date_init > date_end
        debe retornar 400.
        """
        response = client.get(
            "/api/managment/refunds"
            "?date_init=2024-12-31&date_end=2024-01-01"
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "mayor" in data["message"].lower()


# =========================================================================
# ISO 25000: SEGURIDAD — Crear Reembolso
# =========================================================================
class TestCreateRefundISO:
    """Pruebas de seguridad para la creación de reembolsos."""

    def test_create_refund_missing_verification_code(self, client):
        """
        Atributo: Seguridad
        POST /api/managment/refunds sin código de verificación
        debe retornar 400.
        """
        response = client.post(
            "/api/managment/refunds",
            data={"type_acc_em": "nequi"},
            content_type="multipart/form-data",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "código" in data["message"].lower() or "verificación" in data["message"].lower()

    @patch("src.routes.managmentAdmin.AuthService")
    def test_create_refund_invalid_verification_code(
        self, mock_auth, client, app
    ):
        """
        Atributo: Seguridad
        POST /api/managment/refunds con código inválido
        debe retornar 400.
        """
        mock_auth.verify_code.return_value = (
            False, "Código inválido o expirado"
        )

        response = client.post(
            "/api/managment/refunds",
            data={
                "verification_code": "000000",
                "type_acc_em": "nequi",
            },
            content_type="multipart/form-data",
        )
        assert response.status_code == 400

    @patch("src.routes.managmentAdmin.save_img")
    @patch("src.routes.managmentAdmin.validate_refer")
    @patch("src.routes.managmentAdmin.ReferModel")
    @patch("src.routes.managmentAdmin.AuthService")
    def test_create_refund_missing_required_fields(
        self, mock_auth, mock_refer_model, mock_validate,
        mock_save_img, client, app
    ):
        """
        Atributo: Fiabilidad (Madurez)
        POST /api/managment/refunds con campos faltantes
        debe retornar 400 indicando cuáles faltan.
        """
        mock_auth.verify_code.return_value = (True, "OK")

        response = client.post(
            "/api/managment/refunds",
            data={
                "verification_code": "123456",
                "type_acc_em": "nequi",
                # Faltan: type_acc_re, titular_acc_em, etc.
            },
            content_type="multipart/form-data",
        )
        assert response.status_code == 400


# =========================================================================
# ISO 25000: ADECUACIÓN FUNCIONAL — Referidos
# =========================================================================
class TestRefersISO:
    """Pruebas para consulta de referidos."""

    @patch("src.routes.managmentAdmin.Refer")
    def test_get_unpaid_refers(self, mock_refer, client):
        """
        Atributo: Adecuación Funcional (Exactitud)
        GET /api/managment/refers/unpaid con fechas válidas
        debe retornar los referidos no pagados.
        """
        # Configurar la cadena de query completa
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_refer.query.filter.return_value = mock_query

        # Configurar atributos de columna con operadores de
        # comparación explícitos para evitar TypeError con datetime
        mock_col = MagicMock()
        mock_col.__ge__ = MagicMock(return_value=MagicMock())
        mock_col.__le__ = MagicMock(return_value=MagicMock())
        mock_refer.created_at = mock_col
        mock_refer.refund_id = MagicMock()

        response = client.get(
            "/api/managment/refers/unpaid"
            "?date_init=2024-01-01&date_end=2024-12-31"
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"

    @patch("src.routes.managmentAdmin.Refer")
    def test_get_paid_refers(self, mock_refer, client):
        """
        Atributo: Adecuación Funcional (Completitud)
        GET /api/managment/refers/paid con fechas válidas.
        """
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_refer.query.filter.return_value = mock_query

        mock_col = MagicMock()
        mock_col.__ge__ = MagicMock(return_value=MagicMock())
        mock_col.__le__ = MagicMock(return_value=MagicMock())
        mock_refer.created_at = mock_col
        mock_refer.refund_id = MagicMock()

        response = client.get(
            "/api/managment/refers/paid"
            "?date_init=2024-01-01&date_end=2024-12-31"
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"

    @patch("src.routes.managmentAdmin.Refer")
    def test_get_refer_by_id(self, mock_refer, client):
        """
        Atributo: Adecuación Funcional (Exactitud)
        GET /api/managment/refer/<refer_id> debe retornar
        el referido específico.
        """
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_refer.query = mock_query

        response = client.get("/api/managment/refer/1")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"


# =========================================================================
# ISO 25000: ADECUACIÓN FUNCIONAL — Cuentas por Usuario
# =========================================================================
class TestUserAccountsISO:
    """Pruebas para consulta de cuentas por usuario."""

    @patch("src.routes.managmentAdmin.UserModel")
    def test_user_accounts_not_found(self, mock_user_model, client):
        """
        Atributo: Fiabilidad (Madurez)
        GET /api/managment/user/accounts/<googleid> con usuario
        inexistente debe retornar 404.
        """
        mock_user_model.get_accounts_by_google_id.return_value = None

        response = client.get(
            "/api/managment/user/accounts/no_existe_99999"
        )
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data["status"] == "error"

    @patch("src.routes.managmentAdmin.UserModel")
    def test_user_accounts_no_accounts(self, mock_user_model, client):
        """
        Atributo: Fiabilidad (Madurez)
        GET /api/managment/user/accounts/<googleid> con usuario
        que no tiene cuentas debe retornar 404.
        """
        mock_user = MagicMock()
        mock_user.accounts = []
        mock_user_model.get_accounts_by_google_id.return_value = (
            mock_user
        )

        response = client.get(
            "/api/managment/user/accounts/118070327157829661695"
        )
        assert response.status_code == 404

    @patch("src.routes.managmentAdmin.UserModel")
    def test_user_accounts_happy_path(self, mock_user_model, client):
        """
        Atributo: Adecuación Funcional (Exactitud)
        GET /api/managment/user/accounts/<googleid> con usuario
        que tiene cuentas debe retornar 200.
        """
        mock_acc = MagicMock()
        mock_acc.to_dict.return_value = {
            "name_acc": "nequi",
            "number_acc": "3001234567",
        }
        mock_user = MagicMock()
        mock_user.accounts = [mock_acc]
        mock_user_model.get_accounts_by_google_id.return_value = (
            mock_user
        )

        response = client.get(
            "/api/managment/user/accounts/118070327157829661695"
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"


# =========================================================================
# ISO 25000: SEGURIDAD — Pago Masivo
# =========================================================================
class TestMassPaymentISO:
    """Pruebas de seguridad para pago masivo."""

    def test_mass_payment_missing_verification_code(self, client):
        """
        Atributo: Seguridad
        POST /api/managment/mass-payment sin código de verificación
        debe retornar 400.
        """
        response = client.post(
            "/api/managment/mass-payment",
            data={"google_id": "test123"},
            content_type="multipart/form-data",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "verificación" in data["message"].lower() or "código" in data["message"].lower()

    @patch("src.routes.managmentAdmin.AuthService")
    def test_mass_payment_invalid_code(self, mock_auth, client):
        """
        Atributo: Seguridad
        POST /api/managment/mass-payment con código inválido
        debe retornar 400.
        """
        mock_auth.verify_code.return_value = (
            False, "Código expirado"
        )

        response = client.post(
            "/api/managment/mass-payment",
            data={
                "verification_code": "000000",
                "google_id": "test123",
            },
            content_type="multipart/form-data",
        )
        assert response.status_code == 400
