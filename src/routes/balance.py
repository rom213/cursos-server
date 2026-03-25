from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from servises.balance.balance_model import BalanceModel
from utils.auth import get_google_id

router = APIRouter(tags=["balance"])


@router.get("/balance")
def all_balance_categories(
    date_init: str = Query(...),
    date_end: str = Query(...),
    google_id: str = Depends(get_google_id),
    db: Session = Depends(get_db),
):
    try:
        dt_init = datetime.strptime(date_init, "%Y-%m-%d")
        dt_end = datetime.strptime(date_end, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)
    except ValueError:
        raise HTTPException(status_code=400, detail="Fechas inválidas. Usa formato YYYY-MM-DD")

    try:
        summary = BalanceModel.get_all_sales_by_me(
            google_id=google_id,
            date_init=dt_init,
            date_end=dt_end,
        )
        return {
            "count": summary["counts"],
            "non_refunded_value": summary["non_refunded_value"],
            "refunded_value": summary["refunded_value"],
            "total_value_all_refunds": summary["total_value"],
            "courses_payments_value": summary["courses_payments_value"],
            "list_ids_refers": summary["list_ids_refers"],
        }
    except Exception:
        raise HTTPException(status_code=200, detail="KO")


@router.get("/balance/user/{google_id_param}")
def all_balance_categories_by_google_id(
    google_id_param: str,
    date_init: str = Query(...),
    date_end: str = Query(...),
    db: Session = Depends(get_db),
):
    try:
        dt_init = datetime.strptime(date_init, "%Y-%m-%d")
        dt_end = datetime.strptime(date_end, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)
    except ValueError:
        raise HTTPException(status_code=400, detail="Fechas inválidas. Usa formato YYYY-MM-DD")

    try:
        summary = BalanceModel.get_all_sales_by_me(
            google_id=google_id_param,
            date_init=dt_init,
            date_end=dt_end,
        )
        return {
            "status": "success",
            "message": "OK",
            "records": [
                {
                    "count": summary["counts"],
                    "non_refunded_value": summary["non_refunded_value"],
                    "refunded_value": summary["refunded_value"],
                    "total_value_all_refunds": summary["total_value"],
                    "courses_payments_value": summary["courses_payments_value"],
                    "list_ids_refers": summary["list_ids_refers"],
                }
            ],
        }
    except Exception:
        return {"status": "ERROR", "message": "KO", "records": []}


@router.get("/balance/all")
def balance_categories(
    date_init: str = Query(...),
    date_end: str = Query(...),
    db: Session = Depends(get_db),
):
    try:
        dt_init = datetime.strptime(date_init, "%Y-%m-%d")
        dt_end = datetime.strptime(date_end, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)
    except ValueError:
        raise HTTPException(status_code=400, detail="Fechas inválidas. Usa formato YYYY-MM-DD")

    try:
        summary = BalanceModel.get_all_sales(date_init=dt_init, date_end=dt_end)
        return {
            "status": "success",
            "message": "OK",
            "records": [
                {
                    "count": summary["counts"],
                    "non_refunded_value": summary["non_refunded_value"],
                    "refunded_value": summary["refunded_value"],
                    "total_value_all_refunds": summary["total_value"],
                    "courses_payments_value": summary["courses_payments_value"],
                }
            ],
        }
    except Exception:
        return {"status": "ERROR", "message": "KO", "records": []}
