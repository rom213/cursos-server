from models import db
from datetime import datetime

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    autor = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        """Convierte la instancia en un diccionario para facilitar la serialización."""
        return {
            'id': self.id,
            'name': self.name,
            'autor': self.autor,
            'category_id': self.category_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
