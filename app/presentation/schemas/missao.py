from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.enums import DificuldadeMissao, StatusMissao


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


class AtualizarMissaoRequest(BaseModel):
    titulo: str | None = Field(None, min_length=3, max_length=255)
    descricao: str | None = None
    dificuldade: DificuldadeMissao | None = None
    xp_recompensa: int | None = Field(None, gt=0)
    badge_id_recompensa: UUID | None = None
    data_inicio: datetime | None = None
    deadline: datetime | None = None
    trilha_id: str | None = None
    ordem: int | None = None


class PatchMissaoStatusRequest(BaseModel):
    novo_status: StatusMissao


class MissaoResponse(BaseModel):
    id: UUID
    titulo: str
    descricao: str
    dificuldade: str
    xp_recompensa: int
    status: str
    badge_id_recompensa: UUID | None = None
    data_inicio: datetime | None = None
    deadline: datetime | None = None
    trilha_id: str | None = None
    ordem: int = 0


class MissaoListResponse(BaseModel):
    items: list[MissaoResponse]
    total: int
    offset: int
    limit: int
