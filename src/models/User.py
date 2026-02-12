import random
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app
from . import db
from datetime import datetime



import enum

class TipoUsuario(enum.Enum):
    NUEVO = "nuevo"
    VENDEDOR = "vendedor"
    CUPON = "cupon"


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(200), nullable=False, unique=True)
    rol = db.Column(db.String(20), nullable=True)
    name = db.Column(db.String(200), nullable=False)
    picture = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    num_whatsapp= db.Column(db.String(20), nullable=True)
    delete_at = db.Column(db.DateTime,  nullable=True)

    codigo_referido = db.Column(db.String(100), nullable=True, unique=True)
    descuento_referido = db.Column(db.Float, default=0.0)
    tipo_usuario = db.Column(db.Enum(TipoUsuario), default=TipoUsuario.NUEVO, nullable=True)

    accounts = db.relationship('Account', backref='user', lazy=True)

    def __init__(self, google_id, email, name, picture, rol="user"):
        self.google_id=google_id
        self.email=email
        self.rol=rol
        self.name=name
        self.picture=picture

    def to_dict(self):
        return {
            "id": self.id,
            "google_id": self.google_id,
            "codigo_referido": self.codigo_referido,
            "email": self.email,
            "num_whatsapp":self.num_whatsapp,
            "rol": self.rol,
            "name": self.name,
            "picture": self.picture,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "delete_at": self.delete_at.isoformat() if self.delete_at else None,
    }
