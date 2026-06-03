from dataclasses import dataclass
from uuid import UUID

from app.domain.entities import EntradaRanking, ProgressoMissao


@dataclass
class DashboardAlunoDTO:
    aluno_id: UUID
    username: str
    nivel: int
    xp_total: int
    xp_para_proximo_nivel: int
    xp_semana: int
    dias_ofensiva: int
    titulo_rank: str
    objetivo_atual: str
    missoes: list[ProgressoMissao]
    posicao_ranking: int | None
    ranking_top: list[EntradaRanking]


@dataclass
class SubmissaoResultadoDTO:
    submissao_id: UUID
    status: str
    xp_ganho: int
    level_up: bool
    novo_nivel: int | None
    mensagem: str
