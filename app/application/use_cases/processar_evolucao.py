from uuid import UUID

from app.application.ports.repositories import (
    AlunoRepository,
    BadgeRepository,
    MissaoRepository,
    RankingRepository,
)
from app.domain.entities import Aluno
from app.domain.exceptions import EntityNotFoundError


class ProcessarEvolucaoUseCase:
    XP_POR_NIVEL = 5000

    def __init__(
        self,
        aluno_repo: AlunoRepository,
        missao_repo: MissaoRepository,
        badge_repo: BadgeRepository,
        ranking_repo: RankingRepository,
    ) -> None:
        self._aluno_repo = aluno_repo
        self._missao_repo = missao_repo
        self._badge_repo = badge_repo
        self._ranking_repo = ranking_repo

    def executar(self, aluno_id: UUID, missao_id: UUID) -> tuple[Aluno, int, bool]:
        """
        Adiciona XP, verifica level up, concede badge e atualiza ranking.
        Retorna (aluno_atualizado, xp_ganho, level_up).
        """
        aluno = self._aluno_repo.obter_por_id(aluno_id)
        if aluno is None:
            raise EntityNotFoundError(f"Aluno {aluno_id} não encontrado")

        missao = self._missao_repo.obter_por_id(missao_id)
        if missao is None:
            raise EntityNotFoundError(f"Missão {missao_id} não encontrada")

        xp_ganho = missao.xp_recompensa
        aluno.xp_total += xp_ganho
        aluno.xp_semana += xp_ganho

        level_up = False
        if (
            aluno.xp_total > 0
            and aluno.xp_total % self.XP_POR_NIVEL == 0
        ):
            aluno.nivel += 1
            level_up = True

        if missao.badge_id_recompensa is not None:
            ja_tem = any(
                b.badge_id == missao.badge_id_recompensa
                for b in self._badge_repo.listar_conquistadas_aluno(aluno_id)
            )
            if not ja_tem:
                self._badge_repo.conceder_badge(aluno_id, missao.badge_id_recompensa)

        aluno_atualizado = self._aluno_repo.salvar(aluno)
        self._ranking_repo.atualizar_entrada(aluno_atualizado)

        return aluno_atualizado, xp_ganho, level_up
