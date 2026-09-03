"""Modelos ORM mapeados a las tablas que crean las migraciones de Alembic.

Estas clases no crean ni alteran esquema: solo describen tablas que ya existen.
"""

from sqlalchemy import Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class State(Base):
    """Catálogo cerrado de estados. Solo lectura desde la API."""

    __tablename__ = "states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
