"""Pruebas — grupos (FastAPI)."""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException


class TestCreateGroupISO:
    @patch("routes.groups.GroupRepository")
    @patch("routes.groups.ValidateData")
    def test_create_group_happy_path(self, mock_validate, mock_repo, client):
        mock_validate.validate_request_data.return_value = {
            "group_email": "test@cursosestudiaytrabaja.com",
            "group_name": "test_group",
            "group_description": "Descripción de prueba",
        }
        mock_instance = mock_repo.return_value
        mock_instance.crear_grupo.return_value = {
            "group_email": "test@cursosestudiaytrabaja.com",
            "group_name": "test_group",
        }

        response = client.post(
            "/api/groups/create-group",
            json={
                "group_email": "test@cursosestudiaytrabaja.com",
                "group_name": "test_group",
                "group_description": "Descripción de prueba",
            },
        )
        assert response.status_code == 201

    @patch("routes.groups.ValidateData")
    def test_create_group_missing_fields(self, mock_validate, client):
        mock_validate.validate_request_data.side_effect = HTTPException(
            status_code=400, detail="Falta el parámetro: group_email"
        )

        response = client.post(
            "/api/groups/create-group",
            json={"group_description": "Solo descripción"},
        )
        assert response.status_code == 400

    @patch("routes.groups.GroupRepository")
    @patch("routes.groups.ValidateData")
    def test_create_group_api_failure(self, mock_validate, mock_repo, client):
        mock_validate.validate_request_data.return_value = {
            "group_email": "fail@test.com",
            "group_name": "fail",
            "group_description": "Forzar fallo",
        }
        mock_instance = mock_repo.return_value
        mock_instance.crear_grupo.return_value = None

        response = client.post(
            "/api/groups/create-group",
            json={
                "group_email": "fail@test.com",
                "group_name": "fail",
                "group_description": "Forzar fallo",
            },
        )
        assert response.status_code == 400


class TestAddMemberISO:
    @patch("routes.groups.GroupRepository.process_member_addition")
    @patch("routes.groups.ValidateData")
    def test_add_member_happy_path(self, mock_validate, mock_proc, client):
        mock_validate.validate_request_data.return_value = {"extra1": "1,g1,g2"}
        mock_proc.return_value = {"ok": True}

        response = client.post(
            "/api/groups/add-member",
            json={"extra1": "1,g1,g2"},
        )
        assert response.status_code == 200


class TestRemoveMemberISO:
    @patch("routes.groups.GroupRepository")
    @patch("routes.groups.ValidateData")
    def test_remove_member_happy_path(self, mock_validate, mock_repo, client):
        mock_validate.validate_request_data.return_value = {
            "group_email": "g@test.com",
            "member_email": "m@test.com",
        }
        mock_instance = mock_repo.return_value
        mock_instance.eliminar_miembro_grupo.return_value = True

        body = json.dumps(
            {"group_email": "g@test.com", "member_email": "m@test.com"}
        )
        response = client.request(
            "DELETE",
            "/api/groups/remove-member",
            content=body,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200

    @patch("routes.groups.GroupRepository")
    @patch("routes.groups.ValidateData")
    def test_remove_member_failure(self, mock_validate, mock_repo, client):
        mock_validate.validate_request_data.return_value = {
            "group_email": "g@test.com",
            "member_email": "m@test.com",
        }
        mock_instance = mock_repo.return_value
        mock_instance.eliminar_miembro_grupo.return_value = False

        body = json.dumps(
            {"group_email": "g@test.com", "member_email": "m@test.com"}
        )
        response = client.request(
            "DELETE",
            "/api/groups/remove-member",
            content=body,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400
