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
from servises.payment.payment_repository import PaymentRespository
from models.SystemVariable import SystemVariable


load_dotenv()

class CategoryModel(Category):
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
        if not category_id:
            return None
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
    
    def user_is_bought(self, viewer_google_id: str | None = None):
        if not viewer_google_id:
            return False
        return Payment.query.filter(
            (Payment.google_id == viewer_google_id) & (Payment.category_id == self.id)
        ).first() is not None

    def user_is_any_bougth(self, viewer_google_id: str | None = None):
        if not viewer_google_id:
            return False
        return Payment.query.filter(
            Payment.google_id == viewer_google_id
        ).first() is not None

    def user_is_comment(self, viewer_google_id: str | None = None):
        if not viewer_google_id:
            return False
        return Message.query.filter(
            (Message.google_id == viewer_google_id) & (Message.category_id == self.id)
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
    def calc_price(self, descuento=0):
        """
        Calcula el precio final y el descuento efectivo, retornando los valores
        sin modificar el estado del objeto.
        """

        # 1. Calcula el precio con el descuento inicial de la categoría
        precio_descontado = self.calcular_precio_con_descuento(self.precio, self.descuento)
        
        precio_final = 0
        descuento_aplicado = self.descuento # Por defecto, es el de la categoría

        # 2. Decide si se aplica el descuento adicional del 50%
        precio_final = precio_descontado - (precio_descontado * descuento / 100)
        descuento_aplicado = self.calcular_porcentaje_efectivo(self.precio, precio_final)
        
        # Retorna un diccionario con los resultados del cálculo
        return {
            'precio_final': precio_final,
            'descuento_aplicado': descuento_aplicado
        }



    def get_aggregated_plataformas(self):
        if not self.related_categories:
            return {}
        
        plataformas_map = {}
        for rc in self.related_categories:
            if not rc.seccion_plataformas:
                continue
            plats = rc.seccion_plataformas.get("plataformas", [])
            for p in plats:
                titulo = p.get("titulo_plataforma")
                if not titulo:
                    continue
                if titulo not in plataformas_map:
                    plataformas_map[titulo] = {
                        "titulo_plataforma": titulo,
                        "imagen_url": p.get("imagen_url", ""),
                        "url_plataforma_seleccionada": p.get("url_plataforma_seleccionada", ""),
                        "cursos": [],
                        "cantidad_cursos_plataforma": 0
                    }
                plataformas_map[titulo]["cursos"].extend(p.get("cursos", []))
                
        # Update counts
        result_plataformas = []
        for p in plataformas_map.values():
            p["cantidad_cursos_plataforma"] = len(p["cursos"])
            result_plataformas.append(p)
            
        if not result_plataformas:
            return {}
            
        return {
            "plataformas": result_plataformas,
            "cantidad_plataformas": len(result_plataformas)
        }

    def get_aggregated_temas(self):
        if not self.related_categories:
            return {}
            
        temas_map = {}
        for rc in self.related_categories:
            if not rc.seccion_temas:
                continue
            temas = rc.seccion_temas.get("temas", [])
            for t in temas:
                titulo = t.get("titulo_tema")
                if not titulo:
                    continue
                if titulo not in temas_map:
                    temas_map[titulo] = {
                        "titulo_tema": titulo,
                        "imagen_url": t.get("imagen_url", ""),
                        "url_tema_seleccionado": t.get("url_tema_seleccionado", ""),
                        "cursos": [],
                        "cantidad_cursos_tema": 0
                    }
                temas_map[titulo]["cursos"].extend(t.get("cursos", []))
                
        result_temas = []
        for t in temas_map.values():
            t["cantidad_cursos_tema"] = len(t["cursos"])
            result_temas.append(t)
            
        if not result_temas:
            return {}
            
        return {
            "temas": result_temas,
            "cantidad_temas": len(result_temas)
        }

    def get_aggregated_lista_completa(self):
        if not self.related_categories:
            return {}
            
        all_cursos = []
        for rc in self.related_categories:
            if not rc.seccion_lista_completa:
                continue
            cursos = rc.seccion_lista_completa.get("lista_completa", [])
            all_cursos.extend(cursos)
            
        if not all_cursos:
            return {}
            
        return {
            "lista_completa": all_cursos,
            "cantidad_cursos": len(all_cursos)
        }

    def to_dict(
        self,
        light=False,
        user_country: str | None = None,
        viewer_google_id: str | None = None,
    ):
        """Convierte la instancia en un diccionario para facilitar la serialización."""

        user_country = (user_country or "").upper()
        cambio_dolar_raw = SystemVariable.query.filter_by(campo_codigo="CAMBIO_DOLAR").first()
        try:
            cambio_dolar = float(cambio_dolar_raw.dato) if cambio_dolar_raw and cambio_dolar_raw.dato else 1.0
        except (TypeError, ValueError):
            cambio_dolar = 1.0
            
        if user_country == "CO":
            precio = self.precio
        else:
            precio = self.precio / cambio_dolar if cambio_dolar else self.precio
        if light:
            plataformas = {}
            temas = {}
            lista_completa = {}
            pregunta_respuesta = []
            courses = []
        else:
            plataformas = self.seccion_plataformas if self.seccion_plataformas and self.seccion_plataformas.get('plataformas') else self.get_aggregated_plataformas()
            temas = self.seccion_temas if self.seccion_temas and self.seccion_temas.get('temas') else self.get_aggregated_temas()
            lista_completa = self.seccion_lista_completa if self.seccion_lista_completa and self.seccion_lista_completa.get('lista_completa') else self.get_aggregated_lista_completa()
            pregunta_respuesta = self.pregunta_respuesta if self.pregunta_respuesta is not None else []
            courses = [course.to_dict() for course in self.courses]

        return {
            'id': self.id,
            'titulo':self.titulo,
            'url': self.url,
            'frase_1': self.frase_1,
            'frase_2': self.frase_2,
            'imagen_url': self.imagen_url,
            'num_per': self.num_per,
            'cat_rel': [category.id for category in self.related_categories],
            'pregunta_respuesta': pregunta_respuesta,
            'seccion_plataformas': plataformas,
            'seccion_temas': temas,
            'seccion_lista_completa': lista_completa,
            'descuento': self.descuento,
            'precio': precio,
            'duracion': self.duracion,
            'user_bought': self.user_is_bought(viewer_google_id),
            'user_comment': self.user_is_comment(viewer_google_id),
            'courses': courses,
            'delete_at': self.delete_at.isoformat() if self.delete_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
