from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domain.entities import Submissao
from app.infrastructure.database.mappers import (
    submissao_entidade_para_model,
    submissao_model_para_entidade,
)
from app.infrastructure.database.models import SubmissaoModel


class SqlAlchemySubmissaoRepository:
    def __init__(self, session: Session, auto_commit: bool = True) -> None:
        self._session = session
        self._auto_commit = auto_commit

    def obter_por_id(self, submissao_id: UUID) -> Submissao | None:
        model = self._session.get(SubmissaoModel, submissao_id)
        if model is None:
            return None
        return submissao_model_para_entidade(model)

    def obter_por_aluno_e_missao(
        self, aluno_id: UUID, missao_id: UUID
    ) -> Submissao | None:
        model = (
            self._session.query(SubmissaoModel)
            .filter(
                SubmissaoModel.aluno_id == aluno_id,
                SubmissaoModel.missao_id == missao_id,
            )
            .order_by(SubmissaoModel.atualizado_em.desc())
            .first()
        )
        if model is None:
            return None
        return submissao_model_para_entidade(model)

    def listar_por_aluno(
        self, aluno_id: UUID, offset: int = 0, limit: int = 20
    ) -> tuple[list[Submissao], int]:
        query = self._session.query(SubmissaoModel).filter(
            SubmissaoModel.aluno_id == aluno_id
        )
        total = query.with_entities(func.count(SubmissaoModel.id)).scalar() or 0
        models = (
            query.order_by(SubmissaoModel.criado_em.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [submissao_model_para_entidade(m) for m in models], int(total)

    def salvar(self, submissao: Submissao) -> Submissao:
        model = self._session.get(SubmissaoModel, submissao.id)
        if model is None:
            model = SubmissaoModel(
                id=submissao.id,
                aluno_id=submissao.aluno_id,
                missao_id=submissao.missao_id,
                conteudo_codigo=submissao.conteudo_codigo,
                status=submissao.status,
            )
            self._session.add(model)
        else:
            submissao_entidade_para_model(submissao, model)
        if self._auto_commit:
            self._session.commit()
        else:
            self._session.flush()
        self._session.refresh(model)
        return submissao_model_para_entidade(model)
