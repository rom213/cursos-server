from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from servises.account.account_repository import AccountRepository
from servises.Users.user_model import UserModel
from utils.auth import get_google_id

router = APIRouter(tags=["account"])


@router.post("/update")
def update(
    data: dict[str, Any] = Body(...),
    google_id: str = Depends(get_google_id),
    db: Session = Depends(get_db),
):
    try:
        cuentas = ["nequi", "daviplata", "llave"]

        for cuenta in cuentas:
            numero = data.get(cuenta)
            if numero and numero != "null":
                acc = AccountRepository(
                    name_account=cuenta, number_account=numero, google_id=google_id
                )
                account_exist = acc.is_exists()
                if account_exist:
                    account_exist.update(number_acc=numero)
                else:
                    acc.save()

        cellphone = data.get("cellphone")
        if cellphone and cellphone != "null":
            user = UserModel.get_by_google_id(google_id=google_id)
            user.update(num_whatsapp=cellphone)

        # Update codigo_referido if provided
        codigo_referido = data.get("codigo_referido")
        if codigo_referido and codigo_referido != "null":
            user = UserModel.get_by_google_id(google_id=google_id)
            user.update(codigo_referido=codigo_referido)

        return {"status": "succes"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=501, detail="no succes")
