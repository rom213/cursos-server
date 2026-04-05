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

import logging
import colorlog

from config import settings
from database import Base, DBSessionMiddleware, engine
import models  # noqa: F401 — registra todos los modelos en Base.metadata
from routes import init_app


def _setup_logging() -> None:
    handler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s%(levelname)-8s%(reset)s %(cyan)s%(name)s%(reset)s — %(message)s",
            log_colors={
                "DEBUG":    "white",
                "INFO":     "green",
                "WARNING":  "yellow",
                "ERROR":    "red",
                "CRITICAL": "bold_red",
            },
        )
    )
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()
    root.addHandler(handler)


_setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
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
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001","http://localhost:3000", "http://localhost:4173","http://192.168.1.24:3001","http://192.168.0.105:4173", "http://192.168.1.24:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(DBSessionMiddleware)

init_app(app)


@app.exception_handler(HTTPException)
async def _compat_http_errors(request: Request, exc: HTTPException):
    """Compatibilidad con respuestas Flask / tests ISO."""
    detail = exc.detail
    msg = detail if isinstance(detail, str) else str(detail)

    if exc.status_code == 400:
        return JSONResponse(
            status_code=400,
            content={   
                "success": False,
                "error": msg,
                "status": "error",
                "message": msg,
            },  
        )
    if exc.status_code == 404:
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "error": msg,
                "status": "error",
                "message": msg,
            },
        )
    if exc.status_code in (401, 403):
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "error": msg},
        )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


# 👇 AGREGA ESTO AL FINAL DEL ARCHIVO 👇
if __name__ == "__main__":
    import uvicorn
    
    # IMPORTANTE: Pasamos el objeto 'app' directamente, NO el string "main:app". 
    # Nuitka funciona mucho mejor pasando el objeto de la aplicación cuando está compilado.
    # Usamos el puerto 5002 que tenías en tus comentarios.
    uvicorn.run(app, host="0.0.0.0", port=5002)