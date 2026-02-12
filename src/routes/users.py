from flask import Blueprint, request, jsonify, session
import uuid
import re
import smtplib
import subprocess
from config import config
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from models.User import User, db
from abc import ABC, abstractmethod
from servises.Users.user_model import UserModel
from models.account import Account
import uuid


# 1. Repository Pattern -----------------------------------------------------------------
class UserRepository:
    @staticmethod
    def get_by_google_id(google_id: str) -> User:
        return User.query.filter_by(google_id=google_id).first()

    @staticmethod
    def get_by_email(email: str) -> User:
        user=User.query.outerjoin(Account, Account.google_id == User.google_id)\
                     .filter(User.email == email)\
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

    @staticmethod
    def create_with_generated_id(email: str) -> User:
        # Generar un google_id tipo uid si no tenemos uno real
        generated_id = str(uuid.uuid4())
        
        # Nombre por defecto basado en el email
        name = email.split('@')[0]
        
        new_user = User(
            google_id=generated_id,
            email=email,
            name=name,
            picture="https://lh3.googleusercontent.com/a/default-user" # Placeholder
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
            user = self.user_repository.get_by_email(user_data["email"])
                

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

# 4. Utilities --------------------------------------------------------------------------
class GoogleEmailValidator:
    @staticmethod
    def get_mx_record(domain: str) -> str:
        try:
            # Ejecutar nslookup
            result = subprocess.run(
                ["nslookup", "-q=mx", domain],
                capture_output=True,
                text=True,
                shell=True 
            )
            
            # Buscar el servidor de correo (preferencia más baja o el primero que encontremos)
            # Output format example: "domain.com MX preference = 10, mail exchanger = mail.example.com"
            matches = re.findall(r"mail exchanger = ([\w.-]+)", result.stdout)
            
            if matches:
                return matches[0] # Retorna el primero (usualmente el de menor preferencia si está ordenado, pero sirve)
            
            return None
        except Exception:
            return None

    @staticmethod
    def validate(email: str) -> tuple:
        try:
            domain = email.split('@')[1]
            mx_host = GoogleEmailValidator.get_mx_record(domain)

            # Fallback para gmail.com si nslookup falla o no devuelve nada
            if not mx_host:
                if domain == 'gmail.com':
                    mx_host = 'gmail-smtp-in.l.google.com'
                else:
                    return False, "No se encontraron registros MX para el dominio."

            # Verificar si es un servidor de Google (Opcional, pero solicitado "registrado en Google")
            if "google" not in mx_host and "googlemail" not in mx_host:
                 # Podríamos ser estrictos y rechazar si no es google, 
                 # o tratar de validar igual. Por ahora, asumimos que "registrado en google" 
                 # implica cuenta hosteada en Google (Gmail o Workspace)
                 pass
                 # return False, "El dominio no está gestionado por Google." (Comentado para ser laxo si se requiere)

            # Conexión SMTP
            # Puerto 25 es el estándar para MTA-to-MTA.
            server = smtplib.SMTP(mx_host, 25, timeout=5)
            server.helo('validator.com') # Usar un dominio dummy
            server.mail('validate@validator.com')
            code, message = server.rcpt(email)
            server.quit()

            if code == 250:
                return True, "Válido"
            elif code == 550:
                return False, "El correo no existe en Google (Usuario no encontrado)."
            else:
                # Otros códigos (450, 451, etc.) pueden ser temporales.
                # Asumimos error para seguridad o 'Warning'
                return False, f"Respuesta SMTP no válida: {code}"

        except Exception as e:
            return False, f"Error de validación: {str(e)}"

# Configuración y blueprint -------------------------------------------------------------
GOOGLE_CLIENT_ID = "569719966413-vb4hran623dj2mj7urgumsc6u5627dmb.apps.googleusercontent.com"
""
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
    num_whatsapp = getattr(result["user_data"], "num_whatsapp", "") or ""

    session["user"] = {
        "google_id": result["user_data"].google_id,
        "accounts": accounts,
        "email": result["user_data"].email,
        "prefix": num_whatsapp.split()[0] if num_whatsapp and len(num_whatsapp.split()) > 0 else "+57",
        "num_whatsapp": num_whatsapp.split()[1] if num_whatsapp and len(num_whatsapp.split()) > 1 else "",
        "name": result["user_data"].name,
        "given_name": result["user_data"].name.split()[0],
        "picture": result["user_data"].picture,
        "is_bought": UserModel.is_bought(google_id=result["user_data"].google_id)
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
    
    if not user:
        return jsonify({"success": False, "error": "Usuario no encontrado"}), 404
    accounts = [acc.to_dict() for acc in user.accounts]
    num_whatsapp = user.num_whatsapp or ""
    
    session["user"] = {
        "google_id": user.google_id,
        "accounts": accounts,
        "email": user.email,
        "num_whatsapp": num_whatsapp.split()[0] if num_whatsapp and len(num_whatsapp.split()) > 0 else "",
        "name": user.name,
        "given_name": user.name.split()[0],
        "prefix":num_whatsapp.split()[1] if num_whatsapp and len(num_whatsapp.split()) > 1 else "+57",
        "picture": user.picture,
        "is_bought": UserModel.is_bought(google_id=user.google_id)
    }

    return jsonify({
        "success": True,
        "user": {
            **session["user"],
        }
    })

@users_bp.route("/user/<googleid>", methods=["GET"])
def user_by_google_id_afiliaty(googleid):

    """este metodo se usa para verificar si existe el usuario de google id y verifica si el usuario a comprado"""
    
    if "user" not in session:
        return jsonify({"success": False, "error": "No ha iniciado sesión"}), 401
    
    if session["user"].get("is_bought"):
        return jsonify({"success": False, "error": "buen intento"}), 403

    print(googleid)
    print(session["user"].get("is_bought")) 
    user = UserModel.get_by_google_id(googleid)
    is_bought = UserModel.is_bought(googleid)

    if not is_bought:
        return jsonify({"success": False, "error": "Usuario no encontrado"}), 404

    if not user:
        return jsonify({"success": False, "error": "Usuario no registrado, pero con compra válida"}), 400
    
    return jsonify({
        "name": user.to_dict().get("name"),
        "cupon": user.to_dict().get("codigo_referido")
    })



@users_bp.route("/validate-email", methods=["POST"])
def validate_email():
    try:
        data = request.get_json()
        email = data.get("email")

        if not email:
            return jsonify({
                "status": "error",
                "message": "Email is required",
                "records": []
            }), 400

        # Validar que sea Gmail
        email_regex = r'^[a-zA-Z0-9._%+-]+@gmail\.com$'
        if not re.match(email_regex, email):
            return jsonify({
                "status": "error",
                "message": "Only Gmail addresses are allowed",
                "records": []
            }), 400

        # Verificar si existe en la BD
        user = user_repository.get_by_email(email)

        if not user:
            user = user_repository.create_with_generated_id(email)
        
        return jsonify({
            "status": "success",
            "message": "User retrieved or created successfully",
            "records": [user.to_dict()]
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "records": []
        }), 500

