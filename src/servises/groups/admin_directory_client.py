"""
Cliente compartido para Admin SDK Directory API (grupos y miembros).
Misma autenticación que generateTokenAcces / gestionar_miembros.
"""

from __future__ import annotations

from pathlib import Path

import generateTokenAcces
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# src/credentials.json (este archivo está en src/servises/groups/)
RUTA_CREDENTIALS = str(Path(__file__).resolve().parents[2] / "credentials.json")

SCOPES = ["https://www.googleapis.com/auth/admin.directory.group"]


def obtener_credenciales():
    """
    Cuenta de servicio + refresh (misma lógica que generateTokenAcces.generate_token).
    Actualiza generateTokenAcces.access_token para mantener paridad con el resto del proyecto.
    """
    creds = service_account.Credentials.from_service_account_file(
        RUTA_CREDENTIALS,
        scopes=SCOPES,
    )
    creds.refresh(Request())
    generateTokenAcces.access_token = creds.token
    return creds


def build_directory_service():
    return build("admin", "directory_v1", credentials=obtener_credenciales())


def ejecutar_con_reintento_401(api_call):
    """
    Ejecuta api_call(service) y devuelve su valor.
    Si 401, renueva token y reintenta una vez.
    """
    service = build_directory_service()
    try:
        return api_call(service)
    except HttpError as e:
        if getattr(e.resp, "status", None) != 401:
            raise
        print("Token expirado. Renovando...")
        generateTokenAcces.generate_token()
        return api_call(build_directory_service())
