import io
import os
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import Float, desc, func
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models import db
from models.Refer import Refer
from models.User import User
from models.account import AccountType
from servises.auth.auth_service import AuthService
from servises.refer.refer_model import ReferModel
from servises.refund import refund_model
from servises.refund.mass_payment_service import MassPaymentService
from servises.Users.user_model import UserModel

router = APIRouter(tags=["managment"])

UPLOAD_DIRECTORY = os.path.join(os.getcwd(), "uploads")


# ==========================================
# SERIALIZERS
# ==========================================


def serialize_refer(refer) -> dict:
    user = User.query.filter_by(google_id=refer.google_id).first()
    return {
        "refund_id": refer.refund.id,
        "type_acc_em": refer.refund.type_acc_em.value,
        "porcetage_refund": refer.porcentage,
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
        "code_reference": refer.refund.code_reference,
    }


def serialize_refer_with_user(refer) -> dict:
    user = User.query.filter_by(google_id=refer.google_id).first()
    data: dict[str, Any] = {
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
            "porcetage_refund": refer.porcentage,
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
            "code_reference": refer.refund.code_reference,
        }
    return data


def serialize_refund_item(refund) -> dict:
    user = None
    google_id = None
    if refund.refers:
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
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in refund.refers
        ],
    }


# ==========================================
# HELPERS
# ==========================================


def validate_refer(referModel, form_data: dict) -> bool:
    refer = referModel.get_by_id(form_data["refer_id"])
    if refer is None:
        return False
    if refer.to_dict().get("refund"):
        return False
    return True


def get_refer_json(referModel, form_data: dict) -> dict:
    refer = referModel.get_by_id(form_data["refer_id"])
    return refer.to_dict()


async def save_img_from_upload(image: UploadFile) -> str | None:
    try:
        contents = await image.read()
        file_like = io.BytesIO(contents)
        validator = refund_model.PILImageValidator()
        image_service = refund_model.ImageStorageService(file_like, validator)
        return image_service.save()
    except Exception:
        return None


# ==========================================
# ROUTES
# ==========================================


@router.get("/refunds")
def get_refunds_by_date(
    date_init: str | None = Query(None),
    date_end: str | None = Query(None),
    search: str = Query(""),
    page: int = Query(1),
    per_page: int = Query(10, ge=1, le=100),
    db_session: Session = Depends(get_db),
):
    try:
        if not date_init or not date_end:
            raise HTTPException(
                status_code=400,
                detail="Las fechas date_init y date_end son obligatorias",
            )

        if page < 1:
            raise HTTPException(
                status_code=400,
                detail="El parámetro page debe ser mayor o igual a 1",
            )

        try:
            dt_init = datetime.strptime(date_init, "%Y-%m-%d")
            dt_end = datetime.strptime(date_end, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Formato de fecha inválido. Use YYYY-MM-DD",
            )

        if dt_init > dt_end:
            raise HTTPException(
                status_code=400,
                detail="La fecha de inicio no puede ser mayor a la fecha de fin",
            )

        result = refund_model.RefundQueryService.search_refunds(
            date_init=dt_init,
            date_end=dt_end,
            search_term=search.strip() if search.strip() else None,
            page=page,
            per_page=per_page,
        )

        return {
            "status": "success",
            "message": "OK",
            "records": [serialize_refund_item(ref) for ref in result["records"]],
            "pagination": {
                "total": result["total"],
                "pages": result["pages"],
                "current_page": result["current_page"],
                "per_page": result["per_page"],
                "has_next": result["has_next"],
                "has_prev": result["has_prev"],
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/refunds/{google_id}")
def get_refunds(
    google_id: str,
    date_init: str = Query(...),
    date_end: str = Query(...),
    db_session: Session = Depends(get_db),
):
    try:
        dt_init = datetime.strptime(date_init, "%Y-%m-%d")
        dt_end = datetime.strptime(date_end, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use YYYY-MM-DD")

    results = refund_model.RefundQueryService.get_refunds_by_google_id(
        google_id, dt_init, dt_end
    )
    return {
        "status": "success",
        "message": "OK",
        "records": [serialize_refer_with_user(ref) for ref in results],
    }


@router.get("/refund/{refund_id}")
def get_refund_by_id(refund_id: str, db_session: Session = Depends(get_db)):
    results = refund_model.RefundQueryService.get_refund_by_id(refund_id)
    return {
        "status": "success",
        "message": "OK",
        "records": [serialize_refer_with_user(ref) for ref in results],
    }


@router.post("/refunds", status_code=201)
async def create_refund(
    verification_code: str | None = Form(None),
    type_acc_em: str | None = Form(None),
    type_acc_re: str | None = Form(None),
    titular_acc_em: str | None = Form(None),
    titular_acc_res: str | None = Form(None),
    number_acc_em: str | None = Form(None),
    value: str | None = Form(None),
    code_reference: str | None = Form(None),
    refer_id: str | None = Form(None),
    image: UploadFile | None = File(None),
    db_session: Session = Depends(get_db),
):
    if not verification_code or not str(verification_code).strip():
        raise HTTPException(
            status_code=400,
            detail="Debe proporcionar el código de verificación",
        )

    is_valid, message = AuthService.verify_code(settings.ADMIN_EMAIL, verification_code)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)

    required_fields = {
        "type_acc_em": type_acc_em,
        "type_acc_re": type_acc_re,
        "titular_acc_em": titular_acc_em,
        "titular_acc_res": titular_acc_res,
        "number_acc_em": number_acc_em,
        "value": value,
        "code_reference": code_reference,
        "refer_id": refer_id,
    }
    missing = [k for k, v in required_fields.items() if v is None or str(v).strip() == ""]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Faltan campos requeridos: {', '.join(missing)}",
        )

    if image is None or not getattr(image, "filename", None):
        raise HTTPException(status_code=400, detail="La imagen es requerida")

    form_data = {
        "type_acc_em": type_acc_em,
        "type_acc_re": type_acc_re,
        "titular_acc_em": titular_acc_em,
        "titular_acc_res": titular_acc_res,
        "number_acc_em": number_acc_em,
        "value": value,
        "code_reference": code_reference,
        "refer_id": refer_id,
    }

    if not validate_refer(ReferModel, form_data):
        raise HTTPException(
            status_code=400,
            detail="Facilitar un id refer valido",
        )

    image_path = await save_img_from_upload(image)
    if image_path is None:
        raise HTTPException(status_code=400, detail="Error al guardar imagen")

    refer_json = get_refer_json(ReferModel, form_data)

    refund_data = {
        "type_acc_em": AccountType[type_acc_em],
        "type_acc_re": AccountType[type_acc_re],
        "titular_acc_em": titular_acc_em,
        "titular_acc_res": titular_acc_res,
        "code_reference": code_reference,
        "number_acc_em": number_acc_em,
        "value": refer_json.get("value"),
        "image": image_path,
    }

    refund_creator = refund_model.RefundCreator(refund_model.RefundRepository())
    refund = refund_creator.create_refund(refund_data)

    return {
        "status": "success",
        "message": "Refund created",
        "records": {
            "id": refund.id,
            "created_at": refund.created_at.isoformat(),
            "image": refund.image,
        },
    }


@router.post("/mass-payment", status_code=201)
async def create_mass_payment(
    verification_code: str | None = Form(None),
    google_id: str | None = Form(None),
    date_init: str | None = Form(None),
    date_end: str | None = Form(None),
    type_acc_em: str | None = Form(None),
    type_acc_re: str | None = Form(None),
    titular_acc_em: str | None = Form(None),
    titular_acc_res: str | None = Form(None),
    number_acc_res: str | None = Form(None),
    number_acc_em: str | None = Form(None),
    code_reference: str | None = Form(None),
    list_ids_refers: str | None = Form(None),
    image: UploadFile | None = File(None),
    db_session: Session = Depends(get_db),
):
    if not verification_code or not str(verification_code).strip():
        raise HTTPException(
            status_code=400,
            detail="Debe proporcionar el código de verificación",
        )

    is_valid, message = AuthService.verify_code(settings.ADMIN_EMAIL, verification_code)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)

    required_mass = {
        "google_id": google_id,
        "date_init": date_init,
        "date_end": date_end,
        "type_acc_em": type_acc_em,
        "type_acc_re": type_acc_re,
        "titular_acc_em": titular_acc_em,
        "titular_acc_res": titular_acc_res,
        "number_acc_res": number_acc_res,
        "number_acc_em": number_acc_em,
        "code_reference": code_reference,
        "list_ids_refers": list_ids_refers,
    }
    missing_mass = [k for k, v in required_mass.items() if v is None or str(v).strip() == ""]
    if missing_mass:
        raise HTTPException(
            status_code=400,
            detail=f"Faltan campos requeridos: {', '.join(missing_mass)}",
        )

    if image is None or not getattr(image, "filename", None):
        raise HTTPException(status_code=400, detail="La imagen es requerida")

    try:
        dt_init = datetime.strptime(date_init, "%Y-%m-%d")
        dt_end = datetime.strptime(date_end, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Formato de fecha inválido. Use YYYY-MM-DD"
        )

    image_path = await save_img_from_upload(image)
    if image_path is None:
        raise HTTPException(status_code=400, detail="Error al guardar imagen")

    try:
        refund_data = {
            "type_acc_em": AccountType[type_acc_em],
            "type_acc_re": AccountType[type_acc_re],
            "titular_acc_em": titular_acc_em,
            "titular_acc_res": titular_acc_res,
            "number_acc_em": number_acc_em,
            "number_acc_res": number_acc_res,
            "code_reference": code_reference,
            "image": image_path,
        }
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Invalid account type: {e}")

    result = MassPaymentService.process_mass_payment(
        google_id=google_id,
        refund_data=refund_data,
        list_ids_refers=list_ids_refers,
    )

    if result["status"] == "success":
        return result
    raise HTTPException(status_code=400, detail=result.get("message", "Error"))


@router.get("/uploads/{filename:path}")
def serve_uploaded_image(filename: str):
    file_path = os.path.join(UPLOAD_DIRECTORY, filename)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return FileResponse(file_path)


@router.get("/refers/unpaid")
def get_unpaid_refers(
    date_init: str = Query(...),
    date_end: str = Query(...),
    db_session: Session = Depends(get_db),
):
    try:
        dt_init = datetime.strptime(date_init, "%Y-%m-%d")
        dt_end = datetime.strptime(date_end, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use YYYY-MM-DD")

    refers = (
        Refer.query.filter(Refer.refund_id.is_(None))
        .filter(Refer.created_at >= dt_init)
        .filter(Refer.created_at <= dt_end)
        .all()
    )
    return {
        "status": "success",
        "message": "OK",
        "records": [serialize_refer_with_user(r) for r in refers],
    }


@router.get("/refers/paid")
def get_paid_refers(
    date_init: str = Query(...),
    date_end: str = Query(...),
    db_session: Session = Depends(get_db),
):
    try:
        dt_init = datetime.strptime(date_init, "%Y-%m-%d")
        dt_end = datetime.strptime(date_end, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use YYYY-MM-DD")

    refers = (
        Refer.query.filter(Refer.refund_id.isnot(None))
        .filter(Refer.created_at >= dt_init)
        .filter(Refer.created_at <= dt_end)
        .all()
    )
    return {
        "status": "success",
        "message": "OK",
        "records": [serialize_refer_with_user(r) for r in refers],
    }


@router.get("/refers/unpaid/{google_id}")
def get_unpaid_refer_by_google_id(google_id: str, db_session: Session = Depends(get_db)):
    refers = (
        Refer.query.filter(Refer.refund_id.is_(None))
        .filter(Refer.google_id == google_id)
        .all()
    )
    return {
        "status": "success",
        "message": "OK",
        "records": [serialize_refer_with_user(r) for r in refers],
    }


@router.get("/refers/paid/{google_id}")
def get_paid_refer_by_google_id(google_id: str, db_session: Session = Depends(get_db)):
    refers = (
        Refer.query.filter(Refer.refund_id.isnot(None))
        .filter(Refer.google_id == google_id)
        .all()
    )
    return {
        "status": "success",
        "message": "OK",
        "records": [serialize_refer_with_user(r) for r in refers],
    }


@router.get("/refer/{refer_id}")
def get_paid_refer_by_id(refer_id: str, db_session: Session = Depends(get_db)):
    refers = Refer.query.filter(Refer.id == refer_id).all()
    return {
        "status": "success",
        "message": "OK",
        "records": [serialize_refer_with_user(r) for r in refers],
    }


@router.get("/user/accounts/{googleid}")
def user_account_by_google_id(googleid: str, db_session: Session = Depends(get_db)):
    res = UserModel.get_accounts_by_google_id(googleid)

    if res is None:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado",
        )

    if not hasattr(res, "accounts") or not res.accounts:
        raise HTTPException(
            status_code=404,
            detail="El usuario no tiene cuentas registradas",
        )

    return {
        "status": "success",
        "message": "OK",
        "records": [[acc.to_dict() for acc in res.accounts]],
    }


@router.get("/users/pending-refunds")
def get_pending_refund_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db_session: Session = Depends(get_db),
):
    try:
        query = (
            db.session.query(
                User,
                func.sum(func.cast(Refer.value, Float)).label("total_owed"),
                func.count(Refer.id).label("refers_count"),
            )
            .join(Refer, User.google_id == Refer.google_id)
            .filter(Refer.refund_id.is_(None))
            .group_by(User.id)
            .order_by(desc(User.created_at))
        )

        total = query.count()
        pages = (total + per_page - 1) // per_page if per_page else 0
        items = query.offset((page - 1) * per_page).limit(per_page).all()

        records = [
            {
                "user": user.to_dict(),
                "total_owed": total_owed,
                "refers_count": refers_count,
            }
            for user, total_owed, refers_count in items
        ]

        return {
            "status": "success",
            "message": "OK",
            "records": [records],
            "pagination": {
                "total": total,
                "pages": pages,
                "current_page": page,
                "per_page": per_page,
                "has_next": page < pages,
                "has_prev": page > 1,
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}",
        )
