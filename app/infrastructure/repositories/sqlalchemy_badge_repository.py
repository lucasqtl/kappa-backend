from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.domain.entities import Badge, BadgeConquistada
from app.infrastructure.database.mappers import (
    badge_conquistada_model_para_entidade,
    badge_model_para_entidade,
)
from app.infrastructure.database.models import BadgeConquistadaModel, BadgeModel


class SqlAlchemyBadgeRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def obter_por_id(self, badge_id: UUID) -> Badge | None:
        model = self._session.get(BadgeModel, badge_id)
        if model is None:
            return None
        return badge_model_para_entidade(model)

    def listar_conquistadas_aluno(self, aluno_id: UUID) -> list[BadgeConquistada]:
        models = (
            self._session.query(BadgeConquistadaModel)
            .filter(BadgeConquistadaModel.aluno_id == aluno_id)
            .all()
        )
        return [badge_conquistada_model_para_entidade(m) for m in models]

    def conceder_badge(self, aluno_id: UUID, badge_id: UUID) -> BadgeConquistada:
        model = BadgeConquistadaModel(
            id=uuid4(),
            aluno_id=aluno_id,
            badge_id=badge_id,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return badge_conquistada_model_para_entidade(model)
