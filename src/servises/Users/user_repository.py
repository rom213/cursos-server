from .user_model import UserModel
from flask import session, jsonify

class UserRepository():
    def verify_seccion():
        if "user" not in session:
            return False
        return True
    
    