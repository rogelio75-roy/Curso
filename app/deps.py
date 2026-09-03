"""Dependencias de FastAPI para el acceso a datos.

El engine se crea en el arranque de la app (`lifespan` en `app.main`), no al
importar este módulo.
"""

from collections.abc import Iterator

from sqlalchemy.orm import Session, sessionmaker

_sessionmaker: sessionmaker[Session] | None = None


def set_sessionmaker(factory: sessionmaker[Session] | None) -> None:
    """Fija (o limpia) la fábrica de sesiones que usará `get_session`."""
    global _sessionmaker
    _sessionmaker = factory


def get_session() -> Iterator[Session]:
    if _sessionmaker is None:
        raise RuntimeError("La fábrica de sesiones no está inicializada.")
    session = _sessionmaker()
    try:
        yield session
    finally:
        session.close()
