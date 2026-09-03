# Plan — Conexión de la API a PostgreSQL

Estado: **propuesto, pendiente de aprobación**. Hoy solo se acuerda el plan; no
se edita código.

## Fuentes

- `docs/contrato-api.md`, secciones **Salud** y **Estados**.
- `docs/decisiones-ingenieria.md`.
- `CLAUDE.md`.
- Decisiones abiertas: `docs/onboarding.md` §5 (nºs 1–4).

## Alcance

Llegar a `GET /states` sirviendo el catálogo cerrado de estados desde PostgreSQL
real, sembrado por una migración de Alembic idempotente, con `upgrade`/`downgrade`
probados en ambos sentidos.

## Fuera de alcance

Proyectos, tareas, filtros, `due_at`, skills, hooks y CI.

## Archivos protegidos

No se modifican: `docs/contrato-api.md`, `docs/decisiones-ingenieria.md`,
`CLAUDE.md`, `.gitignore`, `.env`. No se abre `.env`. `.env.example` es la única
fuente permitida para nombres de variables.

## Reglas de ejecución

- Cada incremento es un commit que se confirma **solo** con su comprobación.
- Al terminar un incremento, parar y esperar aprobación. No encadenar el
  siguiente.
- Una capacidad nueva empieza por un test que falla por su ausencia.
- No se debilita ni elimina una comprobación para conseguir verde.

## Qué existe ya

**Aplicación**
- `app/main.py` — FastAPI con un único endpoint: `GET /health` →
  `200 {"status": "ok"}`. Sin capa de datos, modelos ni configuración.
- `app/__init__.py` vacío.

**Tests**
- `tests/test_health.py` — dos tests sobre `/health` vía `TestClient`.
- `pyproject.toml`: `testpaths = ["tests"]`.

**Dependencias** (`pyproject.toml` + `uv.lock`)
- Runtime: `fastapi`, `uvicorn[standard]`. `pydantic` y `python-dotenv` entran
  como transitivas.
- Dev: `pytest`, `httpx`, `ruff`.
- No hay SQLAlchemy / SQLModel, Alembic ni driver de PostgreSQL.

**Infraestructura**
- `compose.yaml` — solo servicio `db` (`postgres:18-alpine`), volumen
  `postgres_data`, healthcheck. No hay servicio para la API.
- `.env.example` — `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`,
  `POSTGRES_PORT`.

**Documentos rectores**
- `docs/contrato-api.md` §Salud: `GET /health` → `200 {"status": "ok"}`, sin
  exponer credenciales ni detalles internos.
- `docs/contrato-api.md` §Estados: catálogo cerrado
  `PENDIENTE, EN_CURSO, BLOQUEADA, HECHA`. Sin endpoints de escritura.
  `GET /states` → `200`, lista ordenada por el campo de orden del catálogo y
  `id` como desempate. Esquema exacto por estado: `{"id": 1, "code": "PENDIENTE"}`
  — ni un campo más. El seed llega por migración (no por script de Docker), en
  cada `upgrade`, y debe ser idempotente.
- `docs/decisiones-ingenieria.md`: tests de persistencia contra PostgreSQL real
  (SQLite fuera); esquema solo por migraciones Alembic con `upgrade`/`downgrade`
  probados en ambos sentidos; nada de crear esquema por importación de módulos.
- `CLAUDE.md`: mismos límites; decisiones abiertas a confirmar antes de elegir.

**Estado git**: rama `feature/persistencia`, 4 commits, `evidencias/s03.md` sin
seguimiento (plantilla vacía).

## Incrementos

### Incremento 0 — Decidir el stack de persistencia (sin código)

No se edita nada. Se cierran las 4 decisiones abiertas de `docs/onboarding.md`
§5, adoptando en cada caso lo mínimo que cumple el contrato.

**Decisión 1 — Migraciones: Alembic.**
Único estándar con `upgrade`/`downgrade`; lo pide el contrato.
Encaja con el repo: `docs/decisiones-ingenieria.md` ya nombra "migraciones Alembic"
como mecanismo obligatorio y `CLAUDE.md` §Persistencia exige `upgrade`/`downgrade`
probados en ambos sentidos; hoy no hay ninguna herramienta de migración en
`pyproject.toml`, así que se añade sin desplazar nada.

**Decisión 2 — Capa de datos: SQLAlchemy 2.x, síncrono (Core/ORM).**
El contrato no pide async; sync simplifica tests y Alembic.
Encaja con el repo: el único endpoint actual (`GET /health` en `app/main.py`) es
síncrono y no hay capa de datos previa que fuerce async; `pydantic` ya entra como
transitiva de FastAPI, y SQLAlchemy es el ORM que Alembic asume por defecto.

**Decisión 3 — Driver: `psycopg` (v3), síncrono.**
Compatible con SQLAlchemy sync y Alembic sin bucle de eventos.
Encaja con el repo: la base es `postgres:18-alpine` (`compose.yaml`) y las
variables de conexión ya existen en `.env.example` (`POSTGRES_USER`,
`POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_PORT`); `psycopg` v3 consume esa URL
sin dependencias de async que el resto del código no usa.

**Decisión 4 — Aislamiento de tests: PostgreSQL real vía Compose; cada test en
transacción con `ROLLBACK`; migraciones aplicadas una vez por sesión de test.**
Rápido, determinista, sin SQLite.
Encaja con el repo: `docs/decisiones-ingenieria.md` y `CLAUDE.md` §Persistencia
prohíben SQLite y exigen PostgreSQL real; el servicio `db` de `compose.yaml` ya
trae healthcheck, y no hay suite de persistencia previa cuyo aislamiento haya que
respetar.

**Comprobación:** acuerdo explícito en el hilo. Sin él no arranca el Incremento 1.

### Incremento 1 — Dependencias y configuración de conexión

- Añadir a `pyproject.toml`: `sqlalchemy`, `alembic`, `psycopg[binary]`.
  Regenerar `uv.lock` con `uv lock`.
- `app/config.py`: construir la URL de PostgreSQL desde variables de entorno
  (`POSTGRES_*`; añadir `POSTGRES_HOST` a `.env.example` si hace falta). Sin
  valores reales.
- `app/db.py`: `engine` y `sessionmaker`. No crea esquema al importarse.
- `README.md`: documentar el comando de migraciones.

**Comprobación:**
- `uv sync --frozen` instala sin error.
- `uv run ruff check .` limpio.
- `uv run pytest -q` sigue verde (los tests de `/health` no tocan la base).
- Nuevo `tests/test_db_config.py` que falla si la URL no se construye desde el
  entorno y pasa cuando sí.

### Incremento 2 — Alembic inicializado con migración vacía y ciclo `upgrade`/`downgrade`

- `alembic init` adaptado: `env.py` toma la URL de `app/config.py`, no de
  `alembic.ini`.
- Primera revisión vacía (solo el andamiaje / tabla `alembic_version`).
- `README.md`: `uv run alembic upgrade head` / `downgrade base`.

**Comprobación:**
- Test de integración contra PostgreSQL de Compose: `upgrade head` sobre base
  vacía, verificar, `downgrade base`, verificar que la base queda limpia. Falla
  hoy porque no hay Alembic.
- Documentar en `README.md` cómo levantar la base para los tests.

### Incremento 3 — Migración del catálogo de estados (tabla + seed idempotente)

- Revisión Alembic que crea la tabla `states` con: `id` (PK generada por la
  base), `code` (único, no nulo) y un campo de orden explícito (p. ej.
  `position`) — el contrato exige ordenar por "el campo de orden del catálogo".
- `upgrade`: crea tabla y siembra los 4 estados con
  `INSERT ... ON CONFLICT (code) DO NOTHING` (idempotente).
- `downgrade`: elimina la tabla.

**Comprobación:**
- Test: tras `upgrade head`, la tabla tiene exactamente los 4 códigos del
  contrato.
- Test: ejecutar el seed dos veces no duplica filas.
- Test: `downgrade` elimina la tabla; `upgrade` la reconstruye idéntica.
- Todos fallan hoy.

### Incremento 4 — `GET /states`

- Modelo/tabla SQLAlchemy `State` mapeada a `states` (solo lectura).
- Endpoint `GET /states`: consulta ordenada por el campo de orden y `id` como
  desempate; lista JSON en la raíz; cada item exactamente `{"id": ..., "code": ...}`.
- Sin endpoints de escritura.

**Comprobación:**
- Test end-to-end contra PostgreSQL: `GET /states` → `200`, 4 elementos, orden
  estable entre dos llamadas idénticas, esquema exacto (ni un campo de más), y
  ausencia de rutas `POST/PUT/PATCH/DELETE` sobre `/states`.
- `uv run ruff check .` limpio.
- Suite completa verde.
