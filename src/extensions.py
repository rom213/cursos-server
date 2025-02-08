# extensions.py
from flask_mysqldb import MySQL
from flask import current_app
from itsdangerous import URLSafeTimedSerializer

# Crear instancias de las extensiones

mysql = MySQL()




def get_serializer():
    return URLSafeTimedSerializer(
        secret_key=current_app.config['SECRET_KEY'],
        salt=current_app.config['SECURITY_PASSWORD_SALT']
    )