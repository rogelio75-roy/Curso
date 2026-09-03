"""Configuración de conexión a PostgreSQL.

La URL de la base se construye a partir de las variables de entorno `POSTGRES_*`
(ver `.env.example`). No hay valores reales en el código.
"""

from collections.abc import Mapping
from os import environ

from sqlalchemy.engine import URL

DRIVER = "postgresql+psycopg"


def build_database_url(env: Mapping[str, str] | None = None) -> str:
    """Devuelve la URL SQLAlchemy para PostgreSQL a partir del entorno.

    `POSTGRES_USER`, `POSTGRES_PASSWORD` y `POSTGRES_DB` son obligatorias.
    `POSTGRES_HOST` (por defecto `localhost`) y `POSTGRES_PORT` (por defecto
    `5432`) son opcionales. Cada componente se codifica de forma segura.
    """
    src = environ if env is None else env
    url = URL.create(
        DRIVER,
        username=src["POSTGRES_USER"],
        password=src["POSTGRES_PASSWORD"],
        host=src.get("POSTGRES_HOST", "localhost"),
        port=int(src.get("POSTGRES_PORT", "5432")),
        database=src["POSTGRES_DB"],
    )
    return url.render_as_string(hide_password=False)
