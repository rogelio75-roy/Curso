"""Motor y fábrica de sesiones de SQLAlchemy.

No crea esquema al importarse: el esquema se gestiona solo por migraciones de
Alembic (ver `docs/decisiones-ingenieria.md`).
"""

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import build_database_url


def make_engine() -> Engine:
    """Engine síncrono contra PostgreSQL, con la URL leída del entorno actual."""
    return create_engine(build_database_url(), future=True)


def make_sessionmaker(engine: Engine | None = None) -> sessionmaker[Session]:
    """Fábrica de sesiones ligada a `engine` (o a uno nuevo si no se pasa)."""
    return sessionmaker(
        bind=engine or make_engine(),
        autoflush=False,
        expire_on_commit=False,
    )
