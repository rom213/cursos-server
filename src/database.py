"""
SQLAlchemy 2.0 — sesión por petición con ContextVar para compatibilidad con `db.session`
usado en servicios (migración desde Flask-SQLAlchemy).
"""
from __future__ import annotations

import contextvars
from contextlib import contextmanager
from typing import Any, Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config import settings


def _database_url() -> str:
    return (
        f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}"
        f"@{settings.MYSQL_HOST}/{settings.MYSQL_DB}?charset=utf8mb4"
    )


engine = create_engine(
    _database_url(),
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ContextVar: misma sesión que `get_db` dentro de cada petición
_session_ctx: contextvars.ContextVar[Optional[Session]] = contextvars.ContextVar(
    "db_session", default=None
)


class DBProxy:
    """Sustituye `db` de Flask-SQLAlchemy: `db.session` → sesión de la petición actual."""

    @property
    def session(self) -> Session:
        s = _session_ctx.get()
        if s is None:
            raise RuntimeError(
                "No hay sesión de base de datos en contexto. "
                "Use Depends(get_db) en la ruta o ejecute dentro de get_db()."
            )
        return s


db = DBProxy()


class QueryProperty:
    """Compatibilidad con `Model.query` (patrón Flask-SQLAlchemy)."""

    def __get__(self, instance: Any, owner: type) -> Any:
        if owner is None:
            return self
        return db.session.query(owner)


class Base(DeclarativeBase):
    query = QueryProperty()  # type: ignore[assignment]


def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()
    token = _session_ctx.set(session)
    try:
        yield session
    finally:
        _session_ctx.reset(token)
        session.close()


@contextmanager
def session_scope():
    """Para BackgroundTasks / workers: misma semántica que `db.session` + commit al salir."""
    session = SessionLocal()
    token = _session_ctx.set(session)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        _session_ctx.reset(token)
        session.close()
