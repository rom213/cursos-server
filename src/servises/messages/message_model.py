from models.Message import Message
from models import db
from datetime import datetime
from models import User
from sqlalchemy import and_

class MessageModel(Message):
    user = db.relationship('User', backref='category', lazy=True)
    def __init__(self, category_id, google_id, message="", stars=0 ):
        self.category_id = category_id
        self.google_id = google_id
        self.message = message
        self.stars = stars
        self.created_at = datetime.utcnow()

    def save(self):
        """Guarda la instancia en la base de datos."""
        db.session.add(self)
        db.session.commit()

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
    def get_by_category_id(cls, category_id):
        """Recupera una instancia de PaymentModel por su ID."""
        return cls.query.filter(cls.category_id== category_id).all()
    
    @classmethod
    def get_by_google_id_verify(cls, google_id, category_id):
        """Verifica si existe un usuario con el google_id dado."""
        return cls.query.filter(and_(cls.google_id == google_id, cls.category_id == category_id)).first() is not None

    
    @classmethod
    def get_all(cls):
        """Recupera todas las instancias de PaymentModel."""
        return cls.query.all()

    def verify(self):
        """Verifica si ya existe un pago con la misma categoria y google_id."""
        exists = Message.query.filter(
        Message.category_id == self.category_id,
        Message.google_id == self.google_id
        ).first()
        return exists is None  # Devuelve True si no existe, False si ya existe

    def to_dict(self):
        """Convierte la instancia en un diccionario para facilitar la serialización."""
        return {
            'id': self.id,
            'google_id': self.google_id,
            'category_id': self.category_id,
            'stars': self.stars,
            'message': self.message,
            'user': self.user.to_dict(),
            'created_at': self.created_at.strftime("%Y-%m-%d") if self.created_at else None
        }
