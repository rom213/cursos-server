import re
import smtplib
import subprocess
import uuid
from abc import ABC, abstractmethod

import requests
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import JSONResponse
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models.SystemVariable import SystemVariable
from models.User import User
from models import db
from servises.Users.user_model import UserModel
from models.account import Account
from utils.auth import create_access_token, get_current_user_payload, get_google_id

# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------

def where_is_my_ip_from_headers(headers: dict) -> str | None:
    forwarded = headers.get("x-forwarded-for")
    return forwarded.split(",")[0].strip() if forwarded else None


def who_is_my_country(ip_address: str | None) -> str | None:
    try:
        if ip_address:
            response = requests.get("https://ipinfo.io/24.152.58.172/json", timeout=3)
            if response.status_code == 200:
                return response.json().get("country")
    except Exception as e:
        print(f"Error getting country from IP: {e}")
    return None


class UserRepository:
    @staticmethod
    def get_by_google_id(google_id: str) -> User:
        return User.query.filter_by(google_id=google_id).first()

    @staticmethod
    def get_by_email(email: str) -> User:
        return (
            User.query.outerjoin(Account, Account.google_id == User.google_id)
            .filter(User.email == email)
            .first()
        )

    @staticmethod
    def create_google_user(user_data: dict, country: str | None = None) -> User:
        new_user = User(
            google_id=user_data["user_id"],
            email=user_data["email"],
            name=user_data["name"],
            picture=user_data["picture"],
            country=country,
        )
        db.session.add(new_user)
        db.session.commit()
        return new_user

    @staticmethod
    def create_with_generated_id(email: str) -> User:
        generated_id = str(uuid.uuid4())
        name = email.split("@")[0]
        new_user = User(
            google_id=generated_id,
            email=email,
            name=name,
            picture="https://lh3.googleusercontent.com/a/default-user",
        )
        db.session.add(new_user)
        db.session.commit()
        return new_user


# ---------------------------------------------------------------------------
# Strategy Pattern — token verification
# ---------------------------------------------------------------------------

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
                token, google_requests.Request(), self.client_id
            )
            
            return {
                "user_id": idinfo.get("sub"),
                "email": idinfo.get("email"),
                "name": idinfo.get("name", "Usuario"),
                "picture": idinfo.get("picture"),
                "given_name": idinfo.get("given_name"),
                "family_name": idinfo.get("family_name"),
            }
        except Exception as e:
            raise ValueError(f"Invalid token: {str(e)}")


# ---------------------------------------------------------------------------
# Service Layer
# ---------------------------------------------------------------------------

class AuthService:
    def __init__(self, token_verifier: TokenVerifier, user_repository: UserRepository):
        self.token_verifier = token_verifier
        self.user_repository = user_repository

    def authenticate(self, token: str, country: str | None = None) -> tuple:
        try:
            user_data = self.token_verifier.verify(token)
            user = self.user_repository.get_by_email(user_data["email"])

            is_new_user = False
            if not user:
                user = self.user_repository.create_google_user(user_data, country)
                is_new_user = True
            elif country is not None and user.country != country:
                user.country = country
                db.session.commit()

            return {"user_data": user, "is_new_user": is_new_user}, True
        except Exception as e:
            return {"error": str(e)}, False


# ---------------------------------------------------------------------------
# Email validator
# ---------------------------------------------------------------------------

class GoogleEmailValidator:
    @staticmethod
    def get_mx_record(domain: str) -> str | None:
        try:
            result = subprocess.run(
                ["nslookup", "-q=mx", domain],
                capture_output=True,
                text=True,
                shell=True,
            )
            matches = re.findall(r"mail exchanger = ([\w.-]+)", result.stdout)
            return matches[0] if matches else None
        except Exception:
            return None

    @staticmethod
    def validate(email: str) -> tuple:
        try:
            domain = email.split("@")[1]
            mx_host = GoogleEmailValidator.get_mx_record(domain)

            if not mx_host:
                if domain == "gmail.com":
                    mx_host = "gmail-smtp-in.l.google.com"
                else:
                    return False, "No se encontraron registros MX para el dominio."

            server = smtplib.SMTP(mx_host, 25, timeout=5)
            server.helo("validator.com")
            server.mail("validate@validator.com")
            code, message = server.rcpt(email)
            server.quit()

            if code == 250:
                return True, "Válido"
            elif code == 550:
                return False, "El correo no existe en Google (Usuario no encontrado)."
            else:
                return False, f"Respuesta SMTP no válida: {code}"
        except Exception as e:
            return False, f"Error de validación: {str(e)}"


# ---------------------------------------------------------------------------
# DI setup
# ---------------------------------------------------------------------------

user_repository = UserRepository()
google_verifier = GoogleTokenVerifier(settings.GOOGLE_CLIENT_ID)
auth_service = AuthService(google_verifier, user_repository)

router = APIRouter(tags=["users"])


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/verify-token")
def verify_token(
    body: dict = Body(...),
    db: Session = Depends(get_db),
):
    token = body.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="Token missing")

    country = who_is_my_country(None)
    print(token)
    result, success = auth_service.authenticate(token, country)
    if not success:
        raise HTTPException(status_code=401, detail=result["error"])

    user = result["user_data"]
    accounts = [acc.to_dict() for acc in user.accounts]
    num_whatsapp = user.num_whatsapp or ""

    tasa_de_cambio = SystemVariable.query.filter_by(campo_codigo="CAMBIO_DOLAR").first()

    user_payload = {
        "google_id": user.google_id,
        "accounts": accounts,
        "email": user.email,
        "prefix": num_whatsapp.split()[0] if num_whatsapp and len(num_whatsapp.split()) > 0 else "+57",
        "num_whatsapp": num_whatsapp.split()[1] if num_whatsapp and len(num_whatsapp.split()) > 1 else "",
        "name": user.name,
        "given_name": user.name.split()[0],
        "picture": user.picture,
        "is_bought": UserModel.is_vendedor(google_id=user.google_id),
        "country": user.country,
        "tasa_de_cambio": tasa_de_cambio.dato if tasa_de_cambio else 3800,
    }

    access_token = create_access_token(user_payload)

    return {
        "success": True,
        "token": access_token,
        "user": {
            **user_payload,
            "register": result["is_new_user"],
        },
    }


@router.post("/logout")
def logout():
    # Con JWT stateless no hay sesión server-side que limpiar.
    # El cliente descarta el token localmente.
    return {"success": True, "message": "Sesión cerrada"}


@router.post("/profile")
def profile(
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db),
):
    google_id = payload.get("google_id")
    user = user_repository.get_by_google_id(google_id)

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    accounts = [acc.to_dict() for acc in user.accounts]
    num_whatsapp = user.num_whatsapp or ""
    tasa_de_cambio = SystemVariable.query.filter_by(campo_codigo="CAMBIO_DOLAR").first()

    user_payload = {
        "google_id": user.google_id,
        "accounts": accounts,
        "email": user.email,
        "num_whatsapp": num_whatsapp.split()[0] if num_whatsapp and len(num_whatsapp.split()) > 0 else "",
        "prefix": num_whatsapp.split()[1] if num_whatsapp and len(num_whatsapp.split()) > 1 else "+57",
        "name": user.name,
        "given_name": user.name.split()[0],
        "picture": user.picture,
        "is_bought": UserModel.is_vendedor(google_id=user.google_id),
        "country": user.country,
        "tasa_de_cambio": tasa_de_cambio.dato if tasa_de_cambio else 3800,
    }

    return {"success": True, "user": user_payload}


@router.get("/user/{googleid}")
def user_by_google_id_afiliaty(
    googleid: str,
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db),
):
    if payload.get("is_bought"):
        raise HTTPException(status_code=403, detail="buen intento")

    user = UserModel.get_by_google_id(googleid)
    is_bought = UserModel.is_vendedor(googleid)

    if not is_bought:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if not user:
        raise HTTPException(status_code=400, detail="Usuario no registrado, pero con compra válida")

    return {
        "name": user.to_dict().get("name"),
        "cupon": user.to_dict().get("codigo_referido"),
    }


@router.post("/validate-email")
def validate_email(
    body: dict = Body(...),
    db: Session = Depends(get_db),
):
    _ = db
    email = body.get("email")
    if not email:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": "Email is required",
                "records": [],
            },
        )

    email_regex = r"^[a-zA-Z0-9._%+-]+@gmail\.com$"
    if not re.match(email_regex, email):
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": "Only Gmail addresses are allowed",
                "records": [],
            },
        )

    user = user_repository.get_by_email(email)
    if not user:
        user = user_repository.create_with_generated_id(email)

    return {
        "status": "success",
        "message": "User retrieved or created successfully",
        "records": [user.to_dict()],
    }
