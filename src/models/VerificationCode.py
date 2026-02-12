from models import db
from datetime import datetime, timedelta
import random
import hashlib

class VerificationCode(db.Model):
    __tablename__ = 'verification_codes'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False)  # Storing hash
    code = db.Column(db.String(255), nullable=False)   # Storing hash
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)

    def __init__(self, email, code=None):
        # We hash the email to store it obfuscated
        self.email = hashlib.sha256(email.encode()).hexdigest()
        
        # Generate code if not provided
        raw_code = code if code else ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
        # Hash the code
        self.code = hashlib.sha256(raw_code.encode()).hexdigest()
        
        self.created_at = datetime.utcnow()
        self.expires_at = self.created_at + timedelta(minutes=3)
        self.is_used = False
        
        # Store raw code in instance for sending email (not persisted)
        self.raw_code = raw_code

    def is_valid(self):
        return not self.is_used and datetime.utcnow() < self.expires_at

    @staticmethod
    def hash_value(value):
        return hashlib.sha256(value.encode()).hexdigest()
