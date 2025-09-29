from . import db
from datetime import datetime


class PaymentRegister(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pay_value_refer = db.Column(db.String(100), nullable=False)
    google_id = db.Column(db.String(100), db.ForeignKey('user.google_id'), nullable=True)
    google_id_refer = db.Column(db.String(100), db.ForeignKey('user.google_id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    currency = db.Column(db.String(20), nullable=True)
    codeValue = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.Enum('pending', 'complated', 'error', 'refunded', name='status_enum'), default='pending', nullable=False)

    def cambiarStatus(self, status='complated'):
        self.status = status
        db.session.commit()
