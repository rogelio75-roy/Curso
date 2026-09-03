"""Comprobaciones de la construcción de la URL de PostgreSQL desde el entorno.

El Incremento 1 del plan exige que la URL se construya a partir de las variables
`POSTGRES_*` del entorno y no de valores incrustados en el código.
"""

import pytest
from sqlalchemy.engine import make_url

from app.config import build_database_url


def _env(**overrides: str) -> dict[str, str]:
    base = {
        "POSTGRES_USER": "u",
        "POSTGRES_PASSWORD": "p",
        "POSTGRES_DB": "d",
        "POSTGRES_HOST": "h",
        "POSTGRES_PORT": "6543",
    }
    base.update(overrides)
    return base


def test_url_se_construye_desde_el_entorno():
    url = make_url(build_database_url(_env()))
    assert url.drivername == "postgresql+psycopg"
    assert url.username == "u"
    assert url.password == "p"
    assert url.host == "h"
    assert url.port == 6543
    assert url.database == "d"


def test_host_por_defecto_es_localhost():
    env = _env()
    del env["POSTGRES_HOST"]
    assert make_url(build_database_url(env)).host == "localhost"


def test_puerto_por_defecto_es_5432():
    env = _env()
    del env["POSTGRES_PORT"]
    assert make_url(build_database_url(env)).port == 5432


def test_caracteres_reservados_en_password_se_escapan():
    env = _env(POSTGRES_PASSWORD="p@ss:w/rd#x")
    url = make_url(build_database_url(env))
    assert url.password == "p@ss:w/rd#x"
    assert url.host == "h"
    assert url.port == 6543


@pytest.mark.parametrize(
    "faltante", ["POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB"]
)
def test_falla_si_falta_una_variable_obligatoria(faltante: str):
    env = _env()
    del env[faltante]
    with pytest.raises(KeyError):
        build_database_url(env)
