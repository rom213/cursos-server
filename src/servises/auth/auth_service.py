from models.VerificationCode import VerificationCode
from models import db
from extensions import mail
from flask_mail import Message
from flask import current_app
from datetime import datetime

class AuthService:
    @staticmethod
    def generate_verification_code(email):
        # Create new code (hashing happens in model __init__)
        verification_code = VerificationCode(email)
        db.session.add(verification_code)
        db.session.commit()

        # Send email using the raw code (stored temporarily in the instance)
        msg = Message("Código de Verificación - Cursos Estudia y Trabaja",
                      recipients=[email])
        msg.body = f"Tu código de verificación es: {verification_code.raw_code}\n\nEste código es válido por 3 minutos."
        mail.send(msg)

        return verification_code

    @staticmethod
    def verify_code(email, code):
        # Hash inputs to find in DB
        email_hash = VerificationCode.hash_value(email)
        code_hash = VerificationCode.hash_value(code)

        print("email_hash", email_hash)
        print("code_hash", code_hash)
        
        # Find the latest valid code for this email
        verification_code = VerificationCode.query.filter_by(email=email_hash, code=code_hash, is_used=False).order_by(VerificationCode.created_at.desc()).first()

        if not verification_code:
            return False, "Código inválido o no encontrado."

        if not verification_code.is_valid():
            return False, "El código ha expirado."

        # Mark as used
        verification_code.is_used = True
        db.session.commit()

        return True, "Código verificado correctamente."
