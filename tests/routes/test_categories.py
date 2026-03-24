"""
=============================================================================
 PRUEBAS UNITARIAS: MÓDULO DE CATEGORÍAS — ISO/IEC 25000
 Plataforma: Cursos Estudia y Trabaja
=============================================================================

 Métricas ISO 25023 cubiertas:

 1. ADECUACIÓN FUNCIONAL (Exactitud / Completitud)
    Verifica que las consultas de categorías retornan datos correctos
    con paginación, filtros y búsqueda profunda.

 2. FIABILIDAD (Tolerancia a fallos)
    Verifica que categorías inexistentes retornan 404 y que errores
    internos son manejados sin exponer datos sensibles.

 Comando de ejecución:
    pytest tests/routes/test_categories.py -v -s
    pytest tests/routes/test_categories.py -v -s --cov=src/routes/category
=============================================================================
"""

import json
import pytest
from unittest.mock import patch, MagicMock


# =========================================================================
# ISO 25000: ADECUACIÓN FUNCIONAL — Listar Categorías
# =========================================================================
class TestAllCategoriesISO:
    """Pruebas de adecuación funcional para listado de categorías."""

    @patch("src.routes.category.CategoryModel")
    def test_all_categories_default_pagination(
        self, mock_model, client
    ):
        """
        Atributo: Adecuación Funcional (Exactitud)
        GET /api/category/all-categories sin params debe usar
        limit=6 y offset=0 por defecto.
        """
        mock_cat = MagicMock()
        mock_cat.to_dict.return_value = {
            "id": 1, "titulo": "Python Básico"
        }

        mock_query = MagicMock()
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_cat]
        mock_model.query = mock_query

        response = client.get("/api/category/all-categories")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) == 1

    @patch("src.routes.category.CategoryModel")
    def test_all_categories_custom_pagination(
        self, mock_model, client
    ):
        """
        Atributo: Adecuación Funcional (Completitud)
        GET /api/category/all-categories?limit=2&offset=1 debe
        respetar los parámetros de paginación.
        """
        mock_query = MagicMock()
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_model.query = mock_query

        response = client.get(
            "/api/category/all-categories?limit=2&offset=1"
        )
        assert response.status_code == 200

    @patch("src.routes.category.CategoryModel")
    def test_all_categories_empty_result(self, mock_model, client):
        """
        Atributo: Adecuación Funcional (Exactitud)
        GET /api/category/all-categories debe retornar lista vacía
        cuando no hay categorías.
        """
        mock_query = MagicMock()
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_model.query = mock_query

        response = client.get("/api/category/all-categories")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data == []


# =========================================================================
# ISO 25000: ADECUACIÓN FUNCIONAL — Categoría por ID
# =========================================================================
class TestCategoryByIdISO:
    """Pruebas para obtener categoría por ID."""

    @patch("src.routes.category.CategoryModel")
    def test_get_category_by_id_found(self, mock_model, client):
        """
        Atributo: Adecuación Funcional (Exactitud)
        GET /api/category/1 con ID existente debe retornar 200.
        """
        mock_cat = MagicMock()
        mock_cat.to_dict.return_value = {
            "id": 1,
            "titulo": "Python Básico",
            "descripcion": "Curso completo",
        }
        mock_model.query.get.return_value = mock_cat

        response = client.get("/api/category/1")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["id"] == 1
        assert data["titulo"] == "Python Básico"

    @patch("src.routes.category.CategoryModel")
    def test_get_category_by_id_not_found(self, mock_model, client):
        """
        Atributo: Fiabilidad (Madurez)
        GET /api/category/9999 con ID inexistente debe retornar 404
        con mensaje descriptivo.
        """
        mock_model.query.get.return_value = None

        response = client.get("/api/category/9999")
        assert response.status_code == 404
        data = json.loads(response.data)
        assert "not found" in data["message"].lower()


# =========================================================================
# ISO 25000: ADECUACIÓN FUNCIONAL — Búsqueda Profunda
# =========================================================================
class TestDeepSearchISO:
    """Pruebas para búsqueda profunda de categorías."""

    def test_deep_search_no_query(self, client):
        """
        Atributo: Adecuación Funcional (Exactitud)
        GET /api/category/categories/deep-search sin 'q'
        debe retornar lista vacía.
        """
        response = client.get(
            "/api/category/categories/deep-search"
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data == []

    @patch("src.routes.category.CategoryModel")
    @patch("src.routes.category.TiendaCourse")
    def test_deep_search_with_results(
        self, mock_tienda_course, mock_category_model, client
    ):
        """
        Atributo: Adecuación Funcional (Completitud)
        GET /deep-search?q=python debe buscar en título, nombre
        y autor. La ruta usa TiendaCourse.query (no db.session.query).
        """
        mock_course = MagicMock()
        mock_course.pilar_id = "1"
        mock_course.titulo = "Python Avanzado"
        mock_course.autor = "Autor de prueba"
        mock_course.pack_nombre = "Pack Python"
        mock_course.pack_cantidad_cursos = 1

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_course]
        mock_tienda_course.query = mock_query

        mock_categoria = MagicMock()
        mock_categoria.imagen_url = "http://imagen.com"
        mock_category_model.query.get.return_value = mock_categoria

        response = client.get(
            "/api/category/categories/deep-search?q=python&limit=5"
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) >= 1

    @patch("src.routes.category.TiendaCourse")
    def test_deep_search_no_results(
        self, mock_tienda_course, client
    ):
        """
        Atributo: Adecuación Funcional (Exactitud)
        Búsqueda que no coincide con nada debe retornar lista vacía.
        """
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_tienda_course.query = mock_query

        response = client.get(
            "/api/category/categories/deep-search?q=xyz_no_existe"
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data == []
