from models.account import Account
from models.account import AccountType
from models import db
from datetime import datetime

class AccountModel(Account):
    def save(self):
        """Guarda la instancia en la base de datos."""
        db.session.add(self)
        db.session.commit()

    def delete(self):
        """Elimina la instancia de la base de datos."""
        db.session.delete(self)
        db.session.commit()

    def update(self, **kwargs):
        """
        Actualiza atributos de la instancia.
        Solo se tendrán en cuenta aquellos atributos que existan en el modelo.
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        db.session.commit()

    @classmethod
    def get_by_id(cls, account_id):
        """Recupera una cuenta por su ID."""
        return cls.query.get(account_id)

    @classmethod
    def get_all(cls):
        """Recupera todas las cuentas."""
        return cls.query.all()


    def to_dict(self):
        """Convierte la instancia en un diccionario para JSON."""
        return {
            "id": self.id,
            "name_acc": self.name_acc.value,
            "number_acc": self.number_acc,
            "google_id": self.google_id,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }