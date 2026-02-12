from flask import Blueprint, request, jsonify, session, send_from_directory
from datetime import datetime
from servises.refund import refund_model
from servises.refer.refer_model import ReferModel
from servises.refund.mass_payment_service import MassPaymentService
from models.account import AccountType
from models.Refer import Refer
from models.User import User
from models.account import Account
from datetime import datetime, timedelta
from servises.auth.auth_service import AuthService
from servises.Users.user_model import UserModel
import os
from sqlalchemy import func, desc
from models import db

managmentAdmin_bp = Blueprint("managmentAdmin_bp", __name__)
UPLOAD_DIRECTORY = os.path.join(os.getcwd(), "uploads")



def serialize_refer(refer):
        user = User.query.filter_by(google_id=refer.google_id).first()
        return {
            "refund_id": refer.refund.id,
            "type_acc_em": refer.refund.type_acc_em.value,
            "porcetage_refund":refer.porcentage,
            "titular_acc_em": refer.refund.titular_acc_em,
            "number_acc_em": refer.refund.number_acc_em,
            "type_acc_re": refer.refund.type_acc_re.value,
            "titular_acc_res": refer.refund.titular_acc_em,
            "number_acc_res": refer.refund.number_acc_em,
            "value": refer.value,
            "image": refer.refund.image,
            "created_at": refer.refund.created_at.isoformat(),
            "refer_id": refer.id,
            "google_id": refer.google_id,
            "user": user.to_dict() if user else None,
            "code_reference": refer.refund.code_reference
        }


def serialize_refer_with_user(refer):
    user = User.query.filter_by(google_id=refer.google_id).first()
    data = {
        "refer_id": refer.id,
        "google_id": refer.google_id,
        "porcentage": refer.porcentage,
        "value": refer.value,
        "is_pay": refer.is_pay,
        "created_at": refer.created_at.isoformat() if refer.created_at else None,
        "user": user.to_dict() if user else None,
    }
    if refer.refund:
        data["refund"] = {
            "refund_id": refer.refund.id,
            "type_acc_em": refer.refund.type_acc_em.value,
            "porcetage_refund":refer.porcentage,
            "titular_acc_em": refer.refund.titular_acc_em,
            "number_acc_em": refer.refund.number_acc_em,
            "type_acc_re": refer.refund.type_acc_re.value,
            "titular_acc_res": refer.refund.titular_acc_em,
            "number_acc_res": refer.refund.number_acc_em,
            "value": refer.value,
            "image": refer.refund.image,
            "created_at": refer.refund.created_at.isoformat(),
            "refer_id": refer.id,
            "google_id": refer.google_id,
            "code_reference": refer.refund.code_reference
        }
    return data

def serialize_refund_item(refund):
    # Get user from the first refer (assuming all refers in a refund belong to same user)
    user = None
    google_id = None
    if refund.refers and len(refund.refers) > 0:
        google_id = refund.refers[0].google_id
        user = User.query.filter_by(google_id=google_id).first()
    
    return {
        "refund_id": refund.id,
        "type_acc_re": refund.type_acc_re.value if refund.type_acc_re else None,
        "titular_acc_res": refund.titular_acc_res,
        "number_acc_res": refund.number_acc_res,
        "titular_acc_em": refund.titular_acc_em,
        "type_acc_em": refund.type_acc_em.value if refund.type_acc_em else None,
        "number_acc_em": refund.number_acc_em,
        "value": refund.value,
        "image": refund.image,
        "created_at": refund.created_at.isoformat(),
        "code_reference": refund.code_reference,
        "user": user.to_dict() if user else None,
        "google_id": google_id,
        "refers": [
            {
                "refer_id": r.id,
                "value": r.value,
                "google_id": r.google_id,
                "porcentage": r.porcentage,
                "valor_curso": r.payment.price,
                "created_at": r.created_at.isoformat() if r.created_at else None
            } for r in refund.refers
        ]
    }
        
        
def validate_refer(referModel, form):
    refer = referModel.get_by_id(form["refer_id"])
    
    if refer is None:
      return False
  
    refer_to_dic=refer.to_dict()
    if refer_to_dic.get('refund'):
        return False
    
    return True



def save_img(image_file):
    try:
        validator = refund_model.PILImageValidator()
        image_service = refund_model.ImageStorageService(image_file, validator)
        image_path = image_service.save()
        return image_path
    except Exception as e:
        return None
    
def get_refer_json(referModel, form):
    refer = referModel.get_by_id(form["refer_id"])
    return refer.to_dict()
    


@managmentAdmin_bp.route("/refunds", methods=["GET"])
def get_refunds_by_date():
    """
    Endpoint para obtener reembolsos por fecha con búsqueda y paginación
    
    Query params:
        - date_init (required): Fecha inicio en formato YYYY-MM-DD
        - date_end (required): Fecha fin en formato YYYY-MM-DD
        - search (optional): Término de búsqueda
        - page (optional): Número de página (default: 1)
        - per_page (optional): Elementos por página (default: 10)
    """
    try:
        # Obtener parámetros
        date_init_str = request.args.get("date_init")
        date_end_str = request.args.get("date_end")
        search_term = request.args.get("search", "").strip()
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        
        # Validar parámetros requeridos
        if not all([date_init_str, date_end_str]):
            return jsonify({
                "status": "error",
                "message": "Faltan parámetros requeridos: date_init y date_end",
                "records": []
            }), 400

        # Validar paginación
        if page < 1:
            return jsonify({
                "status": "error",
                "message": "El número de página debe ser mayor a 0",
                "records": []
            }), 400
        
        if per_page < 1 or per_page > 100:
            return jsonify({
                "status": "error",
                "message": "per_page debe estar entre 1 y 100",
                "records": []
            }), 400
        
        # Parsear fechas
        try:
            date_init = datetime.strptime(date_init_str, "%Y-%m-%d")
            date_end = datetime.strptime(date_end_str, "%Y-%m-%d")
        except ValueError:
            return jsonify({
                "status": "error",
                "message": "Formato de fecha inválido. Use YYYY-MM-DD",
                "records": []
            }), 400
        
        # Validar rango de fechas
        if date_init > date_end:
            return jsonify({
                "status": "error",
                "message": "La fecha de inicio no puede ser mayor a la fecha de fin",
                "records": []
            }), 400
        
        # Realizar búsqueda con paginación
        result = refund_model.RefundQueryService.search_refunds(
            date_init=date_init,
            date_end=date_end,
            search_term=search_term if search_term else None,
            page=page,
            per_page=per_page
        )
        
        
        # Serializar resultados
        # Serializar resultados
        serialized_records = [serialize_refund_item(ref) for ref in result["records"]]
        
        return jsonify({
            "status": "success",
            "message": "OK",
            "records": serialized_records,
            "pagination": {
                "total": result["total"],
                "pages": result["pages"],
                "current_page": result["current_page"],
                "per_page": result["per_page"],
                "has_next": result["has_next"],
                "has_prev": result["has_prev"]
            }
        }), 200
        
    except Exception as e:
        # Log del error
        print(f"Error en get_refunds_by_date: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Error interno del servidor: {str(e)}",
            "records": []
        }), 500



@managmentAdmin_bp.route("/refunds/<google_id>", methods=["GET"])
def get_refunds(google_id):

    date_init_str = request.args.get("date_init")
    date_end_str = request.args.get("date_end")

    date_init = datetime.strptime(date_init_str, "%Y-%m-%d")
    date_end = datetime.strptime(date_end_str, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)


    if google_id is None:
        return jsonify({"status": "error", "message": "debes proporcionar un id valido", "records": []}), 401
    results = refund_model.RefundQueryService.get_refunds_by_google_id(google_id, date_init, date_end)

    return jsonify({"status": "success", "message": "OK", "records": [serialize_refer_with_user(ref) for ref in results]}), 200




@managmentAdmin_bp.route("/refund/<refund_id>", methods=["GET"])
def get_refund_by_id(refund_id):
    if refund_id is None:
        return jsonify({"status": "error", "message": "debes proporcionar un id valido", "records": []}), 401
    results = refund_model.RefundQueryService.get_refund_by_id(refund_id)
    return jsonify({"status": "success", "message": "OK", "records": [serialize_refer_with_user(ref) for ref in results]}), 200




@managmentAdmin_bp.route("/refunds", methods=["POST"])
def create_refund():
    form = request.form
    image_file = request.files.get("image")
    verification_code = form.get("verification_code")

    if not verification_code:
        return jsonify({"status": "error", "message": "Falta el código de verificación"}), 400

    # Verify code
    from flask import current_app
    email = current_app.config.get("ADMIN_EMAIL")
    is_valid, message = AuthService.verify_code(email, verification_code)
    if not is_valid:
        return jsonify({"status": "error", "message": message}), 400

    # Validación de campos requeridos
    required_fields = [
        "type_acc_em", "type_acc_re", "titular_acc_em", "titular_acc_res",
        "number_acc_em", "value", "code_reference", "refer_id"
    ]

    missing = [f for f in required_fields if f not in form]
    if missing or not image_file:
        return jsonify({"status": "error", "message": f"Faltan campos: {missing} o imagen", "records": None}), 400


    is_validated=validate_refer(ReferModel, form)

    if is_validated==False:
        return jsonify({"status": "error", "message": "Facilitar un id refer valido", "records": None}), 400


    image_path = save_img(image_file)
    if image_path==None:
        return jsonify({"status": "error", "message": "Error al guardar imagen", "records": None}), 400

    refer_json=get_refer_json(ReferModel, form)

    refund_data = {
        "type_acc_em": AccountType[form["type_acc_em"]],
        "type_acc_re": AccountType[form["type_acc_re"]],
        "titular_acc_em": form["titular_acc_em"],
        "titular_acc_res": form["titular_acc_res"],
        "code_reference": form["code_reference"],
        "number_acc_em": form["number_acc_em"],
        "value": refer_json.get('value'),
        "image": image_path
    }

    refund_creator = refund_model.RefundCreator(refund_model.RefundRepository())

    refund = refund_creator.create_refund(refund_data)


    return jsonify({
        "status": "success",
        "message": "Refund created",
        "records": {
            "id": refund.id,
            "created_at": refund.created_at.isoformat(),
            "image": refund.image
        }
    }), 201


@managmentAdmin_bp.route("/mass-payment", methods=["POST"])
def create_mass_payment():
    form = request.form
    image_file = request.files.get("image")
    verification_code = form.get("verification_code")
    if not verification_code:
        return jsonify({"status": "error", "message": "Falta el código de verificación"}), 400
    from flask import current_app
    email = current_app.config.get("ADMIN_EMAIL")
    is_valid, message = AuthService.verify_code(email, verification_code)
    if not is_valid:
        return jsonify({"status": "error", "message": message}), 400
    
    
    required_fields = [
        "google_id", "date_init", "date_end", 
        "type_acc_em", "type_acc_re", "titular_acc_em", "titular_acc_res", "number_acc_res",
        "number_acc_em", "code_reference"
    ]
    
    missing = [f for f in required_fields if f not in form]
    if missing or not image_file:
        return jsonify({"status": "error", "message": f"Faltan campos: {missing} o imagen"}), 400
        
    try:
        date_init = datetime.strptime(form["date_init"], "%Y-%m-%d")
        date_end = datetime.strptime(form["date_end"], "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)
    except ValueError:
        return jsonify({"status": "error", "message": "Formato de fecha inválido. Use YYYY-MM-DD"}), 400
        
    image_path = save_img(image_file)
    if image_path is None:
        return jsonify({"status": "error", "message": "Error al guardar imagen"}), 400
        
    try:
        refund_data = {
            "type_acc_em": AccountType[form["type_acc_em"]],
            "type_acc_re": AccountType[form["type_acc_re"]],
            "titular_acc_em": form["titular_acc_em"],
            "titular_acc_res": form["titular_acc_res"],
            "number_acc_em": form["number_acc_em"],
            "number_acc_res": form["number_acc_res"],
            "code_reference": form["code_reference"],
            "image": image_path
        }
    except KeyError as e:
        return jsonify({"status": "error", "message": f"Invalid account type: {e}"}), 400
    
    result = MassPaymentService.process_mass_payment(
        google_id=form["google_id"],
        refund_data=refund_data,
        list_ids_refers=form["list_ids_refers"]
    )
    
    if result["status"] == "success":
        return jsonify(result), 201
    else:
        return jsonify(result), 400




@managmentAdmin_bp.route('/uploads/<path:filename>')
def serve_uploaded_image(filename):
    """
    Esta ruta sirve los archivos desde el directorio UPLOAD_DIRECTORY.
    El navegador podrá acceder a las imágenes usando una URL como:
    http://127.0.0.1:5000/uploads/nombre_del_archivo.jpg
    """
    return send_from_directory(UPLOAD_DIRECTORY, filename)



@managmentAdmin_bp.route("/refers/unpaid", methods=["GET"])
def get_unpaid_refers():
    date_init_str = request.args.get("date_init")
    date_end_str = request.args.get("date_end")

    date_init = datetime.strptime(date_init_str, "%Y-%m-%d")
    date_end = datetime.strptime(date_end_str, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)

    refers = Refer.query.filter(Refer.refund_id == None)\
    .filter(Refer.created_at >= date_init) \
    .filter(Refer.created_at <= date_end) \
    .all()

    return jsonify({"status": "success", "message": "OK", "records": [serialize_refer_with_user(r) for r in refers]}), 200


@managmentAdmin_bp.route("/refers/paid", methods=["GET"])
def get_paid_refers():
    date_init_str = request.args.get("date_init")
    date_end_str = request.args.get("date_end")

    date_init = datetime.strptime(date_init_str, "%Y-%m-%d")
    date_end = datetime.strptime(date_end_str, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)

    refers = Refer.query.filter(Refer.refund_id != None)\
    .filter(Refer.created_at >= date_init) \
    .filter(Refer.created_at <= date_end) \
    .all()
    return jsonify({"status": "success", "message": "OK", "records": [serialize_refer_with_user(r) for r in refers]}), 200


@managmentAdmin_bp.route("/refers/unpaid/<google_id>", methods=["GET"])
def get_unpaid_refer_by_google_id(google_id):
    refers = Refer.query.filter(Refer.refund_id == None)\
    .filter(Refer.google_id==google_id)\
    .all()
    return jsonify({"status": "success", "message": "OK", "records": [serialize_refer_with_user(r) for r in refers]}), 200


@managmentAdmin_bp.route("/refers/paid/<google_id>", methods=["GET"])
def get_paid_refer_by_google_id(google_id):
    refers = Refer.query.filter(Refer.refund_id != None)\
    .filter(Refer.google_id==google_id)\
    .all()
    return jsonify({"status": "success", "message": "OK", "records": [serialize_refer_with_user(r) for r in refers]}), 200

@managmentAdmin_bp.route("/refer/<refer_id>", methods=["GET"])
def get_paid_refer_by_id(refer_id):
    refers = Refer.query\
    .filter(Refer.id==refer_id)\
    .all()
    return jsonify({"status": "success", "message": "OK", "records": [serialize_refer_with_user(r) for r in refers]}), 200

@managmentAdmin_bp.route("/user/accounts/<googleid>", methods=["GET"])
def user_account_by_google_id(googleid):
    res=UserModel.get_accounts_by_google_id(googleid)
    
    # Validar que el usuario existe
    if res is None:
        return jsonify({
            "status": "error",
            "message": "Usuario no encontrado",
            "records": []
        }), 404
    
    # Validar que el usuario tiene cuentas registradas
    if not hasattr(res, 'accounts') or not res.accounts:
        return jsonify({
            "status": "error",
            "message": "El usuario no tiene cuentas registradas",
            "records": []
        }), 404
    
    return jsonify({
        "status": "success",
        "message": "OK",
        "records": [[acc.to_dict() for acc in res.accounts]]
    }), 200


@managmentAdmin_bp.route("/users/pending-refunds", methods=["GET"])
def get_pending_refund_users():
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)

        query = db.session.query(
            User,
            func.sum(func.cast(Refer.value, db.Float)).label("total_owed"),
            func.count(Refer.id).label("refers_count")
        ).join(Refer, User.google_id == Refer.google_id)\
         .filter(Refer.refund_id == None)\
         .group_by(User.id)\
         .order_by(desc(User.created_at))

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        records = []
        for user, total_owed, refers_count in pagination.items:
            records.append({
                "user": user.to_dict(),
                "total_owed": total_owed,
                "refers_count": refers_count
            })

        return jsonify({
            "status": "success",
            "message": "OK",
            "records": [records],
            "pagination": {
                "total": pagination.total,
                "pages": pagination.pages,
                "current_page": pagination.page,
                "per_page": pagination.per_page,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev
            }
        }), 200
    except Exception as e:
        print(f"Error in get_pending_refund_users: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Error interno del servidor: {str(e)}",
            "records": []
        }), 500
