from fastapi import FastAPI

from .users import router as users_router
from .payments import router as payments_router
from .groups import router as groups_router
from .messages import router as messages_router
from .category import router as category_router
from .account import router as account_router
from .refund import router as refund_router
from .balance import router as balance_router
from .sail import router as sail_router
from .managmentAdmin import router as managment_router
from .auth import router as auth_router


def init_app(app: FastAPI) -> None:
    app.include_router(users_router)
    app.include_router(payments_router)
    app.include_router(messages_router)
    app.include_router(category_router, prefix="/api/category")
    app.include_router(groups_router, prefix="/api/groups")
    app.include_router(account_router, prefix="/account")
    app.include_router(refund_router, prefix="/api")
    app.include_router(balance_router, prefix="/api")
    app.include_router(sail_router, prefix="/api")
    app.include_router(managment_router, prefix="/api/managment")
    app.include_router(auth_router, prefix="/api/auth")
