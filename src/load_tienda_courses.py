import json
from pathlib import Path

import models  # noqa: F401 — registra todos los modelos en Base.metadata
from database import Base, engine, SessionLocal
from models.TiendaCourse import TiendaCourse

DEFAULT_JSON_PATH = (
    Path(__file__).resolve().parents[2]
    / "documentacion_tecnica"
    / "tienda_pinecone_metadata.json"
)

def load_data():
    json_path = DEFAULT_JSON_PATH
    print(f"Cargando datos desde {json_path}...")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("Creando la tabla si no existe...")
    Base.metadata.create_all(bind=engine)

    print(f"Insertando {len(data)} registros...")
    inserted = 0

    with SessionLocal() as session:
        for item in data:
            course = TiendaCourse(
                titulo=item.get("titulo"),
                autor=item.get("autor"),
                url_curso=item.get("url_curso"),
                pack_id=item.get("pack_id"),
                pack_nombre=item.get("pack_nombre"),
                pack_cantidad_cursos=item.get("pack_cantidad_cursos"),
                pilar_id=item.get("pilar_id"),
                keywords=item.get("keywords")
            )
            session.add(course)
            inserted += 1

            if inserted % 2000 == 0:
                session.commit()
                print(f"Insertados {inserted} registros...")

        session.commit()

    print(f"Operacion completada. Total de registros insertados: {inserted}.")

if __name__ == "__main__":
    load_data()
