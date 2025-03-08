from models.User import User
from models import db
from servises.payment.payment_model import PaymentModel
from datetime import datetime


class UserModel(User):
    def save(self):
        """Guarda el usuario en la base de datos."""
        db.session.add(self)
        db.session.commit()

    def delete(self):
        """Marca el usuario como eliminado (soft delete)."""
        self.delete_at = datetime.utcnow()
        db.session.commit()

    @staticmethod
    def get_by_id(user_id):
        """Obtiene un usuario por su ID."""
        return UserModel.query.filter_by(id=user_id).first()

    @staticmethod
    def get_by_google_id(google_id):
        """Obtiene un usuario por su Google ID."""
        return UserModel.query.filter_by(google_id=google_id).first()
    
    @staticmethod
    def is_bought(google_id):
        """Obtiene un usuario por su Google ID."""
        return PaymentModel.query.filter(PaymentModel.google_id == google_id).first() is not None
    
    @staticmethod
    def get_by_email(email):
        """Obtiene un usuario por su email."""
        return UserModel.query.filter_by(email=email).first()

    def update(self, **kwargs):
        """Actualiza los datos del usuario con los valores proporcionados."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        db.session.commit()

    @staticmethod
    def get_all():
        """Obtiene todos los usuarios que no han sido eliminados."""
        return UserModel.query.filter_by(delete_at=None).all()