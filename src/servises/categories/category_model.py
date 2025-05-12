import os
import hashlib
import uuid
from dotenv import load_dotenv
from models.Category import Category
from models import db
from datetime import datetime
from models.Course import Course 
from models.Payment import Payment
from models.Message import Message
from flask import session
from servises.payment.payment_repository import PaymentRespository


load_dotenv()

class CategoryModel(Category):
    courses = db.relationship('Course', backref='category', lazy=True)
    def __init__(self, url=None, title=None, frase_1=None, frase_2=None, imagen_url=None, num_per=None,
                 descuento=None, precio=None, duracion=None, delete_at=None, descuento_total_price=0):
        self.url = url
        self.frase_1 = frase_1
        self.frase_2 = frase_2
        self.imagen_url = imagen_url
        self.num_per = num_per
        self.descuento = descuento
        self.precio = precio
        self.duracion = duracion
        self.titulo=title
        self.descuento_total_price = descuento_total_price
        self.delete_at = delete_at
        self.created_at = datetime.utcnow()

    def save(self):
        """Guarda la instancia en la base de datos."""
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def find(category_id):
        return CategoryModel.query.get(category_id)

    def delete(self):
        """Elimina la instancia de la base de datos."""
        db.session.delete(self)
        db.session.commit()

    def update(self, **kwargs):
        """Actualiza los atributos de la instancia con los valores proporcionados."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        db.session.commit()

    @classmethod
    def get_all(cls):
        """Recupera todas las instancias de CategoryModel."""
        return cls.query.all()

    @classmethod
    def get_by_id(cls, category_id):
        """Recupera una instancia de CategoryModel por su ID."""
        return cls.query.get(category_id)
    
    @classmethod
    def search_by_title(cls, search_term, limit=None):
        """
        Retorna una lista de categorías cuyo título contiene el término de búsqueda (case-insensitive).
        :param search_term: Cadena para buscar dentro del título.
        :param limit: Número máximo de resultados a devolver (opcional).
        :return: Lista de instancias CategoryModel.
        """
        query = cls.query.filter(cls.titulo.ilike(f"%{search_term}%"))
        if limit:
            return query.limit(limit).all()
        return query.all()
    
    def user_is_bought(self):
        if "user" not in session:
            return False
        user_google_id = session["user"]["google_id"]
        return Payment.query.filter(
            (Payment.google_id == user_google_id) & (Payment.category_id == self.id)
        ).first() is not None
    

    def user_is_any_bougth(self):
        if "user" not in session:
            return False
        user_google_id = session["user"]["google_id"]
        return Payment.query.filter(
            Payment.google_id == user_google_id
        ).first() is not None
    
    

    def user_is_comment(self):
        if "user" not in session:
            return False
        user_google_id = session["user"]["google_id"]
        return Message.query.filter(
            (Message.google_id == user_google_id) & (Message.category_id == self.id)
        ).first() is not None
    

    def calc_price(self, is_middle_price):
        is_bought=self.user_is_any_bougth()
        self.descuento_total_price = round(float(self.precio) - (float(self.precio) * (float(self.descuento) / 100)))

        if  is_bought:
            self.descuento_total_price = round(self.descuento_total_price * 0.5)
            descuento_total = (1 - (self.descuento_total_price / float(self.precio))) * 100
            self.descuento = descuento_total
            return

        if not is_bought and not is_middle_price:
            self.descuento_total_price = round(self.descuento_total_price * 0.5)
            descuento_total = (1 - (self.descuento_total_price / float(self.precio))) * 100
            self.descuento = descuento_total



    def generate_firm_payu(self):

        self.calc_price(is_middle_price=True)
        repo= PaymentRespository(price=self.descuento_total_price)
        repo.generate_firm()
        return {'signature':repo.signature, "reference_code": repo.reference_code, 'precios_des':self.descuento_total_price}

    def to_dict(self):
        """Convierte la instancia en un diccionario para facilitar la serialización."""

        values=self.generate_firm_payu() 
        return {
            'id': self.id,
            'titulo':self.titulo,
            'url': self.url,
            'frase_1': self.frase_1,
            'frase_2': self.frase_2,
            'imagen_url': self.imagen_url,
            'num_per': self.num_per,
            'descuento': self.descuento,
            'signature': values.get('signature'),
            'reference_code': values.get('reference_code'),
            'precio': self.precio,
            'precio_desc':values.get('precios_des'),
            'duracion': self.duracion,
            'user_bought': self.user_is_bought(),
            'user_comment': self.user_is_comment(),
            'courses': [course.to_dict() for course in self.courses],
            'delete_at': self.delete_at.isoformat() if self.delete_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
