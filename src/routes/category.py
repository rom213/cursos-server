from fastapi import APIRouter, Depends, HTTPException, Query

from servises.categories.category_model import CategoryModel
from models.TiendaCourse import TiendaCourse
from spellchecker import SpellChecker
from sqlalchemy import Integer, cast, func, or_, and_
from utils.auth import get_token_payload_optional

try:
    spell = SpellChecker(language="es")
    custom_words = [
        "platzi", "crehana", "udemy", "domestika", "hotmart", "coderhouse", "edteam",
        "trading", "marketing", "cripto", "criptomonedas", "bitcoin", "blockchain",
        "ecommerce", "dropshipping", "amazon", "fba", "seo", "sem", "copywriting",
        "python", "javascript", "react", "vue", "angular", "excel", "powerbi",
        "masterclass", "bootcamp", "startup", "software", "backend", "frontend",
    ]
    spell.word_frequency.load_words(custom_words)
    for cw in custom_words:
        spell.word_frequency._dictionary[cw] = 10000000
except Exception:
    spell = None


router = APIRouter(tags=["category"])


@router.get("/all-categories")
def all_categories(
    limit: int = Query(6, ge=1),
    offset: int = Query(0, ge=0),
    payload: dict | None = Depends(get_token_payload_optional),
):
    viewer_gid = (payload or {}).get("google_id") if payload else None
    uc = (payload or {}).get("country") if payload else None

    categories = (
        CategoryModel.query.order_by(CategoryModel.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        c.to_dict(light=True, user_country=uc, viewer_google_id=viewer_gid)
        for c in categories
    ]


@router.get("/{category_id}")
def get_category_by_id(
    category_id: int,
    payload: dict | None = Depends(get_token_payload_optional),
):
    uc = (payload or {}).get("country") if payload else None
    viewer_gid = (payload or {}).get("google_id") if payload else None

    category = CategoryModel.query.get(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    return category.to_dict(light=False, user_country=uc, viewer_google_id=viewer_gid)


@router.get("/categories/deep-search")
def deep_search(
    q: str = "",
    limit: int | None = 5,
    payload: dict | None = Depends(get_token_payload_optional),
):
    _ = payload
    if not q:
        return []

    limit = limit or 5
    search_term = q
    words = search_term.split()
    conditions = []
    score_terms = []

    score_terms.append(cast(func.lower(TiendaCourse.titulo) == search_term.lower(), Integer) * 50)
    score_terms.append(cast(func.lower(TiendaCourse.autor) == search_term.lower(), Integer) * 30)

    for word in words:
        corrected_word = spell.correction(word) if spell else word

        word_condition = or_(
            func.lower(TiendaCourse.titulo).ilike(f"%{word.lower()}%"),
            func.lower(TiendaCourse.autor).ilike(f"%{word.lower()}%"),
            func.lower(TiendaCourse.pack_nombre).ilike(f"%{word.lower()}%"),
            func.lower(TiendaCourse.keywords).ilike(f"%{word.lower()}%"),
        )

        score_terms.append(cast(func.lower(TiendaCourse.titulo).ilike(f"%{word.lower()}%"), Integer) * 10)
        score_terms.append(cast(func.lower(TiendaCourse.autor).ilike(f"%{word.lower()}%"), Integer) * 8)
        score_terms.append(cast(func.lower(TiendaCourse.pack_nombre).ilike(f"%{word.lower()}%"), Integer) * 5)
        score_terms.append(cast(func.lower(TiendaCourse.keywords).ilike(f"%{word.lower()}%"), Integer) * 2)

        if corrected_word and corrected_word != word:
            word_condition = or_(
                word_condition,
                func.lower(TiendaCourse.titulo).ilike(f"%{corrected_word.lower()}%"),
                func.lower(TiendaCourse.autor).ilike(f"%{corrected_word.lower()}%"),
                func.lower(TiendaCourse.pack_nombre).ilike(f"%{corrected_word.lower()}%"),
                func.lower(TiendaCourse.keywords).ilike(f"%{corrected_word.lower()}%"),
            )
            score_terms.append(cast(func.lower(TiendaCourse.titulo).ilike(f"%{corrected_word.lower()}%"), Integer) * 8)
            score_terms.append(cast(func.lower(TiendaCourse.autor).ilike(f"%{corrected_word.lower()}%"), Integer) * 6)
            score_terms.append(cast(func.lower(TiendaCourse.pack_nombre).ilike(f"%{corrected_word.lower()}%"), Integer) * 4)
            score_terms.append(cast(func.lower(TiendaCourse.keywords).ilike(f"%{corrected_word.lower()}%"), Integer) * 1)

        conditions.append(word_condition)

    query = TiendaCourse.query.filter(and_(*conditions)).distinct()

    relevance_score = sum(score_terms)
    query = query.order_by(relevance_score.desc()).limit(limit)
    courses = query.all()

    results = []
    for course in courses:
        categoria = None
        if course.pilar_id and str(course.pilar_id).isdigit():
            categoria = CategoryModel.query.get(int(course.pilar_id))

        imagen_url = (
            categoria.imagen_url
            if categoria and getattr(categoria, "imagen_url", None)
            else "https://cdn-icons-png.flaticon.com/512/3145/3145765.png"
        )

        results.append(
            {
                "id": course.pilar_id,
                "titulo": course.titulo,
                "imagen_url": imagen_url,
                "autor": course.autor,
                "pack_nombre": course.pack_nombre,
                "cantidad_cursos": course.pack_cantidad_cursos,
            }
        )

    return results
