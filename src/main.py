"""
Punto de entrada FastAPI — reemplaza `app.py` (Flask).
Ejecutar: uvicorn main:app --host 0.0.0.0 --port 5002 --reload
(desde el directorio `src/`, con PYTHONPATH configurado).
"""
from __future__ import annotations

from contextlib import asynccontextmanager

import paypalrestsdk
from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
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


app = FastAPI(title="Cursos Estudia y Trabaja API", lifespan=lifespan)

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
    """Compatibilidad con respuestas Flask: { success, error } en 401/403."""
    if exc.status_code in (401, 403):
        detail = exc.detail
        msg = detail if isinstance(detail, str) else str(detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "error": msg},
        )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
