from . import db
from datetime import datetime
from models.Refund import Refund

class Refer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(100), db.ForeignKey('user.google_id'), nullable=False)
    porcentage = db.Column(db.String(100), nullable=False)
    payment_id = db.Column(db.Integer, db.ForeignKey('payment.id'), nullable=True)
    refund_id = db.Column(db.Integer, db.ForeignKey('refund.id'), nullable=True, unique=True)
    value = db.Column(db.String(100), nullable=False)
    
    # Relación: un Refer está asociado a un Refund (opcional)
    refund = db.relationship("Refund", backref="refers", lazy=True)
    payment = db.relationship("Payment", backref="payments", lazy=True)

    is_pay = db.Column(db.Boolean, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
