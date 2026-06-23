from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SubmeterCodigoRequest(BaseModel):
    conteudo_codigo: str = Field(..., min_length=1)
    submissao_id: UUID | None = None


class AvaliarSubmissaoRequest(BaseModel):
    nota: float
    feedback: str = Field(..., min_length=1)


class SubmissaoResultadoResponse(BaseModel):
    submissao_id: UUID
    status: str
    xp_ganho: int
    level_up: bool
    novo_nivel: int | None = None
    mensagem: str


class SubmissaoDetailResponse(BaseModel):
    id: UUID
    aluno_id: UUID
    missao_id: UUID
    conteudo_codigo: str
    status: str
    criado_em: datetime
    atualizado_em: datetime


class SubmissaoListResponse(BaseModel):
    items: list[SubmissaoDetailResponse]
    total: int
    offset: int
    limit: int
