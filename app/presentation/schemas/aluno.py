from uuid import UUID

from pydantic import BaseModel, Field


class ProgressoMissaoResponse(BaseModel):
    missao_id: UUID
    titulo: str
    dificuldade: str
    progresso_percentual: int
    bloqueada: bool
    motivo_bloqueio: str | None = None
    submissao_id: UUID | None = None
    xp_recompensa: int


class EntradaRankingResponse(BaseModel):
    aluno_id: UUID
    username: str
    xp_total: int
    posicao: int


class DashboardAlunoResponse(BaseModel):
    aluno_id: UUID
    username: str
    nivel: int
    xp_total: int
    xp_no_nivel: int
    xp_para_proximo_nivel: int
    xp_semana: int
    dias_ofensiva: int
    titulo_rank: str
    objetivo_atual: str
    missoes: list[ProgressoMissaoResponse]
    posicao_ranking: int | None
    ranking_top: list[EntradaRankingResponse]
