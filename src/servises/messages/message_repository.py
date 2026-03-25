from fastapi import HTTPException

from .message_model import MessageModel
from servises.Users.user_model import UserModel
from servises.categories.category_model import CategoryModel


class MessageRepository(MessageModel):
    def __init__(self, category_id: int, google_id: str, message: str = "", stars: int = 0):
        super().__init__(category_id, google_id, message, stars)

    def verify(self):
        user = UserModel.get_by_google_id(google_id=self.google_id)
        category = CategoryModel.find(category_id=self.category_id)

        if user is None and category is None:
            raise HTTPException(status_code=404, detail="not found category_id or google_id")

        message_ok = super().verify()

        if not message_ok:
            raise HTTPException(status_code=423, detail="violacion del sistema")

        return True
