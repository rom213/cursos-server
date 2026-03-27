"""
Carga grupos desde documentacion_tecnica/grupos.json hacia la tabla `group`.

Prerrequisito: ejecutar antes la carga de categorías para que existan los FK:
    python load_categories_from_json.py
(o el mismo dataset desde el que salen los id de categoría: 101, 100200300, etc.)

Uso típico (desde el directorio src del proyecto):
    python load_groups_from_json.py
    python load_groups_from_json.py --json "C:/ruta/grupos.json"
    python load_groups_from_json.py --strict
"""

import argparse
import json
import re
from pathlib import Path

from json_repair import repair_json

import models  # noqa: F401 — registra todos los modelos en Base.metadata
from database import Base, engine, SessionLocal
from models.Category import Category
from models.Group import Group

# Mismo criterio que load_categories_from_json para JSON "sucios"
CONTROL_CHAR_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
INVALID_ESCAPE_PATTERN = re.compile(r'\\(?!["\\/bfnrt]|u[0-9a-fA-F]{4})')

DEFAULT_JSON_PATH = (
    Path(__file__).resolve().parents[2]
    / "documentacion_tecnica"
    / "grupos.json"
)

VARCHAR_LEN = 100


def read_json_file(json_path):
    for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            with open(json_path, "r", encoding=encoding) as file:
                raw = file.read()
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError(
            f"No se pudo decodificar el archivo {json_path} con utf-8, latin-1 ni cp1252"
        )
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    raw = CONTROL_CHAR_PATTERN.sub(" ", raw)
    raw = INVALID_ESCAPE_PATTERN.sub(r"\\\\", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return json.loads(repair_json(raw))


def resolve_category_id_from_json(category_id_raw):
    """
    Convierte el código del JSON (ej. "100.200.300" o "101") al entero Category.id
    del catálogo (dígitos concatenados sin puntos).
    """
    if category_id_raw is None:
        return None
    s = str(category_id_raw).strip().replace(".", "")
    if not s or not s.isdigit():
        return None
    try:
        return int(s)
    except ValueError:
        return None


def _fit_text(value, max_len, field_label, strict, truncatable):
    if value is None:
        return None, None
    text = str(value)
    if len(text) <= max_len:
        return text, None
    if not truncatable:
        return None, f"{field_label} supera {max_len} caracteres ({len(text)}); no se trunca"
    if strict:
        return None, f"{field_label} supera {max_len} caracteres ({len(text)}) en modo --strict"
    return text[:max_len], f"{field_label} truncado de {len(text)} a {max_len} caracteres"


def upsert_groups_from_rows(session, rows, strict=False):
    """
    Inserta o actualiza por group_mail. Omite filas con categoría inexistente o datos inválidos.
    """
    created = 0
    updated = 0
    skipped = 0
    warnings = []
    errors = []

    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"Fila {index}: no es un objeto JSON")
            skipped += 1
            continue

        raw_mail = row.get("group_mail")
        group_mail, mail_err = _fit_text(
            raw_mail, VARCHAR_LEN, "group_mail", strict=False, truncatable=False
        )
        if mail_err:
            errors.append(f"Fila {index} ({raw_mail!r}): {mail_err}")
            skipped += 1
            continue
        if not group_mail or not group_mail.strip():
            errors.append(f"Fila {index}: group_mail vacío o ausente")
            skipped += 1
            continue

        name, wn = _fit_text(
            row.get("name"), VARCHAR_LEN, "name", strict=strict, truncatable=True
        )
        if wn:
            warnings.append(f"Fila {index} group_mail={group_mail!r}: {wn}")
        if name is None and row.get("name") is not None:
            errors.append(f"Fila {index}: name inválido o demasiado largo (--strict)")
            skipped += 1
            continue

        description, wd = _fit_text(
            row.get("descripcion"),
            VARCHAR_LEN,
            "description",
            strict=strict,
            truncatable=True,
        )
        if wd:
            warnings.append(f"Fila {index} group_mail={group_mail!r}: {wd}")
        if description is None and row.get("descripcion") is not None:
            errors.append(f"Fila {index}: description inválida o demasiado larga (--strict)")
            skipped += 1
            continue

        count_val = row.get("count_menbers")
        if count_val is None:
            count_val = row.get("count_members")
        try:
            count_members = int(count_val) if count_val is not None else None
        except (TypeError, ValueError):
            errors.append(f"Fila {index} group_mail={group_mail!r}: count_menbers no numérico")
            skipped += 1
            continue

        resolved_cat = resolve_category_id_from_json(row.get("category_id"))
        if resolved_cat is None:
            errors.append(
                f"Fila {index} group_mail={group_mail!r}: category_id no resoluble: {row.get('category_id')!r}"
            )
            skipped += 1
            continue

        if session.get(Category, resolved_cat) is None:
            errors.append(
                f"Fila {index} group_mail={group_mail!r}: no existe category.id={resolved_cat}"
            )
            skipped += 1
            continue

        existing = session.query(Group).filter_by(group_mail=group_mail).first()
        if existing:
            existing.name = name
            existing.description = description
            existing.count_members = count_members
            existing.category_id = resolved_cat
            updated += 1
        else:
            session.add(
                Group(
                    name=name,
                    group_mail=group_mail,
                    description=description,
                    count_members=count_members,
                    category_id=resolved_cat,
                )
            )
            created += 1

    session.commit()
    return {
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "warnings": warnings,
        "errors": errors,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Carga/actualiza grupos desde JSON (upsert por group_mail)."
    )
    parser.add_argument(
        "--json",
        dest="json_path",
        default=str(DEFAULT_JSON_PATH),
        help="Ruta al archivo grupos.json",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fallar filas si name/description superan VARCHAR(100) (no truncar).",
    )
    args = parser.parse_args()

    json_path = Path(args.json_path).expanduser().resolve()
    if not json_path.exists():
        raise FileNotFoundError(f"No existe el archivo JSON: {json_path}")

    payload = read_json_file(json_path)
    if not isinstance(payload, list):
        raise ValueError("El JSON debe ser un array de objetos")

    Base.metadata.create_all(bind=engine)

    with SessionLocal() as session:
        result = upsert_groups_from_rows(session, payload, strict=args.strict)

    print(f"JSON procesado: {json_path}")
    print(f"Creados: {result['created']}, actualizados: {result['updated']}, omitidos: {result['skipped']}")
    for w in result["warnings"]:
        print(f"AVISO: {w}")
    for e in result["errors"]:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    main()
