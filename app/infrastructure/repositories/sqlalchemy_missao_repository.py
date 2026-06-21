from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domain.entities import Missao
from app.domain.enums import DificuldadeMissao, StatusMissao
from app.infrastructure.database.mappers import (
    missao_entidade_para_model,
    missao_model_para_entidade,
)
from app.infrastructure.database.mission_status import sincronizar_status_missoes_por_datas
from app.infrastructure.database.models import MissaoModel


class SqlAlchemyMissaoRepository:
    def __init__(self, session: Session, auto_commit: bool = True) -> None:
        self._session = session
        self._auto_commit = auto_commit

    def obter_por_id(self, missao_id: UUID) -> Missao | None:
        sincronizar_status_missoes_por_datas(self._session, self._auto_commit)
        model = self._session.get(MissaoModel, missao_id)
        if model is None:
            return None
        return missao_model_para_entidade(model)

    def listar_ativas_por_trilha(self, trilha_id: str) -> list[Missao]:
        sincronizar_status_missoes_por_datas(self._session, self._auto_commit)
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

    def listar_todas(
        self,
        status: StatusMissao | None = None,
        dificuldade: DificuldadeMissao | None = None,
        trilha_id: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Missao], int]:
        sincronizar_status_missoes_por_datas(self._session, self._auto_commit)
        query = self._session.query(MissaoModel)
        if status is not None:
            query = query.filter(MissaoModel.status == status)
        if dificuldade is not None:
            query = query.filter(MissaoModel.dificuldade == dificuldade)
        if trilha_id is not None:
            query = query.filter(MissaoModel.trilha_id == trilha_id)
        total = query.with_entities(func.count(MissaoModel.id)).scalar() or 0
        models = query.order_by(MissaoModel.ordem).offset(offset).limit(limit).all()
        return [missao_model_para_entidade(m) for m in models], int(total)

    def listar(
        self,
        status: StatusMissao | None = None,
        trilha_id: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Missao], int]:
        return self.listar_todas(
            status=status,
            trilha_id=trilha_id,
            offset=offset,
            limit=limit,
        )

    def deletar(self, missao_id: UUID) -> None:
        model = self._session.get(MissaoModel, missao_id)
        if model is not None:
            self._session.delete(model)
            self._commit_or_flush()

    def salvar(self, missao: Missao) -> Missao:
        model = self._session.get(MissaoModel, missao.id)
        if model is None:
            model = MissaoModel(id=missao.id)
            self._session.add(model)
        missao_entidade_para_model(missao, model)
        self._commit_or_flush()
        self._session.refresh(model)
        return missao_model_para_entidade(model)

    def _commit_or_flush(self) -> None:
        if self._auto_commit:
            self._session.commit()
        else:
            self._session.flush()
