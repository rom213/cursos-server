from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from config import settings
from models import get_db
from servises.auth.auth_service import AuthService

router = APIRouter(tags=["auth"])


@router.post("/request-verification-code")
async def request_verification_code(db: Session = Depends(get_db)):
    _ = db
    email = settings.ADMIN_EMAIL
    try:
        await AuthService.generate_verification_code(email)
        return {"status": "success", "message": ""}
    except Exception as e:
        return {"status": "error", "message": str(e)}
