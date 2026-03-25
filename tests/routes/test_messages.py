"""
Pruebas — módulo de mensajes (FastAPI + JWT).
"""

from unittest.mock import MagicMock, patch

import pytest


class TestGetMessagesISO:
    @patch("routes.messages.MessageModel")
    def test_get_messages_public_user(self, mock_model, client):
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

    @patch("routes.messages.MessageModel")
    def test_get_messages_authenticated_user(self, mock_model, authenticated_client):
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
        mock_model.get_by_category_id.return_value = [mock_msg_own, mock_msg_other]

        response = authenticated_client.get("/all-messages/1")
        assert response.status_code == 200
        data = response.json()
        assert data["is_login"] is True
        assert data["is_comment"] is True
        assert data["messages"][0]["google_id"] == "118070327157829661695"


class TestAddMessageISO:
    def test_add_message_requires_session(self, client):
        response = client.post(
            "/add-message-category",
            json={"category_id": 1, "message": "Excelente", "stars": 5},
        )
        assert response.status_code == 401

    @patch("routes.messages.MessageRepository")
    @patch("routes.messages.ValidateData")
    def test_add_message_happy_path(
        self, mock_validate, mock_msg_repo, authenticated_client
    ):
        mock_validate.validate_request_data.return_value = {
            "category_id": 1,
            "message": "Excelente",
            "stars": 5,
        }
        mock_instance = mock_msg_repo.return_value
        mock_instance.verify = MagicMock()

        response = authenticated_client.post(
            "/add-message-category",
            json={"category_id": 1, "message": "Excelente", "stars": 5},
        )
        assert response.status_code == 200
