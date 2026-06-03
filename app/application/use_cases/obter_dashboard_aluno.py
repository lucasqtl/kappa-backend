from uuid import UUID

from app.application.dto import DashboardAlunoDTO
from app.application.ports.repositories import (
    AlunoRepository,
    ProgressoMissaoRepository,
    RankingRepository,
)
from app.domain.exceptions import EntityNotFoundError


class ObterDashboardAlunoUseCase:
    XP_POR_NIVEL = 5000
    TRILHA_PADRAO = "STARTER_PACK_TRACK"

    def __init__(
        self,
        aluno_repo: AlunoRepository,
        progresso_repo: ProgressoMissaoRepository,
        ranking_repo: RankingRepository,
    ) -> None:
        self._aluno_repo = aluno_repo
        self._progresso_repo = progresso_repo
        self._ranking_repo = ranking_repo

    def executar(self, aluno_id: UUID, trilha_id: str | None = None) -> DashboardAlunoDTO:
        aluno = self._aluno_repo.obter_por_id(aluno_id)
        if aluno is None:
            raise EntityNotFoundError(f"Aluno {aluno_id} não encontrado")

        trilha = trilha_id or self.TRILHA_PADRAO
        missoes = self._progresso_repo.listar_progresso_aluno(aluno_id, trilha)
        posicao = self._ranking_repo.obter_posicao_aluno(aluno_id)
        ranking_top = self._ranking_repo.listar_top(limite=5)

        return DashboardAlunoDTO(
            aluno_id=aluno.id,
            username=aluno.username,
            nivel=aluno.nivel,
            xp_total=aluno.xp_total,
            xp_para_proximo_nivel=aluno.xp_para_proximo_nivel(self.XP_POR_NIVEL),
            xp_semana=aluno.xp_semana,
            dias_ofensiva=aluno.dias_ofensiva,
            titulo_rank=self._titulo_por_nivel(aluno.nivel),
            objetivo_atual=self._objetivo_atual(aluno.nivel),
            missoes=missoes,
            posicao_ranking=posicao,
            ranking_top=ranking_top,
        )

    @staticmethod
    def _titulo_por_nivel(nivel: int) -> str:
        if nivel < 10:
            return "NOVICE CODER"
        if nivel < 25:
            return "OPERATIVE"
        return "ELITE HACKER"

    @staticmethod
    def _objetivo_atual(nivel: int) -> str:
        return (
            f"Current objective: Complete Starter Pack modules to unlock "
            f"Level {nivel + 1} access protocols."
        )
