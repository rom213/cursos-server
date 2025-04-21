from . import db
from datetime import datetime
import enum

class AccountType(enum.Enum):
    nequi = "nequi"
    daviplata = "daviplata"
    llave = "llave"

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name_acc = db.Column(db.Enum(AccountType), nullable=False)
    number_acc = db.Column(db.String(100), nullable=False)
    google_id = db.Column(db.String(100), db.ForeignKey('user.google_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
