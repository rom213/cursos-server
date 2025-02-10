from flask import Flask, request, jsonify
from flask_cors import CORS
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from models import db
from config import config
from routes import init_app
from extensions import mysql

app = Flask(__name__)
CORS(app, supports_credentials=True, origins=["http://localhost:5173"] )

# 🔹 Primero carga la configuración
app.config.from_object(config["development"])

# 🔹 Luego inicializa las extensiones con la configuración ya cargada
db.init_app(app)
mysql.init_app(app)

# Inicializar rutas
init_app(app)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Crea las tablas si no existen
    app.run(debug=True, port='5001', host='0.0.0.0')
