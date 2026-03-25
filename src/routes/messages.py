from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any

from database import get_db
from servises.messages.message_model import MessageModel
from servises.messages.message_repository import MessageRepository
from servises.request.validate_data import ValidateData
from utils.auth import get_google_id, get_token_payload_optional

router = APIRouter(tags=["messages"])


@router.get("/all-messages/{id}")
def all_messages_by_category(
    id: int,
    payload: dict | None = Depends(get_token_payload_optional),
    db: Session = Depends(get_db),
):
    try:
        messages = MessageModel.get_by_category_id(id)

        if payload is None:
            return {
                "is_login": False,
                "is_comment": False,
                "messages": sorted(
                    [msg.to_dict() for msg in messages],
                    key=lambda x: x["stars"],
                    reverse=True,
                ),
            }

        user_google_id = payload.get("google_id")
        user_comment = None
        other_comments = []

        for msg in messages:
            msg_dict = msg.to_dict()
            if msg_dict["google_id"] == user_google_id:
                user_comment = msg_dict
            else:
                other_comments.append(msg_dict)

        other_comments.sort(key=lambda x: x["stars"], reverse=True)
        ordered_messages = [user_comment] + other_comments if user_comment else other_comments

        return {
            "is_login": True,
            "is_comment": bool(user_comment),
            "messages": ordered_messages,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-message-category")
def add_message_category(
    data: dict[str, Any] = Body(...),
    google_id: str = Depends(get_google_id),
    db: Session = Depends(get_db),
):
    try:
        ValidateData.validate_request_data(
            required_fields=["category_id", "message", "stars"],
            data=data,
        )
        message = MessageRepository(
            stars=data.get("stars"),
            message=data.get("message"),
            google_id=google_id,
            category_id=data.get("category_id"),
        )

        message_verify = message.verify()
        if message_verify is True:
            message.save()
            return {"message": "Menssage guardado"}
        return message_verify
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="error en el sistema")
