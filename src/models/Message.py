from . import db
from datetime import datetime



class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(100), nullable=False)
    google_id = db.Column(db.String(100), db.ForeignKey('user.google_id'), nullable=True)
    category_id= db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    stars = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)