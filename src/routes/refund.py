from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from servises.refund import refund_model
from utils.auth import get_google_id

router = APIRouter(tags=["refund"])


def serialize_refer(refer):
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
        "code_reference": refer.refund.code_reference,
    }


@router.get("/refunds")
def get_refunds_by_user_and_date(
    date_init: str = Query(...),
    date_end: str = Query(...),
    google_id: str = Depends(get_google_id),
    db: Session = Depends(get_db),
):
    if not date_init or not date_end:
        raise HTTPException(status_code=400, detail="Faltan parámetros requeridos")

    try:
        dt_init = datetime.fromisoformat(date_init)
        dt_end = datetime.fromisoformat(date_end)
    except ValueError:
        raise HTTPException(status_code=400, detail="Fechas inválidas. Usa formato YYYY-MM-DD")

    results = refund_model.RefundQueryService.get_by_user_and_date(google_id, dt_init, dt_end)
    return [serialize_refer(ref) for ref in results]
