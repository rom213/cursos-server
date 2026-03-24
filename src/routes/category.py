from flask import Blueprint, request, jsonify, session
from servises.categories.category_model import CategoryModel
from models.Course import Course
from models.TiendaCourse import TiendaCourse
from spellchecker import SpellChecker
from sqlalchemy.orm import joinedload
from sqlalchemy import or_, and_, cast, Integer
from sqlalchemy.sql import func

try:
    spell = SpellChecker(language='es')
    
    # Añade aquí todas las palabras raras, plataformas o extranjerismos que no quieres que se "corrijan"
    custom_words = [
        'platzi', 'crehana', 'udemy', 'domestika', 'hotmart', 'coderhouse', 'edteam',
        'trading', 'marketing', 'cripto', 'criptomonedas', 'bitcoin', 'blockchain',
        'ecommerce', 'dropshipping', 'amazon', 'fba', 'seo', 'sem', 'copywriting',
        'python', 'javascript', 'react', 'vue', 'angular', 'excel', 'powerbi', 
        'masterclass', 'bootcamp', 'startup', 'software', 'backend', 'frontend'
    ]
    spell.word_frequency.load_words(custom_words)
    # Darle altísima prioridad a estas palabras del negocio
    # para que "plazi" se corrija a "platzi" y no a "plazo" (una palabra normal).
    for cw in custom_words:
        spell.word_frequency._dictionary[cw] = 10000000

except Exception:
    spell = None



category_bp = Blueprint("category", __name__)


@category_bp.route("/all-categories", methods=["GET"])
def all_categories():
    limit = request.args.get("limit", default=6, type=int)
    offset = request.args.get("offset", default=0, type=int)

    if limit is None or limit <= 0:
        limit = 6
    if offset is None or offset < 0:
        offset = 0

    categories = (
        CategoryModel.query
        .order_by(CategoryModel.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    data = [category.to_dict(light=True) for category in categories]
    return jsonify(data)

@category_bp.route("/<int:category_id>", methods=["GET"])
def get_category_by_id(category_id):
    category = CategoryModel.query.get(category_id)
    if not category:
        return jsonify({"message": "Category not found"}), 404
        
    return jsonify(category.to_dict(light=False))



@category_bp.route('/categories/deep-search', methods=['GET'])
def deep_search():
    search_term = request.args.get('q', '')
    if search_term:
        limit = request.args.get('limit', type=int) or 5
        
        words = search_term.split()
        conditions = []
        score_terms = []
        
        # Exact match bonus para el término entero
        score_terms.append(cast(func.lower(TiendaCourse.titulo) == search_term.lower(), Integer) * 50)
        score_terms.append(cast(func.lower(TiendaCourse.autor) == search_term.lower(), Integer) * 30)
        
        for word in words:
            # Corrección ortográfica
            corrected_word = spell.correction(word) if spell else word
            
            # Condición para la palabra original
            word_condition = or_(
                func.lower(TiendaCourse.titulo).ilike(f"%{word.lower()}%"),
                func.lower(TiendaCourse.autor).ilike(f"%{word.lower()}%"),
                func.lower(TiendaCourse.pack_nombre).ilike(f"%{word.lower()}%"),
                func.lower(TiendaCourse.keywords).ilike(f"%{word.lower()}%")
            )
            
            # Puntuación por la palabra original
            score_terms.append(cast(func.lower(TiendaCourse.titulo).ilike(f"%{word.lower()}%"), Integer) * 10)
            score_terms.append(cast(func.lower(TiendaCourse.autor).ilike(f"%{word.lower()}%"), Integer) * 8)
            score_terms.append(cast(func.lower(TiendaCourse.pack_nombre).ilike(f"%{word.lower()}%"), Integer) * 5)
            score_terms.append(cast(func.lower(TiendaCourse.keywords).ilike(f"%{word.lower()}%"), Integer) * 2)
            
            # Si el corrector sugirió algo diferente, ampliamos la búsqueda
            if corrected_word and corrected_word != word:
                word_condition = or_(
                    word_condition,
                    func.lower(TiendaCourse.titulo).ilike(f"%{corrected_word.lower()}%"),
                    func.lower(TiendaCourse.autor).ilike(f"%{corrected_word.lower()}%"),
                    func.lower(TiendaCourse.pack_nombre).ilike(f"%{corrected_word.lower()}%"),
                    func.lower(TiendaCourse.keywords).ilike(f"%{corrected_word.lower()}%")
                )
                # Puntuación menor para la palabra corregida
                score_terms.append(cast(func.lower(TiendaCourse.titulo).ilike(f"%{corrected_word.lower()}%"), Integer) * 8)
                score_terms.append(cast(func.lower(TiendaCourse.autor).ilike(f"%{corrected_word.lower()}%"), Integer) * 6)
                score_terms.append(cast(func.lower(TiendaCourse.pack_nombre).ilike(f"%{corrected_word.lower()}%"), Integer) * 4)
                score_terms.append(cast(func.lower(TiendaCourse.keywords).ilike(f"%{corrected_word.lower()}%"), Integer) * 1)
                
            conditions.append(word_condition)
        
        # Búsqueda combinada: todos los términos (originales o corregidos) deben coincidir
        query = TiendaCourse.query.filter(and_(*conditions)).distinct()

        # Ordenar resultados por relevancia (los más exactos primero)
        relevance_score = sum(score_terms)
        query = query.order_by(relevance_score.desc())

        query = query.limit(limit)
        courses = query.all()
        
        # Adaptar respuesta para el componente header.search.component.vue
        results = []
        for course in courses:
            # Buscar la imagen en la categoría usando el pilar_id
            categoria = None
            if course.pilar_id and course.pilar_id.isdigit():
                categoria = CategoryModel.query.get(int(course.pilar_id))
            
            imagen_url = categoria.imagen_url if categoria and getattr(categoria, 'imagen_url', None) else "https://cdn-icons-png.flaticon.com/512/3145/3145765.png"

            results.append({
                "id": course.pilar_id,
                "titulo": course.titulo,
                "imagen_url": imagen_url,
                "autor": course.autor,
                "pack_nombre": course.pack_nombre,
                "cantidad_cursos": course.pack_cantidad_cursos
            })
            
        return jsonify(results)
    
    return jsonify([])
    
    