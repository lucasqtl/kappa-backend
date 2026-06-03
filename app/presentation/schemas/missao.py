from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.enums import DificuldadeMissao


class CriarMissaoRequest(BaseModel):
    titulo: str = Field(..., min_length=3, max_length=255)
    descricao: str
    dificuldade: DificuldadeMissao
    xp_recompensa: int = Field(..., gt=0)
    agendar: bool = False
    badge_id_recompensa: UUID | None = None
    data_inicio: datetime | None = None
    deadline: datetime | None = None
    trilha_id: str | None = None
    ordem: int = 0


class MissaoResponse(BaseModel):
    id: UUID
    titulo: str
    descricao: str
    dificuldade: str
    xp_recompensa: int
    status: str
    trilha_id: str | None = None
    ordem: int = 0
