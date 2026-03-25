from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from servises.sail.sail_model import ReferQueryService
from utils.auth import get_google_id

router = APIRouter(tags=["sail"])


def serialize_refer(refer):
    return {
        "porcetage_refund": refer.porcentage,
        "affiliaty": "manual",
        "category_bought": refer.payment.category.titulo,
        "category_price": refer.payment.price,
        "refund_price": refer.value,
        "created_at": refer.created_at,
        "is_refund": refer.refund is not None,
        "refer_id": refer.id,
        "baucher_image": refer.refund.image if refer.refund else None,
    }


@router.get("/sails")
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

    results = ReferQueryService.get_by_user_and_date(google_id, dt_init, dt_end)
    return [serialize_refer(ref) for ref in results]
