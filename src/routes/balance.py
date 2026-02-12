from flask import Blueprint, request, jsonify, session
from servises.balance.balance_model import BalanceModel
from datetime import datetime
from datetime import timedelta

balance_bp = Blueprint("balance", __name__)



@balance_bp.route("/balance", methods=["GET"])
def all_balance_categories():
    date_init_str = request.args.get("date_init")
    date_end_str = request.args.get("date_end")
    

    date_init = datetime.strptime(date_init_str, "%Y-%m-%d")
    date_end = datetime.strptime(date_end_str, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)
    
    if "user" not in session:
        return jsonify({"success": False, "error": "No ha iniciado sesión"}), 401

    user_google_id = session["user"]["google_id"]

    if not date_init or not date_end:
        return jsonify({"status": "ERROR", "message": "Se requieren las fechas 'date_init' y 'date_end'.", "records": []}), 200


    try:
        summary = BalanceModel.get_all_sales_by_me(
            google_id=user_google_id,
            date_init=date_init,
            date_end=date_end
        )
        
        return jsonify({
            "count": summary["counts"],
            "non_refunded_value": summary["non_refunded_value"],
            "refunded_value": summary["refunded_value"],
            "total_value_all_refunds": summary["total_value"],
            "courses_payments_value": summary["courses_payments_value"],
            "list_ids_refers": summary["list_ids_refers"]
        }), 200

    except Exception as e:
        return jsonify({"status": "ERROR", "message": "KO", "records": []}), 200

@balance_bp.route("/balance/user/<google_id>", methods=["GET"])
def all_balance_categories_by_google_id(google_id):
    date_init_str = request.args.get("date_init")
    date_end_str = request.args.get("date_end")
    

    date_init = datetime.strptime(date_init_str, "%Y-%m-%d")
    date_end = datetime.strptime(date_end_str, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)

    if not date_init or not date_end:
        return jsonify({"status": "ERROR", "message": "Se requieren las fechas 'date_init' y 'date_end'.", "records": []}), 200


    try:
        summary = BalanceModel.get_all_sales_by_me(
            google_id=google_id,
            date_init=date_init,
            date_end=date_end
        )
        return jsonify({"status": "success", "message": "OK", "records": [{
            "count": summary["counts"],
            "non_refunded_value": summary["non_refunded_value"],
            "refunded_value": summary["refunded_value"],
            "total_value_all_refunds": summary["total_value"],
            "courses_payments_value": summary["courses_payments_value"],
            "list_ids_refers": summary["list_ids_refers"]
        }]}), 200

    except Exception as e:
        return jsonify({"status": "ERROR", "message": "KO", "records": []}), 200


@balance_bp.route("/balance/all", methods=["GET"])
def balance_categories():
    date_init_str = request.args.get("date_init")
    date_end_str = request.args.get("date_end")
    

    date_init = datetime.strptime(date_init_str, "%Y-%m-%d")
    date_end = datetime.strptime(date_end_str, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)

    if not date_init or not date_end:
        return jsonify({"status": "ERROR", "message": "Se requieren las fechas 'date_init' y 'date_end'.", "records": []}), 200


    try:
        summary = BalanceModel.get_all_sales(
            date_init=date_init,
            date_end=date_end
        )
        return jsonify({"status": "success", "message": "OK", "records": [{
            "count": summary["counts"],
            "non_refunded_value": summary["non_refunded_value"],
            "refunded_value": summary["refunded_value"],
            "total_value_all_refunds": summary["total_value"],
            "courses_payments_value": summary["courses_payments_value"]
        }]}), 200

    except Exception as e:
        return jsonify({"status": "ERROR", "message": "KO", "records": []}), 200