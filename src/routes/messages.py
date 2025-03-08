from flask import Blueprint, request, jsonify, session
from servises.messages.message_model import  MessageModel
from servises.request.validate_data import ValidateData
from servises.Users.user_repository import UserRepository
from servises.messages.message_repository import MessageRepository

message_bp = Blueprint("messages", __name__)


@message_bp.route("/all-messages/<int:id>", methods=["GET"])
def allMessagesByCategory(id):
    try:
        messages = MessageModel.get_by_category_id(id)

        if "user" not in session:
            return jsonify({
                "is_login": False,
                "is_comment": False,
                "messages": sorted([msg.to_dict() for msg in messages], key=lambda x: x["stars"], reverse=True)
            }), 200

        user_google_id = session["user"]["google_id"]
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

        return jsonify({
            "is_login": True,
            "is_comment": bool(user_comment),
            "messages": ordered_messages
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@message_bp.route("/add-message-category", methods=["POST"])
def payu_confirmation():
    try:
        is_login = UserRepository.verify_seccion()
        if is_login is False:
            return jsonify({"success": False, "error": "No ha iniciado sesión"}), 401

        required_fields = ["category_id", "message", "stars"]
        data, error = ValidateData.validate_request_data(required_fields=required_fields)
        if error:
            return error
        
        user_data = session.get("user")
        message = MessageRepository(stars=data.get("stars"), message=data.get("message"), google_id=user_data.get("google_id"), category_id=data.get("category_id"))
        
        message_verify=message.verify()
        
        if message_verify is True:
            message.save()
            return jsonify({"message": "Menssage guardado"}), 200
        return message_verify
    except:
        return jsonify({"message": "error en el sistema"}), 500
