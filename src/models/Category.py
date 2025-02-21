from . import db
from datetime import datetime



class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(100), nullable=True)
    frase_1 = db.Column(db.String(200), nullable=True)
    frase_2 = db.Column(db.String(200), nullable=True)
    imagen_url = db.Column(db.String(200), nullable=True)
    num_per = db.Column(db.String(20), nullable=True)
    descuento = db.Column(db.String(20), nullable=True)
    precio = db.Column(db.Integer, nullable=True)
    description = db.Column(db.String(200), nullable=True)
    duracion = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    delete_at = db.Column(db.DateTime, nullable=True)

    def __init__(self, url=None, frase_1=None, frase_2=None, imagen_url=None, num_per=None, 
                 descuento=None, precio=None, description=None, duracion=None, delete_at=None):
        self.url = url
        self.frase_1 = frase_1
        self.frase_2 = frase_2
        self.imagen_url = imagen_url
        self.num_per = num_per
        self.descuento = descuento
        self.precio = precio
        self.description = description
        self.duracion = duracion
        self.delete_at = delete_at