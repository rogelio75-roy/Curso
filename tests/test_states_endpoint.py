"""End-to-end de `GET /states` contra el PostgreSQL real de Compose.

Comprobación del Incremento 4:

- `GET /states` -> `200` con 4 elementos;
- orden estable entre dos llamadas idénticas;
- esquema exacto por estado (`{"id", "code"}`, ni un campo de más);
- no hay rutas de escritura (`POST/PUT/PATCH/DELETE`) sobre `/states`.

Requiere el servicio `db` de `compose.yaml` levantado y sano, con las migraciones
aplicadas (`uv run alembic upgrade head`).
"""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.config import build_database_url
from app.main import app

_REPO_ROOT = Path(__file__).resolve().parent.parent
_CATALOGO = ["PENDIENTE", "EN_CURSO", "BLOQUEADA", "HECHA"]


@pytest.fixture(scope="module")
def migrada():
    """Aplica las migraciones una vez para el módulo; las revierte al final."""
    eng = create_engine(build_database_url(), future=True)
    try:
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        eng.dispose()
        pytest.skip(f"PostgreSQL de Compose no disponible: {exc}")

    cfg = Config(str(_REPO_ROOT / "alembic.ini"))
    command.upgrade(cfg, "head")
    yield
    command.downgrade(cfg, "base")
    with eng.begin() as conn:
        for tabla in ("alembic_version",):
            conn.execute(text(f'DROP TABLE IF EXISTS "{tabla}" CASCADE'))
    eng.dispose()


@pytest.fixture
def client(migrada):
    with TestClient(app) as c:
        yield c


def test_get_states_devuelve_200_y_cuatro_elementos(client):
    resp = client.get("/states")
    assert resp.status_code == 200
    cuerpo = resp.json()
    assert isinstance(cuerpo, list)
    assert len(cuerpo) == 4


def test_get_states_orden_estable_entre_llamadas(client):
    primera = client.get("/states").json()
    segunda = client.get("/states").json()
    assert primera == segunda
    assert [s["code"] for s in primera] == _CATALOGO


def test_get_states_esquema_exacto(client):
    for estado in client.get("/states").json():
        assert set(estado) == {"id", "code"}
        assert isinstance(estado["id"], int)
        assert isinstance(estado["code"], str)


@pytest.mark.parametrize("metodo", ["post", "put", "patch", "delete"])
def test_states_no_admite_escritura(client, metodo):
    resp = getattr(client, metodo)("/states")
    assert resp.status_code in (404, 405)
