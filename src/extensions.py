from itsdangerous import URLSafeTimedSerializer

from config import settings


def get_serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(
        secret_key=settings.SECRET_KEY,
        salt=settings.SECURITY_PASSWORD_SALT,
    )
