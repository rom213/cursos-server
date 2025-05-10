from flask import Blueprint, request, jsonify, session
from config import config
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from models.User import User, db
from abc import ABC, abstractmethod
from servises.Users.user_model import UserModel
from models.account import Account


# 1. Repository Pattern -----------------------------------------------------------------
class UserRepository:
    @staticmethod
    def get_by_google_id(google_id: str) -> User:
        user=User.query.outerjoin(Account, Account.google_id == User.google_id)\
                     .filter(User.google_id == google_id)\
                     .first()
        return user

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
                "user_data": user,
                "is_new_user": is_new_user
            }, True

        except Exception as e:
            return {"error": str(e)}, False

# Configuración y blueprint -------------------------------------------------------------
GOOGLE_CLIENT_ID = "569719966413-vb4hran623dj2mj7urgumsc6u5627dmb.apps.googleusercontent.com"

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
    # print(result["user_data"].accounts[0].name_acc)
    if not success:
        return jsonify({"success": False, "error": result["error"]}), 401
    

    accounts = [acc.to_dict() for acc in result["user_data"].accounts]

    session["user"] = {
        "google_id": result["user_data"].google_id,
        "accounts": accounts,
        "email": result["user_data"].email,
        "num_whatsapp": result["user_data"].num_whatsapp.split()[1],
        "name": result["user_data"].name,
        "given_name": result["user_data"].name.split()[0],
        "prefix":result["user_data"].num_whatsapp.split()[0],
        "picture": result["user_data"].picture,
        "is_bought": UserModel.is_bought(google_id=session["user"]["google_id"])
    }

    return jsonify({
        "success": True,
        "user": {
            **session["user"],
            "register": result["is_new_user"],
            
        }
    })


@users_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()  # o session.pop("user", None)
    return jsonify({"success": True, "message": "Sesión cerrada"})

@users_bp.route("/profile", methods=["POST"])
def profile():

    # verifica si hay seccion y actualiza cualquier novedad en el usuario
    if "user" not in session:
        return jsonify({"success": False, "error": "No ha iniciado sesión"}), 401
    
    user = user_repository.get_by_google_id(session["user"]["google_id"])
    
    
    accounts = [acc.to_dict() for acc in user.accounts]

    session["user"] = {
        "google_id": user.google_id,
        "accounts": accounts,
        "email": user.email,
        "num_whatsapp":user.num_whatsapp.split()[1],
        "name": user.name,
        "given_name": user.name.split()[0],
        "prefix":user.num_whatsapp.split()[0],
        "picture": user.picture,
        "is_bought": UserModel.is_bought(google_id=session["user"]["google_id"])
    }

    return jsonify({
        "success": True,
        "user": {
            **session["user"],
        }
    })

@users_bp.route("/user/<googleid>", methods=["GET"])
def user_by_google_id_afiliaty(googleid):

    """este metodo se usa para verificar si existe el usuario de google id"""
    
    if "user" not in session:
        return jsonify({"success": False, "error": "No ha iniciado sesión"}), 401
    
    if session["user"].get("is_bought"):
        return jsonify({"success": False, "error": "buen intento"}), 403

    print(session["user"].get("is_bought")) 
    user = UserModel.get_by_google_id(google_id=googleid)
    is_bought = UserModel.is_bought(google_id=googleid)

    if not is_bought:
        return jsonify({"success": False, "error": "Usuario no encontrado"}), 404

    if not user:
        return jsonify({"success": False, "error": "Usuario no registrado, pero con compra válida"}), 400
    
    return jsonify({
        "name": user.to_dict().get("name")
    })
