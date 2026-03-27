from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    SECRET_KEY: str
    SECURITY_PASSWORD_SALT: str
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    MYSQL_HOST: str
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_DB: str

    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_PORT: int = 587
    MAIL_USE_TLS: bool = True
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_DEFAULT_SENDER: str = ""
    ADMIN_EMAIL: str = "romarioariza@gmail.com"

    GOOGLE_CLIENT_ID: str = "569719966413-vb4hran623dj2mj7urgumsc6u5627dmb.apps.googleusercontent.com"

    REFUND_PERCENTAGE: float = 30.0

    # PayU
    PAYU_URL: str = ""
    PAYU_API_KEY: str = ""
    PAYU_MERCHANT_ID: str = ""
    PAYU_ACCOUNT_ID: str = ""

    # PayPal (preferir variables de entorno; valores por defecto vacíos)
    PAYPAL_MODE: str = "sandbox"
    PAYPAL_CLIENT_ID: str = "Aew9PIGagtvhZ6jRQc83QvG5_c7HwBiDH80DMHJuYIl5py8i9U94o_VeayP1H26zvO6V3rfKK-GqyS4b"
    PAYPAL_CLIENT_SECRET: str = "EOBT3PiVBjI3pSUDXKnn01b3FlGsjtLlnrHzoTvtnx21Pygm4cVUBgcsjjLtI6wCYh3Rc4Uc_6cli7l-"

    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None

    DEBUG: bool = True

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}/{self.MYSQL_DB}?charset=utf8mb4"
        )

    @property
    def upload_folder(self) -> str:
        base = Path(__file__).resolve().parent
        return str(base / "static" / "uploads")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
