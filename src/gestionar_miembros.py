import os

from googleapiclient.errors import HttpError

from servises.groups.admin_directory_client import ejecutar_con_reintento_401


def menu_gestion_miembros():
    """Menú interactivo para gestionar miembros de los grupos (Admin SDK)."""
    print("\n" + "=" * 50)
    print(" 🛠️  GESTOR DE MIEMBROS DE GOOGLE GROUPS")
    print("=" * 50)
    print("1. Agregar persona a un grupo")
    print("2. Quitar persona de un grupo")
    print("3. Ver miembros de un grupo (cantidad y correos)")
    print("=" * 50)

    opcion = input("Elige una opción (1, 2 o 3): ").strip()

    if opcion not in ["1", "2", "3"]:
        print("❌ Opción no válida. Por favor, ejecuta el script de nuevo y elige 1, 2 o 3.")
        return

    correo_grupo = input("\nIngresa el correo del GRUPO (ej. 104marketing...): ").strip()

    try:
        if opcion == "1":
            correo_usuario = input("Ingresa el correo del USUARIO a agregar: ").strip()
            print(f"\nAgregando a {correo_usuario} al grupo {correo_grupo}...")

            def _add(s):
                return (
                    s.members()
                    .insert(
                        groupKey=correo_grupo,
                        body={"email": correo_usuario, "role": "MEMBER"},
                    )
                    .execute()
                )

            ejecutar_con_reintento_401(_add)
            print("✅ ¡Usuario agregado con éxito!")

        elif opcion == "2":
            correo_usuario = input("Ingresa el correo del USUARIO a quitar: ").strip()
            print(f"\nQuitando a {correo_usuario} del grupo {correo_grupo}...")

            def _del(s):
                return s.members().delete(
                    groupKey=correo_grupo, memberKey=correo_usuario
                ).execute()

            ejecutar_con_reintento_401(_del)
            print("✅ ¡Usuario eliminado con éxito!")

        elif opcion == "3":
            print(f"\nObteniendo miembros de {correo_grupo}...")

            def _list(s):
                return (
                    s.members().list(groupKey=correo_grupo).execute().get("members", [])
                )

            miembros = ejecutar_con_reintento_401(_list) or []

            if not miembros:
                print("ℹ️ El grupo no tiene miembros actualmente.")
            else:
                print(f"\n👥 Total de miembros encontrados: {len(miembros)}")
                print("-" * 30)
                for miembro in miembros:
                    rol = miembro.get("role", "Desconocido")
                    email = miembro.get("email", "Sin correo")
                    print(f"- {email} ({rol})")
                print("-" * 30)

    except HttpError as e:
        if e.resp.status == 409:
            print("⚠️ Error: El usuario ya es miembro de este grupo.")
        elif e.resp.status == 404:
            print(
                "⚠️ Error: No se encontró el grupo o el usuario. Revisa que los correos estén bien escritos."
            )
        else:
            print(f"❌ Error al conectar con Google: {e.reason}")
    except Exception as e:
        print(f"❌ Ocurrió un error inesperado: {e}")


if __name__ == "__main__":
    menu_gestion_miembros()
