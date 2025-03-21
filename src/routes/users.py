from flask import Blueprint, request, jsonify, session
from config import config
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from models.User import User, db
from abc import ABC, abstractmethod
from servises.Users.user_model import UserModel


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
            
            print(user_data)
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
GOOGLE_CLIENT_ID = "150428135378-em2lm6k41hkremer0nn5rkhj916oseoi.apps.googleusercontent.com"

# Inyección de dependencias
user_repository = UserRepository()
google_verifier = GoogleTokenVerifier(GOOGLE_CLIENT_ID)
auth_service = AuthService(google_verifier, user_repository)



users_bp = Blueprint("users", __name__)


@users_bp.route("/verify-token", methods=["POST"])
def verify_token():
    token = request.json.get("token")

    print(token)
    
    if not token:
        return jsonify({"success": False, "error": "Token missing"}), 400
    
    result, success = auth_service.authenticate(token)
    
    if not success:
        return jsonify({"success": False, "error": result["error"]}), 401
    

    session["user"] = {
        "google_id": result["user_data"]["user_id"],
        "email": result["user_data"]["email"],
        "name": result["user_data"]["name"],
        "given_name": result["user_data"]["given_name"],
        "picture": result["user_data"]["picture"]
    }

    return jsonify({
        "success": True,
        "user": {
            **session["user"],
            "register": result["is_new_user"],
            "is_bought": UserModel.is_bought(google_id=session["user"]["google_id"])
        }
    })


@users_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()  # o session.pop("user", None)
    return jsonify({"success": True, "message": "Sesión cerrada"})



@users_bp.route("/profile", methods=["POST"])
def profile():
    if "user" not in session:
        return jsonify({"success": False, "error": "No ha iniciado sesión"}), 401
    return jsonify({
        "success": True,
        "user": {
            **session["user"],
            "is_bought": UserModel.is_bought(google_id=session["user"]["google_id"])
        }
    })

@users_bp.route("/user/<googleid>", methods=["GET"])
def user_by_google_id(googleid):
    if "user" not in session:
        return jsonify({"success": False, "error": "No ha iniciado sesión"}), 401

    print(googleid)
    user = User.query.filter(User.google_id == googleid).first()


    if not user:
        return jsonify({"success": False, "error": "Usuario no encontrado"}), 404

    return jsonify({
        "name": user.to_dict().get("name")  # Devuelve el diccionario completo del usuario
    })
