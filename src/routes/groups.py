from flask import Blueprint, request, jsonify
from servises.groups.repository import GroupRepository
from servises.request.validate_data import ValidateData
from servises.categories.category_model import CategoryModel
from servises.groups.group_model import GroupModel

group_bp = Blueprint("groups", __name__)


@group_bp.route("/create-group", methods=["POST"])
def create_group():
    required_fields = ["group_email", "group_name", "group_description"]
    data, error = ValidateData.validate_request_data(required_fields=required_fields)

    if error:
        return error

    group_repo = GroupRepository(
        group_email=data["group_email"],
        group_name=data["group_name"],
        group_description=data["group_description"]
    )

    result = group_repo.crear_grupo()
    if result:
        return jsonify(result), 201
    return jsonify({"error": "Error al crear el grupo"}), 400



@group_bp.route("/add-member", methods=["POST"])
@group_bp.route("/add-member-time", methods=["POST"])
def add_member():
    action = "agregar_miembro_grupo_time" if request.path.endswith("time") else "agregar_miembro_grupo"
    
    required_fields = ["member_email", "category_id", "reference_code"]
    data, error = ValidateData.validate_request_data(required_fields=required_fields)
    if error:
        return error
    
    return GroupRepository.process_member_addition(action, data=data)


@group_bp.route("/remove-member", methods=["DELETE"])
def remove_member():
    required_fields = ["group_email", "member_email"]
    data, error = ValidateData.validate_request_data(required_fields=required_fields)
    if error:
        return error

    group_repo = GroupRepository(
        group_email=data["group_email"],
        member_email=data["member_email"]
    )
    result = group_repo.eliminar_miembro_grupo()
    if result:
        return jsonify({
            "message": f"Miembro {data['member_email']} eliminado del grupo {data['group_email']}"
        }), 200
    return jsonify({"error": "Error al eliminar el miembro del grupo"}), 400
