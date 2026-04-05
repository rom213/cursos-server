#!/usr/bin/env python3
"""
Script para cargar imágenes de categorías desde imagenespinteres.json
Actualiza el campo imagen_url en el modelo Category
"""

import json
import os
import sys
from pathlib import Path

# Agregar el directorio padre al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent))

from database import SessionLocal
from models.Category import Category

def load_imagenes_from_json(json_path: str) -> dict:
    """Lee el JSON de imágenes y retorna un diccionario con id -> imagen_url"""
    print(f"📂 Leyendo JSON: {json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    imagenes_map = {}

    # Procesar categorías principales
    if 'categorias' in data:
        for categoria in data['categorias']:
            categoria_id = categoria.get('id')
            imagen_url = categoria.get('imagen_url')

            if categoria_id and imagen_url:
                imagenes_map[categoria_id] = imagen_url
                print(f"  ✓ Categoría {categoria_id}: {imagen_url}")

            # Procesar módulos (sub-categorías)
            if 'modulos' in categoria:
                for modulo in categoria['modulos']:
                    modulo_id = modulo.get('id')
                    modulo_imagen = modulo.get('imagen_url')

                    if modulo_id and modulo_imagen:
                        imagenes_map[modulo_id] = modulo_imagen
                        print(f"  ✓ Módulo {modulo_id}: {modulo_imagen}")

    # Procesar combos y membresías
    if 'combos_y_membresias' in data:
        for combo in data['combos_y_membresias']:
            combo_id = combo.get('id')
            combo_imagen = combo.get('imagen_url')

            if combo_id and combo_imagen:
                imagenes_map[combo_id] = combo_imagen
                print(f"  ✓ Combo {combo_id}: {combo_imagen}")

    return imagenes_map

def update_category_images(imagenes_map: dict) -> None:
    """Actualiza las imágenes en la base de datos"""
    session = SessionLocal()

    try:
        total_updated = 0
        total_not_found = 0

        for categoria_id, imagen_url in imagenes_map.items():
            # Buscar la categoría en la BD
            category = session.query(Category).filter_by(id=categoria_id).first()

            if category:
                old_image = category.imagen_url
                category.imagen_url = imagen_url
                session.commit()

                if old_image != imagen_url:
                    print(f"  ✅ Actualizado ID {categoria_id}")
                    total_updated += 1
                else:
                    print(f"  ℹ️  ID {categoria_id} ya tenía esa imagen")
            else:
                print(f"  ⚠️  Categoría con ID {categoria_id} no encontrada en BD")
                total_not_found += 1

        print(f"\n📊 Resumen:")
        print(f"  ✅ Actualizadas: {total_updated}")
        print(f"  ⚠️  No encontradas: {total_not_found}")
        print(f"  📝 Total procesadas: {len(imagenes_map)}")

    except Exception as e:
        print(f"❌ Error al actualizar imágenes: {e}")
        session.rollback()
    finally:
        session.close()

def main():
    """Función principal del script"""
    print("🚀 Iniciando carga de imágenes de categorías...\n")

    # Construir la ruta al JSON
    current_dir = Path(__file__).parent
    json_path = current_dir.parent.parent / "documentacion_tecnica" / "imagenespinteres.json"

    if not json_path.exists():
        print(f"❌ No se encontró el archivo: {json_path}")
        sys.exit(1)

    # Cargar imágenes del JSON
    imagenes_map = load_imagenes_from_json(str(json_path))

    if not imagenes_map:
        print("❌ No se encontraron imágenes en el JSON")
        sys.exit(1)

    print(f"\n📦 Total de imágenes encontradas: {len(imagenes_map)}\n")

    # Actualizar en la base de datos
    print("💾 Actualizando base de datos...\n")
    update_category_images(imagenes_map)

    print("\n✨ ¡Proceso completado!")

if __name__ == "__main__":
    main()
