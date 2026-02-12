from flask import Blueprint, request, jsonify, session, send_from_directory
from datetime import datetime
from servises.refund import refund_model


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
    
    
    return jsonify([serialize_refer(ref) for ref in results]), 200




