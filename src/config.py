import os

class Config:
    SECRET_KEY = 'laila'
    SECURITY_PASSWORD_SALT = 'perra'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'chatunity7@gmail.com'
    MAIL_PASSWORD = 'vncl refb besy tadl'
    MAIL_DEFAULT_SENDER = 'chatunity7@gmail.com'
    
    # Usar el nuevo formato sin prefijo
    CELERY_BROKER_URL = 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'



class DevelopmentConfig(Config):
    DEBUG = True
    MYSQL_HOST = "localhost"
    MYSQL_USER = "root"
    MYSQL_PASSWORD = "roma"
    MYSQL_DB = "cursos"
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}?charset=utf8mb4"

    # Aquí defines la carpeta de subida para los avatares
    UPLOAD_FOLDER = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "static/uploads"
    )

config = {"development": DevelopmentConfig}
