"""
=============================================================================
 PRUEBAS UNITARIAS: MÓDULO DE GRUPOS — ISO/IEC 25000
 Plataforma: Cursos Estudia y Trabaja
=============================================================================

 Métricas ISO 25023 cubiertas:

 1. ADECUACIÓN FUNCIONAL (Exactitud)
    Verifica CRUD de grupos Google Workspace: crear, añadir y remover.

 2. FIABILIDAD (Tolerancia a fallos)
    Verifica manejo de campos faltantes y respuestas de error.

 Comando de ejecución:
    pytest tests/routes/test_groups.py -v -s
    pytest tests/routes/test_groups.py -v -s --cov=src/routes/groups
=============================================================================
"""

import json
import pytest
from unittest.mock import patch, MagicMock


# =========================================================================
# ISO 25000: ADECUACIÓN FUNCIONAL — Crear Grupo
# =========================================================================
class TestCreateGroupISO:
    """Pruebas de creación de grupos Google Workspace."""

    @patch("src.routes.groups.GroupRepository")
    @patch("src.routes.groups.ValidateData")
    def test_create_group_happy_path(
        self, mock_validate, mock_repo, client
    ):
        """
        Atributo: Adecuación Funcional (Exactitud)
        POST /api/groups/create-group con datos válidos debe
        retornar 201 y el grupo creado.
        """
        mock_validate.validate_request_data.return_value = (
            {
                "group_email": "test@cursosestudiaytrabaja.com",
                "group_name": "test_group",
                "group_description": "Descripción de prueba",
            },
            None,
        )
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

    @patch("src.routes.groups.ValidateData")
    def test_create_group_missing_fields(self, mock_validate, client):
        """
        Atributo: Fiabilidad (Madurez)
        POST /api/groups/create-group sin campos requeridos debe
        retornar un error de validación.
        """
        error_response = (
            {"error": "Campos faltantes: group_email, group_name"},
            400,
        )
        mock_validate.validate_request_data.return_value = (
            None,
            error_response,
        )

        response = client.post(
            "/api/groups/create-group",
            json={"group_description": "Solo descripción"},
        )
        assert response.status_code == 400

    @patch("src.routes.groups.GroupRepository")
    @patch("src.routes.groups.ValidateData")
    def test_create_group_api_failure(
        self, mock_validate, mock_repo, client
    ):
        """
        Atributo: Fiabilidad (Tolerancia a Fallos)
        Si la API de Google Workspace falla, debe retornar 400.
        """
        mock_validate.validate_request_data.return_value = (
            {
                "group_email": "fail@test.com",
                "group_name": "fail",
                "group_description": "Forzar fallo",
            },
            None,
        )
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


# =========================================================================
# ISO 25000: ADECUACIÓN FUNCIONAL — Añadir Miembro
# =========================================================================
class TestAddMemberISO:
    """Pruebas para añadir miembros a grupos."""

    @patch("src.routes.groups.GroupRepository")
    @patch("src.routes.groups.ValidateData")
    def test_add_member_happy_path(
        self, mock_validate, mock_repo, client
    ):
        """
        Atributo: Adecuación Funcional (Exactitud)
        POST /api/groups/add-member con datos válidos debe
        procesar la adición del miembro.
        """
        mock_validate.validate_request_data.return_value = (
            {"extra1": "|1,118070327157829661695"},
            None,
        )
        mock_repo.process_member_addition.return_value = (
            {"message": "Miembro añadido"},
            200,
        )

        response = client.post(
            "/api/groups/add-member",
            json={"extra1": "|1,118070327157829661695"},
        )
        assert response.status_code == 200


# =========================================================================
# ISO 25000: ADECUACIÓN FUNCIONAL — Remover Miembro
# =========================================================================
class TestRemoveMemberISO:
    """Pruebas para remover miembros de grupos."""

    @patch("src.routes.groups.GroupRepository")
    @patch("src.routes.groups.ValidateData")
    def test_remove_member_happy_path(
        self, mock_validate, mock_repo, client
    ):
        """
        Atributo: Adecuación Funcional (Exactitud)
        DELETE /api/groups/remove-member con datos válidos debe
        retornar 200 con mensaje de confirmación.
        """
        mock_validate.validate_request_data.return_value = (
            {
                "group_email": "hola24@cursosestudiaytrabaja.com",
                "member_email": "usuario@gmail.com",
            },
            None,
        )
        mock_instance = mock_repo.return_value
        mock_instance.eliminar_miembro_grupo.return_value = True

        response = client.delete(
            "/api/groups/remove-member",
            json={
                "group_email": "hola24@cursosestudiaytrabaja.com",
                "member_email": "usuario@gmail.com",
            },
        )
        assert response.status_code == 200

    @patch("src.routes.groups.GroupRepository")
    @patch("src.routes.groups.ValidateData")
    def test_remove_member_failure(
        self, mock_validate, mock_repo, client
    ):
        """
        Atributo: Fiabilidad (Tolerancia a Fallos)
        DELETE /api/groups/remove-member cuando la API falla
        debe retornar 400.
        """
        mock_validate.validate_request_data.return_value = (
            {
                "group_email": "grupo@test.com",
                "member_email": "user@gmail.com",
            },
            None,
        )
        mock_instance = mock_repo.return_value
        mock_instance.eliminar_miembro_grupo.return_value = False

        response = client.delete(
            "/api/groups/remove-member",
            json={
                "group_email": "grupo@test.com",
                "member_email": "user@gmail.com",
            },
        )
        assert response.status_code == 400
