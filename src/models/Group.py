from . import db
from datetime import datetime



class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True)
    group_mail = db.Column(db.String(100), nullable=True)
    description = db.Column(db.String(100), nullable=True)
    count_members= db.Column(db.Integer, nullable=True)
    category_id= db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
