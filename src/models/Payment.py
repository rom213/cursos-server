from enum import Enum
from . import db
from datetime import datetime


class PaymentStatus(str, Enum):
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    signature = db.Column(db.String(100), nullable=False)
    price = db.Column(db.String(100), nullable=False)
    google_id = db.Column(db.String(100), db.ForeignKey('user.google_id'), nullable=True)
    category_id= db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    status = db.Column(
        db.Enum(PaymentStatus, name='payment_status_enum', values_callable=lambda x: [e.value for e in x]),
        nullable=True,
    )
    is_refer = db.Column(db.Boolean, nullable=True)
    info_error = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    category = db.relationship("Category", backref="categories", lazy=True)
