from fastapi import APIRouter, Depends, HTTPException, Query

from servises.categories.category_model import CategoryModel
from servises.Users.user_model import UserModel
from models.TiendaCourse import TiendaCourse
from models.TiendaCourse import TiendaCourse
from spellchecker import SpellChecker
from sqlalchemy import Integer, cast, func, or_, and_
from sqlalchemy.orm import selectinload
from utils.auth import get_current_user_payload, get_token_payload_optional

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


def _build_filter_condition(filter_type: str | None):
    if filter_type == "temas":
        return or_(
            and_(CategoryModel.id >= 101, CategoryModel.id <= 107),
            and_(CategoryModel.id >= 201, CategoryModel.id <= 207),
            and_(CategoryModel.id >= 301, CategoryModel.id <= 309),
        )
    if filter_type == "pilares":
        return CategoryModel.id.in_([100, 200, 300])
    if filter_type == "combos":
        return CategoryModel.id.in_([100200, 100300, 200300])
    if filter_type == "toda-la-tienda":
        return CategoryModel.id == 100200300
    return None


@router.get("/my-courses")
def my_courses(
    payload: dict = Depends(get_current_user_payload),
):
    from models.Payment import Payment, PaymentStatus

    google_id = payload.get("google_id")
    uc = payload.get("country")
    user_bouth = UserModel.is_vendedor(google_id)

    category_ids = [
        p.category_id
        for p in Payment.query.filter(
            Payment.google_id == google_id,
            Payment.status == PaymentStatus.SUCCESS,
            Payment.category_id.isnot(None),
        ).all()
    ]

    if not category_ids:
        return []

    categories = (
        CategoryModel.query
        .options(selectinload(CategoryModel.related_categories))
        .filter(CategoryModel.id.in_(category_ids))
        .all()
    )

    return [
        c.to_dict(light=True, user_country=uc, viewer_google_id=google_id, esVendedor=user_bouth)
        for c in categories
    ]


@router.get("/all-categories")
def all_categories(
    limit: int = Query(6, ge=1),
    offset: int = Query(0, ge=0),
    filter_type: str | None = Query(None),
    payload: dict | None = Depends(get_token_payload_optional),
):
    viewer_gid = (payload or {}).get("google_id") if payload else None
    uc = (payload or {}).get("country") if payload else None

    user_bouth=UserModel.is_vendedor(viewer_gid)
    q = (
        CategoryModel.query
        .options(selectinload(CategoryModel.related_categories))
        .order_by(CategoryModel.id.desc())
    )
    condition = _build_filter_condition(filter_type)
    if condition is not None:
        q = q.filter(condition)
    categories = q.offset(offset).limit(limit).all()
    return [
        c.to_dict(light=True, user_country=uc, viewer_google_id=viewer_gid,esVendedor= user_bouth)
        for c in categories
    ]
    

@router.get("/{category_id}")
def get_category_by_id(
    category_id: int,
    payload: dict | None = Depends(get_token_payload_optional),
):
    uc = (payload or {}).get("country") if payload else None
    viewer_gid = (payload or {}).get("google_id") if payload else None
    user_bouth=UserModel.is_vendedor(viewer_gid)
    category = (
        CategoryModel.query
        .options(selectinload(CategoryModel.related_categories))
        .filter(CategoryModel.id == category_id)
        .first()
    )
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    return category.to_dict(light=False, user_country=uc, viewer_google_id=viewer_gid, esVendedor=user_bouth )


@router.get("/{category_id}/bloques")
def get_category_bloques(
    category_id: int,
    payload: dict | None = Depends(get_token_payload_optional),
):
    _PILAR_SET = {100, 200, 300}
    _TODA_ID = 100200300
    _COMBO_IDS = {100200, 100300, 200300}

    if category_id not in _PILAR_SET and category_id not in _COMBO_IDS and category_id != _TODA_ID:
        return []

    uc = (payload or {}).get("country") if payload else None
    viewer_gid = (payload or {}).get("google_id") if payload else None
    user_bouth = UserModel.is_vendedor(viewer_gid)

    if category_id in _PILAR_SET:
        pilar_cat = (
            CategoryModel.query
            .options(selectinload(CategoryModel.related_categories))
            .filter(CategoryModel.id == category_id)
            .first()
        )
        if not pilar_cat:
            raise HTTPException(status_code=404, detail="Category not found")

        tema_ids = [c.id for c in pilar_cat.related_categories]
        temas = CategoryModel.query.filter(CategoryModel.id.in_(tema_ids)).all()

        return [{
            "pilar": {"id": pilar_cat.id, "titulo": pilar_cat.titulo},
            "bloques": [
                t.to_dict(light=False, user_country=uc, viewer_google_id=viewer_gid, esVendedor=user_bouth)
                for t in sorted(temas, key=lambda x: x.id)
            ]
        }]

    combo_cat = (
        CategoryModel.query
        .options(selectinload(CategoryModel.related_categories))
        .filter(CategoryModel.id == category_id)
        .first()
    )
    if not combo_cat:
        raise HTTPException(status_code=404, detail="Category not found")

    pilar_ids = sorted([c.id for c in combo_cat.related_categories if c.id in _PILAR_SET])
    pilares = (
        CategoryModel.query
        .options(selectinload(CategoryModel.related_categories))
        .filter(CategoryModel.id.in_(pilar_ids))
        .all()
    )

    result = []
    for pilar in sorted(pilares, key=lambda x: x.id):
        tema_ids = [c.id for c in pilar.related_categories]
        temas = CategoryModel.query.filter(CategoryModel.id.in_(tema_ids)).all()
        result.append({
            "pilar": {"id": pilar.id, "titulo": pilar.titulo},
            "bloques": [
                t.to_dict(light=False, user_country=uc, viewer_google_id=viewer_gid, esVendedor=user_bouth)
                for t in sorted(temas, key=lambda x: x.id)
            ]
        })

    return result



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
