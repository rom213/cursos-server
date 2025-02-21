from models.Payment import Payment
from models import db
from datetime import datetime

class PaymentModel(Payment):
    
    def __init__(self, signature, google_id, category_id, status, is_refer=False):
        self.signature = signature
        self.google_id = google_id
        self.category_id = category_id
        self.status = status
        self.is_refer = is_refer
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
    def get_by_id(cls, payment_id):
        """Recupera una instancia de PaymentModel por su ID."""
        return cls.query.get(payment_id)
    
    @classmethod
    def get_all(cls):
        """Recupera todas las instancias de PaymentModel."""
        return cls.query.all()

    def verify(self):
        """Verifica si ya existe un pago con la misma firma y google_id."""
        exists = Payment.query.filter(
            Payment.signature == self.signature,
            Payment.google_id == self.google_id
        ).first()
        return exists is None  # Devuelve True si no existe, False si ya existe

    def to_dict(self):
        """Convierte la instancia en un diccionario para facilitar la serialización."""
        return {
            'id': self.id,
            'signature': self.signature,
            'google_id': self.google_id,
            'category_id': self.category_id,
            'status': self.status,
            'is_refer': self.is_refer,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
