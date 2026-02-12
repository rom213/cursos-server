from . import db
from .account import AccountType
from datetime import datetime



class Refund(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type_acc_em = db.Column(db.Enum(AccountType), nullable=True)
    titular_acc_em = db.Column(db.String(100), nullable=False)
    number_acc_em = db.Column(db.String(100), nullable=False)
    type_acc_re = db.Column(db.Enum(AccountType), nullable=True)
    titular_acc_res = db.Column(db.String(100), nullable=False)
    number_acc_res = db.Column(db.String(100), nullable=False)
    code_reference = db.Column(db.String(255), nullable=False)
    value = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __init__(self, type_acc_em, type_acc_re, titular_acc_em, titular_acc_res, number_acc_em, number_acc_res, value, image, code_reference,created_at=None):
        self.type_acc_em = type_acc_em
        self.type_acc_re = type_acc_re
        self.code_reference= code_reference
        self.titular_acc_em = titular_acc_em
        self.titular_acc_res = titular_acc_res
        self.number_acc_em = number_acc_em
        self.number_acc_res = number_acc_res
        self.value = value
        self.image = image
        if created_at is not None:
            self.created_at = created_at