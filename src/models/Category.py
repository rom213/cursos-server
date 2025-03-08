from . import db
from datetime import datetime



class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=True)
    url = db.Column(db.String(100), nullable=True)
    frase_1 = db.Column(db.String(200), nullable=True)
    frase_2 = db.Column(db.String(200), nullable=True)
    imagen_url = db.Column(db.String(200), nullable=True)
    num_per = db.Column(db.String(20), nullable=True)
    descuento = db.Column(db.String(20), nullable=True)
    precio = db.Column(db.Integer, nullable=True)
    duracion = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    delete_at = db.Column(db.DateTime, nullable=True)

