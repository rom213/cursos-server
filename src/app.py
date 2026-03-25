"""
Compatibilidad: la aplicación principal es FastAPI (`main.py` / `main:app`).
Ejecutar desde `src/`:

  uvicorn main:app --host 0.0.0.0 --port 5002 --reload
"""
from main import app  # noqa: F401
