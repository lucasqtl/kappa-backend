from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.entities import Missao
from app.domain.enums import StatusMissao
from app.infrastructure.database.mappers import (
    missao_entidade_para_model,
    missao_model_para_entidade,
)
from app.infrastructure.database.models import MissaoModel


class SqlAlchemyMissaoRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def obter_por_id(self, missao_id: UUID) -> Missao | None:
        model = self._session.get(MissaoModel, missao_id)
        if model is None:
            return None
        return missao_model_para_entidade(model)

    def listar_ativas_por_trilha(self, trilha_id: str) -> list[Missao]:
        models = (
            self._session.query(MissaoModel)
            .filter(
                MissaoModel.trilha_id == trilha_id,
                MissaoModel.status == StatusMissao.ATIVA,
            )
            .order_by(MissaoModel.ordem)
            .all()
        )
        return [missao_model_para_entidade(m) for m in models]

    def salvar(self, missao: Missao) -> Missao:
        model = self._session.get(MissaoModel, missao.id)
        if model is None:
            model = MissaoModel(id=missao.id)
            self._session.add(model)
        missao_entidade_para_model(missao, model)
        self._session.commit()
        self._session.refresh(model)
        return missao_model_para_entidade(model)
