from flask import Blueprint, request, jsonify
from config import config
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from models.User import User, db
from abc import ABC, abstractmethod
import hashlib


# 1. Repository Pattern -----------------------------------------------------------------
class UserRepository:
    @staticmethod
    def get_by_google_id(google_id: str) -> User:
        return User.query.filter_by(google_id=google_id).first()

    @staticmethod
    def create_google_user(user_data: dict) -> User:
        new_user = User(
            google_id=user_data["user_id"],
            email=user_data["email"],
            name=user_data["name"],
            picture=user_data["picture"]
        )
        db.session.add(new_user)
        db.session.commit()
        return new_user

# 2. Strategy Pattern (Para diferentes proveedores de autenticación) --------------------
class TokenVerifier(ABC):
    @abstractmethod
    def verify(self, token: str) -> dict:
        pass

class GoogleTokenVerifier(TokenVerifier):
    def __init__(self, client_id: str):
        self.client_id = client_id

    def verify(self, token: str) -> dict:
        try:
            idinfo = id_token.verify_oauth2_token(
                token, 
                google_requests.Request(), 
                self.client_id
            )
            return {
                "user_id": idinfo.get("sub"),
                "email": idinfo.get("email"),
                "name": idinfo.get("name", "Usuario"),
                "picture": idinfo.get("picture"),
                "given_name": idinfo.get("given_name"),
                "family_name": idinfo.get("family_name")
            }
        except Exception as e:
            raise ValueError(f"Invalid token: {str(e)}")

# 3. Service Layer ----------------------------------------------------------------------
class AuthService:
    def __init__(self, token_verifier: TokenVerifier, user_repository: UserRepository):
        self.token_verifier = token_verifier
        self.user_repository = user_repository

    def authenticate(self, token: str) -> tuple:
        try:
            # Verificar token
            user_data = self.token_verifier.verify(token)
            
            # Buscar o crear usuario
            user = self.user_repository.get_by_google_id(user_data["user_id"])
            is_new_user = False
            
            if not user:
                user = self.user_repository.create_google_user(user_data)
                is_new_user = True

            return {
                "user_data": user_data,
                "is_new_user": is_new_user
            }, True
            
        except Exception as e:
            return {"error": str(e)}, False

# Configuración y blueprint -------------------------------------------------------------
GOOGLE_CLIENT_ID = "150428135378-7p5fkl7douv1sj3kd0tofav3kneks7lv.apps.googleusercontent.com"

# Inyección de dependencias
user_repository = UserRepository()
google_verifier = GoogleTokenVerifier(GOOGLE_CLIENT_ID)
auth_service = AuthService(google_verifier, user_repository)



users_bp = Blueprint("users", __name__)

@users_bp.route("/verify-token", methods=["POST"])
def verify_token():
    token = request.json.get("token")
    
    if not token:
        return jsonify({"success": False, "error": "Token missing"}), 400
    
    result, success = auth_service.authenticate(token)
    
    if not success:
        return jsonify({"success": False, "error": result["error"]}), 401
    
    return jsonify({
        "success": True,
        "user": {
            **result["user_data"],
            "register": result["is_new_user"]
        }
    })


API_KEY = "WTwXvH9RHxXSOaap990f76ti6o" 


@users_bp.route("/payu-confirmation", methods=["POST"])
def payu_confirmation():
    try:
        data = request.form.to_dict()
        
        # Extraer los parámetros necesarios para la firma
        merchant_id = data.get("merchant_id")
        reference_sale = data.get("reference_sale")
        value = data.get("value")
        currency = data.get("currency")
        state_pol = data.get("state_pol")
        received_sign = data.get("sign")

        print(request.form.to_dict())
        
        if not all([merchant_id, reference_sale, value, currency, state_pol, received_sign]):
            return jsonify({"error": "Missing parameters"}), 400
        
        # Formatear el valor adecuadamente
        value = float(value)
        formatted_value = f"{value:.1f}" if value % 1 == 0 else f"{value:.2f}"
        
        # Generar la firma local
        signature_string = f"{API_KEY}~{merchant_id}~{reference_sale}~{formatted_value}~{currency}~{state_pol}"
        generated_sign = hashlib.md5(signature_string.encode()).hexdigest()
        
        # Verificar la firma
        if received_sign != generated_sign:
            return jsonify({"error": "Invalid signature"}), 403
        
        # Aquí puedes procesar la transacción en tu base de datos
        # Ejemplo: actualizar órdenes, inventarios, etc.
        transaction_status = "approved" if state_pol == "4" else "rejected"
        
        return jsonify({"message": "Confirmation received", "transaction_status": transaction_status}), 200
    except:
        print("hola hubo un error")
        return jsonify({"message": "Confirmation received", "transaction_status": "error"}), 200

