"""
Pruebas manuales contra la Admin SDK Directory API (miembros de grupos).

Requisitos: credentials.json de cuenta de servicio con delegación y scopes de grupos.

Ejecutar desde el directorio src (donde está este archivo):
    python test_google_group_members.py add --group-email "grupo@dominio.com" --member-email "user@gmail.com"
    python test_google_group_members.py remove --group-email "grupo@dominio.com" --member-email "user@gmail.com"

Opcional: --role OWNER|MANAGER|MEMBER (solo add; por defecto MEMBER).
"""

from __future__ import annotations

import argparse
import json
import sys
from urllib.parse import quote

import requests

from generateTokenAcces import access_token, generate_token

ADMIN_MEMBERS_BASE = "https://admin.googleapis.com/admin/directory/v1/groups"


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def _member_path_segment(email: str) -> str:
    """Codifica el identificador del miembro para la ruta (emails con @, etc.)."""
    return quote(email, safe="")


def add_member(
    group_email: str,
    member_email: str,
    role: str = "MEMBER",
) -> tuple[int, dict | list | str | None]:
    global access_token
    url = f"{ADMIN_MEMBERS_BASE}/{quote(group_email, safe='')}/members"
    payload = {"email": member_email, "role": role}
    headers = _headers(access_token)
    print('access_token')
    print(access_token)
    print('--------------------------------')
    response = requests.post(url, headers=headers, data=json.dumps(payload))

    if response.status_code == 401:
        print("Token expirado. Renovando...")
        access_token = generate_token()
        headers = _headers(access_token)
        response = requests.post(url, headers=headers, data=json.dumps(payload))


    body: dict | list | str | None
    try:
        body = response.json()
    except json.JSONDecodeError:
        body = response.text or None

    return response.status_code, body


def remove_member(group_email: str, member_email: str) -> tuple[int, str | None]:
    global access_token
    url = (
        f"{ADMIN_MEMBERS_BASE}/{quote(group_email, safe='')}/members/"
        f"{_member_path_segment(member_email)}"
    )
    headers = _headers(access_token)

    response = requests.delete(url, headers=headers)

    if response.status_code == 401:
        print("Token expirado. Renovando...")
        access_token = generate_token()
        headers = _headers(access_token)
        response = requests.delete(url, headers=headers)

    text = response.text if response.text else None
    return response.status_code, text


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Añadir o quitar miembros de un grupo de Google Workspace (Admin SDK).",
        epilog=(
            "Ejemplos:\n"
            "  %(prog)s add --group-email grupo@dominio.com --member-email user@gmail.com\n"
            "  %(prog)s remove --group-email grupo@dominio.com --member-email user@gmail.com"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=False, metavar="command")

    p_add = sub.add_parser("add", help="Añadir miembro al grupo")
    p_add.add_argument("--group-email", required=True, help="Email del grupo")
    p_add.add_argument("--member-email", required=True, help="Email del usuario a añadir")
    p_add.add_argument(
        "--role",
        default="MEMBER",
        choices=("OWNER", "MANAGER", "MEMBER"),
        help="Rol en el grupo (por defecto MEMBER)",
    )

    p_rm = sub.add_parser("remove", help="Quitar miembro del grupo")
    p_rm.add_argument("--group-email", required=True, help="Email del grupo")
    p_rm.add_argument("--member-email", required=True, help="Email del usuario a quitar")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "add":
        status, body = add_member(
            args.group_email,
            args.member_email,
            role=args.role,
        )
        print(f"HTTP {status}")
        print(json.dumps(body, indent=2, ensure_ascii=False) if isinstance(body, (dict, list)) else body)
        return 0 if status in (200, 201) else 1

    if args.command == "remove":
        status, text = remove_member(args.group_email, args.member_email)
        print(f"HTTP {status}")
        if text:
            print(text)
        # 204 No Content = éxito típico en DELETE
        return 0 if status == 204 else 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
