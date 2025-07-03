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
    

    def calcular_precio_con_descuento(self, precio, descuento_porcentaje):
        """Calcula el precio final aplicando un descuento en porcentaje."""
        factor_descuento = float(descuento_porcentaje) / 100
        precio_final = float(precio) * (1 - factor_descuento)
        return round(precio_final)

    def calcular_porcentaje_efectivo(self, precio_original, precio_final):
        if float(precio_original) == 0:
            return 0  # Evitar división por cero
        
        porcentaje = (1 - (float(precio_final) / float(precio_original))) * 100
        return porcentaje

    # Versión corregida de calc_price
    def calc_price(self, is_middle_price, is_not_payu_request=True):
        """
        Calcula el precio final y el descuento efectivo, retornando los valores
        sin modificar el estado del objeto.
        """
        is_bought = False
        if is_not_payu_request:
            is_bought = self.user_is_any_bougth()

        # 1. Calcula el precio con el descuento inicial de la categoría
        precio_descontado = self.calcular_precio_con_descuento(self.precio, self.descuento)
        
        precio_final = 0
        descuento_aplicado = self.descuento # Por defecto, es el de la categoría

        # 2. Decide si se aplica el descuento adicional del 50%
        if is_bought or (not is_bought and not is_middle_price):
            # Aplica el 50% de descuento adicional sobre el precio ya rebajado
            precio_final = round(precio_descontado * 0.5)
            # Calcula el porcentaje efectivo para este cálculo específico
            descuento_aplicado = self.calcular_porcentaje_efectivo(self.precio, precio_final)
        else:
            # Si no, el precio final es el que tiene el descuento inicial
            precio_final = precio_descontado
        
        # Retorna un diccionario con los resultados del cálculo
        return {
            'precio_final': precio_final,
            'descuento_aplicado': descuento_aplicado
        }


    def generate_firm_payu(self):

        values=self.calc_price(is_middle_price=True)
        repo= PaymentRespository(price=values.get("precio_final"))
        repo.generate_firm()
        return {'signature':repo.signature, "reference_code": repo.reference_code, 'precios_des':values.get("precio_final")}

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
