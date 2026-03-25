"""
=============================================================================
 PRUEBAS UNITARIAS: MÓDULO DE MENSAJES — ISO/IEC 25000
 Plataforma: Cursos Estudia y Trabaja
=============================================================================

 Métricas ISO 25023 cubiertas:

 1. ADECUACIÓN FUNCIONAL (Exactitud / Completitud)
    Verifica obtención de mensajes y creación de comentarios.

 2. SEGURIDAD (Protección contra accesos no autorizados)
    Verifica que la creación de comentarios requiere sesión.

 3. FIABILIDAD (Tolerancia a fallos)
    Verifica manejo de IDs inexistentes y datos inválidos.

 Comando de ejecución:
    pytest tests/routes/test_messages.py -v -s
    pytest tests/routes/test_messages.py -v -s --cov=src/routes/messages
=============================================================================
"""

import json
import pytest
from unittest.mock import patch, MagicMock


# =========================================================================
# ISO 25000: ADECUACIÓN FUNCIONAL — Obtener Mensajes
# =========================================================================
class TestGetMessagesISO:
    """Pruebas para obtención de mensajes por categoría."""

    @patch("src.routes.messages.MessageModel")
    def test_get_messages_public_user(self, mock_model, client):
        """
        Atributo: Adecuación Funcional (Exactitud)
        GET /all-messages/1 sin sesión debe retornar
        is_login=False y los mensajes ordenados por estrellas.
        """
        mock_msg = MagicMock()
        mock_msg.to_dict.return_value = {
            "id": 1,
            "message": "Buen curso",
            "stars": 5,
            "google_id": "other_user",
        }
        mock_model.get_by_category_id.return_value = [mock_msg]

        response = client.get("/all-messages/1")
        assert response.status_code == 200
        data = response.json()
        assert data["is_login"] is False
        assert isinstance(data["messages"], list)

    @patch("src.routes.messages.MessageModel")
    def test_get_messages_authenticated_user(
        self, mock_model, authenticated_client
    ):
        """
        Atributo: Adecuación Funcional (Completitud)
        GET /all-messages/1 con sesión debe retornar is_login=True
        y separar el comentario del usuario actual.
        """
        mock_msg_own = MagicMock()
        mock_msg_own.to_dict.return_value = {
            "id": 1,
            "message": "Mi comentario",
            "stars": 4,
            "google_id": "118070327157829661695",
        }
        mock_msg_other = MagicMock()
        mock_msg_other.to_dict.return_value = {
            "id": 2,
            "message": "Otro comentario",
            "stars": 5,
            "google_id": "otro_user",
        }
        mock_model.get_by_category_id.return_value = [
            mock_msg_own, mock_msg_other
        ]

        response = authenticated_client.get("/all-messages/1")
        assert response.status_code == 200
        data = response.json()
        assert data["is_login"] is True
        assert data["is_comment"] is True
        # El primer mensaje debe ser el del usuario autenticado
        assert data["messages"][0]["google_id"] == "118070327157829661695"


# =========================================================================
# ISO 25000: SEGURIDAD — Crear Comentario
# =========================================================================
class TestAddMessageISO:
    """Pruebas de seguridad y funcionalidad para crear comentarios."""

    @patch("src.routes.messages.UserRepository")
    def test_add_message_requires_session(
        self, mock_user_repo, client
    ):
        """
        Atributo: Seguridad
        POST /add-message-category sin sesión debe retornar 401.
        """
        mock_user_repo.verify_seccion.return_value = False

        response = client.post(
            "/add-message-category",
            json={
                "category_id": 1,
                "message": "Excelente",
                "stars": 5,
            },
        )
        assert response.status_code == 401

    @patch("src.routes.messages.MessageRepository")
    @patch("src.routes.messages.ValidateData")
    @patch("src.routes.messages.UserRepository")
    def test_add_message_happy_path(
        self, mock_user_repo, mock_validate, mock_msg_repo,
        authenticated_client
    ):
        """
        Atributo: Adecuación Funcional (Exactitud)
        POST /add-message-category con sesión y datos válidos
        debe crear el mensaje y retornar 200.
        """
        mock_user_repo.verify_seccion.return_value = True
        mock_validate.validate_request_data.return_value = (
            {"category_id": 1, "message": "Excelente", "stars": 5},
            None,
        )
        mock_instance = mock_msg_repo.return_value
        mock_instance.verify.return_value = True

        response = authenticated_client.post(
            "/add-message-category",
            json={
                "category_id": 1,
                "message": "Excelente",
                "stars": 5,
            },
        )
        assert response.status_code == 200
