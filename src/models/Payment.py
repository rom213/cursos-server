from . import db
from datetime import datetime



class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    signature = db.Column(db.String(100), nullable=True)
    google_id = db.Column(db.String(100), db.ForeignKey('user.google_id'), nullable=True)
    category_id= db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    status= db.Column(db.String(20), nullable=True)
    is_refer = db.Column(db.Boolean, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
