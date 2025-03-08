from . message_model import MessageModel
from servises.Users.user_model import UserModel
from servises.categories.category_model import CategoryModel
from flask import jsonify


class MessageRepository(MessageModel):
    def __init__(self, category_id: int, google_id: str, message: str = "", stars: int = 0):
        super().__init__(category_id, google_id, message, stars)

    
    def verify(self):
        user=UserModel.get_by_google_id(google_id=self.google_id)
        category= CategoryModel.find(category_id=self.category_id)

        if user is None and category is None:
            return jsonify({"error": "not found category_id or google_id"}), 404
        

        message = super().verify()

        
        if not message:
            return jsonify({"error": "violacion del sistema"}), 423

        return True

