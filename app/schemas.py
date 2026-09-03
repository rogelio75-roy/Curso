"""Esquemas de respuesta de la API (ver `docs/contrato-api.md` §Esquemas)."""

from pydantic import BaseModel, ConfigDict


class StateOut(BaseModel):
    """Estado tal como lo devuelve `GET /states`: `id` y `code`, ni un campo más."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: int
    code: str
