from flask import Blueprint, request, jsonify, session, send_from_directory
from datetime import datetime
from servises.refund import refund_model
from servises.sail.sail_model import ReferQueryService
from models.account import AccountType
import os

# Blueprint para refund
sail_bp = Blueprint("sail", __name__)


def serialize_refer(refer):
        return {
            "porcetage_refund":refer.porcentage,
            "affiliaty": "manual",
            "category_bought": refer.payment.category.titulo,
            "category_price": refer.payment.price,
            "refund_price": refer.value,
            "created_at": refer.created_at,
            "is_refund": refer.refund_id is not None,
            "refer_id": refer.id,
            "baucher_image": refer.refund.image
        }



# Endpoint: Obtener refunds por usuario y fechas
@sail_bp.route("/sails", methods=["GET"])
def get_refunds_by_user_and_date():
    date_init = request.args.get("date_init")
    date_end = request.args.get("date_end")


    # if "user" not in session:
    #     return jsonify({"success": False, "error": "No ha iniciado sesión"}), 401

    # user_google_id = session["user"]["google_id"]
    user_google_id = 118070327157829661695

    if not all([date_init, date_end]):
        return jsonify({"error": "Faltan parámetros requeridos"}), 400

    try:
        dt_init = datetime.fromisoformat(date_init)
        dt_end = datetime.fromisoformat(date_end)
    except ValueError:
        return jsonify({"error": "Fechas inválidas. Usa formato YYYY-MM-DD"}), 400

    results = ReferQueryService.get_by_user_and_date(user_google_id, dt_init, dt_end)
    return jsonify([serialize_refer(ref) for ref in results]), 200