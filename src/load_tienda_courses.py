import json
from app import app
from models import db
from models.TiendaCourse import TiendaCourse

def load_data():
    json_path = r"C:\Users\ASUS\Documents\Romario\work\cursos estudia y trabaja\documentacion_tecnica\tienda_pinecone_metadata.json"
    print(f"Cargando datos desde {json_path}...")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    with app.app_context():
        print("Creando la tabla si no existe...")
        db.create_all()
        
        print(f"Insertando {len(data)} registros...")
        inserted = 0
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
            db.session.add(course)
            inserted += 1
            
            if inserted % 2000 == 0:
                db.session.commit()
                print(f"Insertados {inserted} registros...")
                
        db.session.commit()
        print(f"Operacion completada. Total de registros insertados: {inserted}.")

if __name__ == "__main__":
    load_data()
