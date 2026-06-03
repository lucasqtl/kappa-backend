from datetime import datetime
from uuid import UUID, uuid4

from app.application.ports.repositories import MissaoRepository
from app.domain.entities import Missao
from app.domain.enums import DificuldadeMissao, StatusMissao


class CriarMissaoUseCase:
    def __init__(self, missao_repo: MissaoRepository) -> None:
        self._missao_repo = missao_repo

    def executar(
        self,
        titulo: str,
        descricao: str,
        dificuldade: DificuldadeMissao,
        xp_recompensa: int,
        agendar: bool = False,
        badge_id_recompensa: UUID | None = None,
        data_inicio: datetime | None = None,
        deadline: datetime | None = None,
        trilha_id: str | None = None,
        ordem: int = 0,
    ) -> Missao:
        status = StatusMissao.AGENDADA if agendar else StatusMissao.EM_RASCUNHO
        missao = Missao(
            id=uuid4(),
            titulo=titulo,
            descricao=descricao,
            dificuldade=dificuldade,
            xp_recompensa=xp_recompensa,
            status=status,
            badge_id_recompensa=badge_id_recompensa,
            data_inicio=data_inicio,
            deadline=deadline,
            trilha_id=trilha_id,
            ordem=ordem,
        )
        return self._missao_repo.salvar(missao)
