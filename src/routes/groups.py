from flask import Blueprint, request, jsonify
from servises.groups.repository import GroupRepository
from servises.request.validate_data import ValidateData


group_bp = Blueprint("groups", __name__)

def parse_data(dat, reference_sale):
    items = dat.strip('|').split('|')  # Eliminar '|' inicial y final, luego dividir por '|'
    parsed_items = []

    for item in items:
        parts = item.split(',')
        obj = {
            "category_id": int(parts[0]),  # Convertir el primer valor a entero
            "google_id": parts[1] if len(parts) > 1 else None,  # Verificar si hay datos
            "google_id_refer": parts[2] if len(parts) > 2 else None,
            "reference_code": reference_sale
        }
        parsed_items.append(obj)

    return parsed_items

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
    
    required_fields = ["extra1"]
    data, error = ValidateData.validate_request_data(required_fields=required_fields)
    if error:
        return error

    response = jsonify({"error": "No se proporcionaron datos"}), 200

    cart_data = parse_data(data.get("extra1"), "kkkkkkkkkkkk")

    print(cart_data) 

    if isinstance(cart_data, list):
        for item in cart_data:
            #print(item.get("category_id"))
            response = GroupRepository.process_member_addition("agregar_miembro_grupo", data=item)
            
    return response


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
