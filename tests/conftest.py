"""Configuración compartida de la suite.

Las variables `POSTGRES_*` se toman del entorno. Si no están, se cargan de un
`.env` en la raíz del repo (si existe) y, como último recurso, de los mismos
valores por defecto que `compose.yaml` publica para desarrollo local (idénticos
a los de `.env.example`).
"""

import os
from pathlib import Path

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parent.parent

# Valores por defecto del servicio `db` de compose.yaml en local.
_COMPOSE_DEFAULTS = {
    "POSTGRES_USER": "taskflow",
    "POSTGRES_PASSWORD": "taskflow_local",
    "POSTGRES_DB": "taskflow",
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5432",
}

# No sobrescribe lo que ya venga en el entorno.
load_dotenv(_REPO_ROOT / ".env", override=False)

for _key, _value in _COMPOSE_DEFAULTS.items():
    os.environ.setdefault(_key, _value)
