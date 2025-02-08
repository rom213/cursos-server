import random
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app
from . import db
from datetime import datetime



class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(200), nullable=False, unique=True)
    email = db.Column(db.String(200), nullable=False, unique=True)
    rol = db.Column(db.String(20), nullable=True)
    name = db.Column(db.String(200), nullable=False)
    picture = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    delete_at = db.Column(db.DateTime,  nullable=True)

    def __init__(self, google_id, email, name, picture, rol="user"):
        self.google_id=google_id
        self.email=email
        self.rol=rol
        self.name=name
        self.picture=picture
