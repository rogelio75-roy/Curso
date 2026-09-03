"""crea la tabla states y siembra el catalogo

Revision ID: 0b1b461bb5d6
Revises: 06d7fb2bda34
Create Date: 2026-08-31 20:46:21.872704

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import insert

# revision identifiers, used by Alembic.
revision: str = "0b1b461bb5d6"
down_revision: str | Sequence[str] | None = "06d7fb2bda34"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Catálogo cerrado del contrato (docs/contrato-api.md §Estados), en su orden.
_CATALOGO = ("PENDIENTE", "EN_CURSO", "BLOQUEADA", "HECHA")

_states = sa.table(
    "states",
    sa.column("code", sa.String),
    sa.column("position", sa.Integer),
)


def seed_states(bind: sa.engine.Connection) -> None:
    """Inserta el catálogo cerrado. Idempotente: repetirlo no cambia nada."""
    filas = [
        {"code": code, "position": pos}
        for pos, code in enumerate(_CATALOGO, start=1)
    ]
    stmt = insert(_states).values(filas)
    stmt = stmt.on_conflict_do_nothing(index_elements=["code"])
    bind.execute(stmt)


def upgrade() -> None:
    op.create_table(
        "states",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(length=32), nullable=False, unique=True),
        sa.Column("position", sa.Integer, nullable=False, unique=True),
    )
    seed_states(op.get_bind())


def downgrade() -> None:
    op.drop_table("states")
