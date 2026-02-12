from . import db
from datetime import datetime



import enum

class TipoCategoria(enum.Enum):
    CAT_1 = 1
    CAT_2 = 2
    CAT_3 = 3
    CAT_4 = 4

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo_categoria = db.Column(db.Enum(TipoCategoria), nullable=True)
    titulo = db.Column(db.String(200), nullable=True)
    url = db.Column(db.String(100), nullable=True)
    frase_1 = db.Column(db.String(200), nullable=True)
    frase_2 = db.Column(db.String(200), nullable=True)
    imagen_url = db.Column(db.String(200), nullable=True)
    num_per = db.Column(db.String(20), nullable=True)
    contenido = db.Column(db.JSON, nullable=True, default=lambda: {})
    descuento = db.Column(db.String(20), default="0", nullable=False)
    precio = db.Column(db.Integer, nullable=True)
    duracion = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    delete_at = db.Column(db.DateTime, nullable=True)
