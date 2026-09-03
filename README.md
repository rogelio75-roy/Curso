# TaskFlow API

Base de la API de TaskFlow: FastAPI gestionada con [uv](https://docs.astral.sh/uv/)
y Python 3.12. En esta entrega solo existe `GET /health`.

## Requisitos

- Python 3.12 (serie 3.12).
- uv.
- Docker con Compose v2.

## Recorrido

```bash
# 1. Instalar dependencias exactamente como están fijadas en uv.lock
uv sync --frozen

# 2. Ejecutar los tests
uv run pytest -q

# 3. Comprobar el estilo con Ruff
uv run ruff check .

# 4. Levantar PostgreSQL en segundo plano
docker compose up -d

# 5. Aplicar las migraciones
uv run alembic upgrade head

# 6. Servir la API en local (http://127.0.0.1:8000)
uv run uvicorn app.main:app --reload

# 7. Al terminar, parar y retirar los contenedores
docker compose down
```

`GET /health` responde `200` con `{"status": "ok"}`.

## Configuración

`compose.yaml` trae valores locales por defecto, así que arranca sin `.env`. Para
personalizarlo, copia `.env.example` a `.env` y ajusta `POSTGRES_USER`,
`POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST` y `POSTGRES_PORT`.

## Migraciones

El esquema de la base se gestiona solo con Alembic. La URL de conexión la
construye `alembic/env.py` desde las variables `POSTGRES_*` del entorno (las
mismas de `.env.example`); no está en `alembic.ini`.

```bash
uv run alembic upgrade head     # aplica todas las migraciones
uv run alembic downgrade base   # revierte todas las revisiones
uv run alembic downgrade -1     # revierte solo la última
```

## Base de datos para los tests

Los tests de persistencia corren contra el PostgreSQL real de `compose.yaml`, no
contra SQLite. Antes de `uv run pytest`:

```bash
docker compose up -d            # levanta el servicio `db`
docker compose ps               # espera a que aparezca como healthy
```

`tests/conftest.py` toma las variables `POSTGRES_*` del entorno; si no están,
carga un `.env` de la raíz (si existe) y, en último caso, usa los valores por
defecto de `compose.yaml`. Cada test de migraciones deja la base sin tablas al
empezar y al terminar. Si la base no está disponible, esos tests se marcan como
`skipped` en lugar de fallar.
