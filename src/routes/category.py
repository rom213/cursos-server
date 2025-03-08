from flask import Blueprint, request, jsonify, session
from servises.categories.category_model import CategoryModel
from models.Course import Course


category_bp = Blueprint("category", __name__)


@category_bp.route("/all-categories", methods=["GET"])
def all_categories():
    categories = CategoryModel.get_all()
    data = [category.to_dict() for category in categories]
    return data
    
    