from models.VerificationCode import VerificationCode
from models import db
from utils.mail import send_plain_email


class AuthService:
    @staticmethod
    async def generate_verification_code(email: str):
        verification_code = VerificationCode(email)
        db.session.add(verification_code)
        db.session.commit()

        await send_plain_email(
            subject="Código de Verificación - Cursos Estudia y Trabaja",
            body=(
                f"Tu código de verificación es: {verification_code.raw_code}\n\n"
                "Este código es válido por 3 minutos."
            ),
            recipients=[email],
        )

        return verification_code

    @staticmethod
    def verify_code(email, code):
        email_hash = VerificationCode.hash_value(email)
        code_hash = VerificationCode.hash_value(code)

        verification_code = (
            VerificationCode.query.filter_by(
                email=email_hash, code=code_hash, is_used=False
            )
            .order_by(VerificationCode.created_at.desc())
            .first()
        )

        if not verification_code:
            return False, "Código inválido o no encontrado."

        if not verification_code.is_valid():
            return False, "El código ha expirado."

        verification_code.is_used = True
        db.session.commit()

        return True, "Código verificado correctamente."
