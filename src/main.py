"""
Punto de entrada FastAPI — reemplaza `app.py` (Flask).
Ejecutar: uvicorn main:app --host 0.0.0.0 --port 5002 --reload
(desde el directorio `src/`, con PYTHONPATH configurado).
"""
from __future__ import annotations

from contextlib import asynccontextmanager

import paypalrestsdk
from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from models import get_db
from routes import init_app


@asynccontextmanager
async def lifespan(app: FastAPI):
    paypalrestsdk.configure(
        {
            "mode": settings.PAYPAL_MODE,
            "client_id": settings.PAYPAL_CLIENT_ID,
            "client_secret": settings.PAYPAL_CLIENT_SECRET,
        }
    )
    yield


app = FastAPI(
    title="Cursos Estudia y Trabaja API",
    lifespan=lifespan,
    dependencies=[Depends(get_db)],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_app(app)


@app.exception_handler(HTTPException)
async def _compat_http_errors(request: Request, exc: HTTPException):
    """Compatibilidad con respuestas Flask / tests ISO."""
    detail = exc.detail
    msg = detail if isinstance(detail, str) else str(detail)

    if exc.status_code == 400:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": msg},
        )
    if exc.status_code == 404:
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": msg},
        )
    if exc.status_code in (401, 403):
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "error": msg},
        )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
