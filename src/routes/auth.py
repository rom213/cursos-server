from flask import Blueprint, request, jsonify
from servises.auth.auth_service import AuthService

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/request-verification-code", methods=["POST"])
def request_verification_code():
    # Get email from config
    from flask import current_app
    email = current_app.config.get("ADMIN_EMAIL")
    
    try:
        AuthService.generate_verification_code(email)
        return jsonify({"status": "success", "message": ""}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
