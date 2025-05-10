from datetime import datetime
from models.Refer import Refer
from models import db

class ReferModel(Refer):
    def __init__(self, google_id, payment_id="0", is_pay=False, refund=None):
        self.google_id = google_id
        self.payment_id = payment_id
        self.refund = refund
        self.is_pay = is_pay
        self.created_at = datetime.utcnow()

    def save(self):
        """
        Guarda la instancia en la base de datos.
        """
        db.session.add(self)
        db.session.commit()


    def delete(self):
        """
        Elimina la instancia de la base de datos.
        """
        db.session.delete(self)
        db.session.commit()

    def update(self, **kwargs):
        """
        Actualiza los atributos de la instancia con los valores proporcionados
        y guarda los cambios en la base de datos.
        
        Ejemplo de uso:
            instancia.update(status="activo", refund=100)
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        db.session.commit()

    @classmethod
    def get_by_id(cls, id):
        """
        Recupera una instancia de ReferModel según su ID.
        """
        return cls.query.get(id)
    
    @classmethod
    def get_all(cls):
        """
        Recupera todas las instancias de ReferModel.
        """
        return cls.query.all()

    def verify(self):
        """
        Verifica si ya existe un registro con el mismo google_id y payment_id.
        Retorna True si existe, de lo contrario False. esto es para verificar compras
        """
        exists = Refer.query.filter(
            Refer.google_id == self.google_id,
            Refer.payment_id == self.payment_id
        ).first()

        
        return exists is None  # Devuelve True si existe, False si no


    def to_dict(self):
        """
        Convierte la instancia en un diccionario para facilitar su serialización.
        """
        return {
            'id': self.id,
            'google_id': self.google_id,
            'payment_id': self.payment_id,
            'status': self.status,
            'refund': self.refund,
            'is_pay': self.is_pay,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
