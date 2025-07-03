from flask import Blueprint, request, jsonify, session
from servises.balance.balance_model import BalanceModel
from datetime import datetime

balance_bp = Blueprint("balance", __name__)

@balance_bp.route("/balance", methods=["GET"])
def all_categories():
    # Validar sesión de usuario
    # if "user" not in session:
    #     return jsonify({"success": False, "error": "No ha iniciado sesión"}), 401

    # user_google_id = session["user"]["google_id"]
    # Para pruebas locales, puedes usar este valor:
    user_google_id = "118070327157829661695"

    # Obtener fechas del query string
    date_init = request.args.get("date_init")
    date_end = request.args.get("date_end")

    # Validación de parámetros
    if not date_init or not date_end:
        return jsonify({"error": "Se requieren las fechas 'date_init' y 'date_end'."}), 400

    try:
        dt_init = datetime.fromisoformat(date_init)
        dt_end = datetime.fromisoformat(date_end)
    except ValueError:
        return jsonify({"error": "Fechas inválidas. Usa formato YYYY-MM-DD"}), 400

    try:
        # Llamada al modelo
        summary = BalanceModel.get_all_sales_by_me(
            google_id=user_google_id,
            date_init=dt_init,
            date_end=dt_end
        )


        # Access dictionary elements using key-value access
        return jsonify({
            "count": summary["counts"],
            "non_refunded_value": summary["non_refunded_value"],
            "refunded_value": summary["refunded_value"],
            "total_value": summary["total_value"]
        }), 200

    except Exception as e:
        return jsonify({"error": f"Error al obtener resumen: {str(e)}"}), 500