from flask import Blueprint, request, jsonify, session, send_from_directory
from datetime import datetime
from servises.refund import refund_model
from models.account import AccountType
import os

# Blueprint para refund
refund_bp = Blueprint("refund", __name__)


def serialize_refer(refer):
        return {
            "refund_id": refer.refund.id,
            "type_acc_em": refer.refund.type_acc_em.value,
            "porcetage_refund":refer.porcentage,
            "titular_acc_em": refer.refund.titular_acc_em,
            "number_acc_em": refer.refund.number_acc_em,
            "type_acc_re": refer.refund.type_acc_re.value,
            "titular_acc_res": refer.refund.titular_acc_em,
            "number_acc_res": refer.refund.number_acc_em,
            "value": refer.value,
            "image": refer.refund.image,
            "created_at": refer.refund.created_at.isoformat(),
            "refer_id": refer.id,
            "google_id": refer.google_id,
            "code_reference": refer.refund.code_reference
        }



# Endpoint: Obtener refunds por usuario y fechas
@refund_bp.route("/refunds", methods=["GET"])
def get_refunds_by_user_and_date():
    date_init = request.args.get("date_init")
    date_end = request.args.get("date_end")


    if "user" not in session:
        return jsonify({"success": False, "error": "No ha iniciado sesión"}), 401

    user_google_id = session["user"]["google_id"]

    if not all([date_init, date_end]):
        return jsonify({"error": "Faltan parámetros requeridos"}), 400

    try:
        dt_init = datetime.fromisoformat(date_init)
        dt_end = datetime.fromisoformat(date_end)
    except ValueError:
        return jsonify({"error": "Fechas inválidas. Usa formato YYYY-MM-DD"}), 400

    results = refund_model.RefundQueryService.get_by_user_and_date(user_google_id, dt_init, dt_end)
    print(results)
    return jsonify([serialize_refer(ref) for ref in results]), 200




# Endpoint: Crear un nuevo refund
@refund_bp.route("/refunds", methods=["POST"])
def create_refund():
    form = request.form
    image_file = request.files.get("image")

    # Validación de campos requeridos
    required_fields = [
        "type_acc_em", "type_acc_re", "titular_acc_em", "titular_acc_res",
        "number_acc_em", "value"
    ]
    
    missing = [f for f in required_fields if f not in form]
    if missing or not image_file:
        return jsonify({"error": f"Faltan campos: {missing} o imagen"}), 400

    # Guardar imagen
    try:
        validator = refund_model.PILImageValidator()
        image_service = refund_model.ImageStorageService(image_file, validator)
        image_path = image_service.save()
    except Exception as e:
        return jsonify({"error": f"Error al guardar imagen: {str(e)}"}), 400

    # Crear refund
    refund_data = {
        "type_acc_em": AccountType[form["type_acc_em"]],
        "type_acc_re": AccountType[form["type_acc_re"]],
        "titular_acc_em": form["titular_acc_em"],
        "titular_acc_res": form["titular_acc_res"],
        "number_acc_em": form["number_acc_em"],
        "value": form["value"],
        "image": image_path
    }

    refund_creator = refund_model.RefundCreator(refund_model.RefundRepository())
    refund = refund_creator.create_refund(refund_data)

    return jsonify({
        "id": refund.id,
        "created_at": refund.created_at.isoformat(),
        "image": refund.image
    }), 201



UPLOAD_DIRECTORY = os.path.join(os.getcwd(), "uploads")

@refund_bp.route('/uploads/<path:filename>')
def serve_uploaded_image(filename):
    """
    Esta ruta sirve los archivos desde el directorio UPLOAD_DIRECTORY.
    El navegador podrá acceder a las imágenes usando una URL como:
    http://127.0.0.1:5000/uploads/nombre_del_archivo.jpg
    """
    return send_from_directory(UPLOAD_DIRECTORY, filename)