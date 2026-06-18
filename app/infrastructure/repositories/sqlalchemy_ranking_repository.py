from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.domain.entities import Aluno, EntradaRanking
from app.infrastructure.database.models import AlunoModel


class SqlAlchemyRankingRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def obter_posicao_aluno(self, aluno_id: UUID) -> int | None:
        aluno = self._session.get(AlunoModel, aluno_id)
        if aluno is None:
            return None
        acima = (
            self._session.query(func.count(AlunoModel.usuario_id))
            .filter(AlunoModel.xp_total > aluno.xp_total)
            .scalar()
        )
        return int(acima or 0) + 1

    def listar_top(self, limite: int = 10) -> list[EntradaRanking]:
        models = (
            self._session.query(AlunoModel)
            .options(joinedload(AlunoModel.usuario))
            .order_by(AlunoModel.xp_total.desc())
            .limit(limite)
            .all()
        )
        return [
            EntradaRanking(
                aluno_id=m.usuario_id,
                username=m.usuario.username,
                xp_total=m.xp_total,
                posicao=idx + 1,
            )
            for idx, m in enumerate(models)
        ]

    def atualizar_entrada(self, aluno: Aluno) -> None:
        model = self._session.get(AlunoModel, aluno.id)
        if model is None:
            return
        model.xp_total = aluno.xp_total
        model.nivel = aluno.nivel
        model.xp_semana = aluno.xp_semana
        model.dias_ofensiva = aluno.dias_ofensiva
        self._session.flush()
