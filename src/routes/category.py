from flask import Blueprint, request, jsonify, session
from servises.categories.category_model import CategoryModel
from models.Course import Course
from sqlalchemy.orm import joinedload
from sqlalchemy import or_
from sqlalchemy.sql import func



category_bp = Blueprint("category", __name__)


@category_bp.route("/all-categories", methods=["GET"])
def all_categories():
    categories = CategoryModel.get_all()
    data = [category.to_dict() for category in categories]
    return data





@category_bp.route('/categories/deep-search', methods=['GET'])
def deep_search():
    search_term = request.args.get('q', '')
    limit = request.args.get('limit', type=int)

    # Filtro SQL directamente con ilike
    query = CategoryModel.query \
        .outerjoin(Course) \
        .filter(
            or_(
                func.lower(CategoryModel.titulo).ilike(f"%{search_term.lower()}%"),
                func.lower(Course.name).ilike(f"%{search_term.lower()}%"),
                func.lower(Course.autor).ilike(f"%{search_term.lower()}%")
            )
        ) \
        .options(joinedload(CategoryModel.courses)) \
        .distinct()

    if limit:
        query = query.limit(limit)
    
    categories = query.all()
    return jsonify([cat.to_dict() for cat in categories])
    
    