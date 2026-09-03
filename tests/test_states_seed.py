"""Migración del catálogo de estados: tabla + seed idempotente.

Comprobación del Incremento 3, contra el PostgreSQL real de Compose:

- tras `upgrade head`, `states` tiene exactamente los 4 códigos del contrato;
- correr el seed dos veces no duplica filas;
- `downgrade` elimina la tabla y `upgrade` la reconstruye idéntica.

Requiere el servicio `db` de `compose.yaml` levantado y sano.
"""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text

from app.config import build_database_url

_REPO_ROOT = Path(__file__).resolve().parent.parent

# Catálogo cerrado del contrato, en su orden natural (docs/contrato-api.md §Estados).
_CATALOGO = ["PENDIENTE", "EN_CURSO", "BLOQUEADA", "HECHA"]


@pytest.fixture
def engine():
    eng = create_engine(build_database_url(), future=True)
    try:
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        eng.dispose()
        pytest.skip(f"PostgreSQL de Compose no disponible: {exc}")
    yield eng
    eng.dispose()


@pytest.fixture
def alembic_config() -> Config:
    return Config(str(_REPO_ROOT / "alembic.ini"))


def _reset_base(engine, alembic_config) -> None:
    """Deja la base sin ninguna tabla: revierte y borra todo lo que quede."""
    command.downgrade(alembic_config, "base")
    with engine.begin() as conn:
        for tabla in inspect(conn).get_table_names():
            conn.execute(text(f'DROP TABLE IF EXISTS "{tabla}" CASCADE'))


@pytest.fixture(autouse=True)
def base_limpia(engine, alembic_config):
    _reset_base(engine, alembic_config)
    yield
    _reset_base(engine, alembic_config)


def _rows(engine) -> list[tuple[int, str, int]]:
    with engine.connect() as conn:
        return list(
            conn.execute(
                text("SELECT id, code, position FROM states ORDER BY position, id")
            )
        )


def _run_seed_again(engine) -> None:
    """Re-ejecuta el bloque de seed de la revisión cabeza."""
    script = ScriptDirectory.from_config(Config(str(_REPO_ROOT / "alembic.ini")))
    head = script.get_revision(script.get_current_head())
    with engine.begin() as conn:
        head.module.seed_states(conn)


def test_upgrade_head_crea_los_cuatro_codigos(engine, alembic_config):
    command.upgrade(alembic_config, "head")

    assert "states" in inspect(engine).get_table_names()
    codigos = [code for _id, code, _pos in _rows(engine)]
    assert codigos == _CATALOGO


def test_columnas_y_restricciones_de_states(engine, alembic_config):
    command.upgrade(alembic_config, "head")

    cols = {c["name"]: c for c in inspect(engine).get_columns("states")}
    assert set(cols) == {"id", "code", "position"}
    assert cols["code"]["nullable"] is False
    assert cols["position"]["nullable"] is False

    uniques = inspect(engine).get_unique_constraints("states")
    unique_cols = {tuple(u["column_names"]) for u in uniques}
    pk_cols = tuple(inspect(engine).get_pk_constraint("states")["constrained_columns"])
    assert pk_cols == ("id",)
    assert ("code",) in unique_cols


def test_seed_es_idempotente(engine, alembic_config):
    command.upgrade(alembic_config, "head")
    antes = _rows(engine)

    _run_seed_again(engine)

    assert _rows(engine) == antes
    assert len(_rows(engine)) == len(_CATALOGO)


def test_downgrade_elimina_la_tabla_y_upgrade_la_reconstruye(engine, alembic_config):
    command.upgrade(alembic_config, "head")
    original = _rows(engine)
    assert original  # no vacío

    command.downgrade(alembic_config, "base")
    assert "states" not in inspect(engine).get_table_names()

    command.upgrade(alembic_config, "head")
    assert _rows(engine) == original
