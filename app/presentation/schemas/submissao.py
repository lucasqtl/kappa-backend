from uuid import UUID

from pydantic import BaseModel, Field


class SubmeterCodigoRequest(BaseModel):
    conteudo_codigo: str = Field(..., min_length=1)
    submissao_id: UUID | None = None


class SubmissaoResultadoResponse(BaseModel):
    submissao_id: UUID
    status: str
    xp_ganho: int
    level_up: bool
    novo_nivel: int | None = None
    mensagem: str
