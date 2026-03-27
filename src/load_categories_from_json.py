import argparse
import json
import re
from pathlib import Path

from json_repair import repair_json
from sqlalchemy import inspect, text

import models  # noqa: F401 — registra todos los modelos en Base.metadata
from database import Base, engine, SessionLocal
from models.Category import Category, category_relations


# Caracteres de control inválidos en strings JSON (excluye tab \t=0x09, newline \n=0x0a, cr \r=0x0d)
CONTROL_CHAR_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
# Backslash seguido de carácter no válido (JSON solo permite \ " / b f n r t u)
INVALID_ESCAPE_PATTERN = re.compile(r'\\(?!["\\/bfnrt]|u[0-9a-fA-F]{4})')


DEFAULT_JSON_PATH = (
    Path(__file__).resolve().parents[2]
    / "documentacion_tecnica"
    / "estructurasimple_final (3) (2).json"
)


def to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


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
    # Si falla: sanitizar y/o reparar
    raw = CONTROL_CHAR_PATTERN.sub(" ", raw)
    raw = INVALID_ESCAPE_PATTERN.sub(r"\\\\", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return json.loads(repair_json(raw))


def flatten_subfolders(payload):
    """Extrae recursivamente todas las categorías con 'id' desde cualquier nivel de subcarpetas."""
    categories = []
    if not isinstance(payload, list):
        return categories

    for block in payload:
        if not isinstance(block, dict):
            continue
        # Si tiene id, es una categoría terminal
        if "id" in block:
            categories.append(block)
        # Recorrer subcarpetas en cualquier nivel
        subcarpetas = block.get("subcarpetas", [])
        if isinstance(subcarpetas, list):
            categories.extend(flatten_subfolders(subcarpetas))

    return categories


def ensure_category_schema(session):
    inspector = inspect(engine)
    existing_columns = {column["name"] for column in inspector.get_columns("category")}

    required_json_columns = [
        "pregunta_respuesta",
        "seccion_plataformas",
        "seccion_temas",
        "seccion_lista_completa",
    ]

    for column_name in required_json_columns:
        if column_name not in existing_columns:
            session.execute(
                text(f"ALTER TABLE category ADD COLUMN {column_name} JSON NULL")
            )

    session.commit()


def replace_categories(session, category_rows):
    session.execute(category_relations.delete())
    session.query(Category).delete(synchronize_session=False)

    categories_by_id = {}
    pending_relations = {}
    skipped_without_id = 0

    for row in category_rows:
        category_id = to_int(row.get("id"))
        if category_id is None:
            skipped_without_id += 1
            continue

        contenido = {}
        if row.get("beneficios"):
            contenido["beneficios"] = row["beneficios"]
        if row.get("frase_3"):
            contenido["frase_3"] = row["frase_3"]

        category = Category(
            id=category_id,
            titulo=row.get("titulo"),
            url=row.get("url"),
            frase_1=row.get("frase_1"),
            frase_2=row.get("frase_2"),
            imagen_url=row.get("imagen_url"),
            num_per=str(row.get("num_per")) if row.get("num_per") is not None else None,
            descuento=str(row.get("descuento")) if row.get("descuento") is not None else "0",
            precio=to_int(row.get("precio")),
            duracion=row.get("duracion"),
            contenido=contenido or {},
            pregunta_respuesta=row.get("pregunta_respuesta", []),
            seccion_plataformas=row.get("seccion_plataformas", {}),
            seccion_temas=row.get("seccion_temas", {}),
            seccion_lista_completa=row.get("seccion_lista_completa", {}),
        )

        session.add(category)
        categories_by_id[category_id] = category
        pending_relations[category_id] = row.get("cat_rel", [])

    session.flush()

    relation_links = 0
    missing_relation_refs = []

    for category_id, raw_rel_ids in pending_relations.items():
        if not isinstance(raw_rel_ids, list):
            continue

        source = categories_by_id.get(category_id)
        if source is None:
            continue

        for raw_rel_id in raw_rel_ids:
            related_id = to_int(raw_rel_id)
            if related_id is None:
                continue

            target = categories_by_id.get(related_id)
            if target is None:
                missing_relation_refs.append((category_id, related_id))
                continue

            if target not in source.related_categories:
                source.related_categories.append(target)
                relation_links += 1

    session.commit()
    return {
        "created_categories": len(categories_by_id),
        "relation_links": relation_links,
        "missing_relation_refs": missing_relation_refs,
        "skipped_without_id": skipped_without_id,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Carga categorías desde JSON y reconstruye relaciones cat_rel."
    )
    parser.add_argument(
        "--json",
        dest="json_path",
        default=str(DEFAULT_JSON_PATH),
        help="Ruta del archivo JSON fuente.",
    )
    args = parser.parse_args()

    json_path = Path(args.json_path).expanduser().resolve()
    if not json_path.exists():
        raise FileNotFoundError(f"No existe el archivo JSON: {json_path}")

    payload = read_json_file(json_path)
    category_rows = flatten_subfolders(payload)

    Base.metadata.create_all(bind=engine)

    with SessionLocal() as session:
        ensure_category_schema(session)
        result = replace_categories(session, category_rows)

    print(f"JSON procesado: {json_path}")
    print(f"Categorias creadas: {result['created_categories']}")
    print(f"Relaciones creadas: {result['relation_links']}")
    print(f"Registros omitidos sin id: {result['skipped_without_id']}")
    print(f"Referencias cat_rel no encontradas: {len(result['missing_relation_refs'])}")

    if result["missing_relation_refs"]:
        sample = result["missing_relation_refs"][:20]
        print("Muestra de referencias faltantes (origen -> destino):")
        for origin_id, target_id in sample:
            print(f"- {origin_id} -> {target_id}")


if __name__ == "__main__":
    main()
