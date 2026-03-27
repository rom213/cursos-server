"""
SQLAlchemy 2.0 — sesion por peticion con ContextVar (compatible con async/sync handlers y workers).
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Generator

import pymysql.err
from sqlalchemy import create_engine, event
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
    pool_recycle=1800,
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG,
)


_PYMYSQL_DISCONNECT_CODES = {
    2006,   # MySQL server has gone away
    2013,   # Lost connection to MySQL server during query
    2055,   # Lost connection to MySQL server at '%s', system error: %d
}


@event.listens_for(engine, "handle_error")
def _handle_db_protocol_error(ctx) -> None:
    """Descarta del pool conexiones con errores de protocolo o desconexion MySQL."""
    exc = ctx.original_exception
    if isinstance(exc, (pymysql.err.InternalError, pymysql.err.InterfaceError)):
        ctx.is_disconnect = True
    elif isinstance(exc, pymysql.err.OperationalError):
        code = exc.args[0] if exc.args else None
        if code in _PYMYSQL_DISCONNECT_CODES:
            ctx.is_disconnect = True


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

_current_session: ContextVar[Session | None] = ContextVar("_current_session", default=None)


class DBProxy:
    """Sustituye `db` de Flask-SQLAlchemy: `db.session` -> sesion de la peticion actual."""

    @property
    def session(self) -> Session:
        s = _current_session.get()
        if s is None:
            raise RuntimeError(
                "No hay sesion de base de datos en contexto. "
                "Asegurese de que DBSessionMiddleware esta activo."
            )
        return s


db = DBProxy()


class QueryProperty:
    """Compatibilidad con `Model.query` (patron Flask-SQLAlchemy)."""

    def __get__(self, instance: Any, owner: type) -> Any:
        if owner is None:
            return self
        return db.session.query(owner)


class Base(DeclarativeBase):
    query = QueryProperty()  # type: ignore[assignment]


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency. Si el middleware ya establecio una sesion, la reutiliza.
    Si no, crea una propia (fallback para CLI, scripts o tests directos).
    """
    s = _current_session.get()
    if s is not None:
        yield s
    else:
        session = SessionLocal()
        token = _current_session.set(session)
        try:
            yield session
        finally:
            _current_session.reset(token)
            session.close()


@contextmanager
def session_scope():
    """Para BackgroundTasks / workers: crea su propia sesion aislada con commit al salir."""
    session = SessionLocal()
    token = _current_session.set(session)
    try:
        yield session
        if session.is_active:
            session.commit()
        else:
            session.rollback()
    except Exception:
        try:
            session.rollback()
        except Exception:
            pass
        raise
    finally:
        _current_session.reset(token)
        session.close()


class DBSessionMiddleware:
    """
    ASGI middleware: crea una sesion SQLAlchemy por peticion HTTP
    y la almacena en un ContextVar visible para todos los handlers sync/async.
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        session = SessionLocal()
        token = _current_session.set(session)
        try:
            await self.app(scope, receive, send)
        finally:
            _current_session.reset(token)
            session.close()
