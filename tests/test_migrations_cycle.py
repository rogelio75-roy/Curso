"""Ciclo de migraciones contra el PostgreSQL real de Compose.

Comprobación del Incremento 2: `upgrade head` sobre una base vacía aplica todas
las revisiones y registra la cabeza en `alembic_version`; `downgrade base`
revierte todas las revisiones y deja la base sin tablas de dominio y sin
revisión aplicada.

Requiere el servicio `db` de `compose.yaml` levantado y sano
(`docker compose up -d`).
"""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text

from app.config import build_database_url

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCAFFOLDING = {"alembic_version"}


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


def _all_tables(engine) -> set[str]:
    return set(inspect(engine).get_table_names())


def _domain_tables(engine) -> set[str]:
    return _all_tables(engine) - _SCAFFOLDING


def _head_revision() -> str:
    return ScriptDirectory.from_config(
        Config(str(_REPO_ROOT / "alembic.ini"))
    ).get_current_head()


def _applied_revision(engine) -> str | None:
    if "alembic_version" not in _all_tables(engine):
        return None
    with engine.connect() as conn:
        return conn.execute(text("SELECT version_num FROM alembic_version")).scalar()


@pytest.fixture(autouse=True)
def base_limpia(engine, alembic_config):
    _reset_base(engine, alembic_config)
    yield
    _reset_base(engine, alembic_config)


def test_upgrade_head_sobre_base_vacia(engine, alembic_config):
    assert _all_tables(engine) == set()

    command.upgrade(alembic_config, "head")

    # El andamiaje existe y la revisión aplicada es la cabeza del árbol.
    assert "alembic_version" in _all_tables(engine)
    assert _applied_revision(engine) == _head_revision()


def test_downgrade_base_deja_la_base_limpia(engine, alembic_config):
    command.upgrade(alembic_config, "head")
    assert _applied_revision(engine) is not None

    command.downgrade(alembic_config, "base")

    # Ninguna tabla de dominio y ninguna revisión aplicada.
    assert _domain_tables(engine) == set()
    assert _applied_revision(engine) is None
