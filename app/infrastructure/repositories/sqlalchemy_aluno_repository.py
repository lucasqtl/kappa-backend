from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.domain.entities import Aluno
from app.infrastructure.database.mappers import aluno_para_model, usuario_model_para_aluno
from app.infrastructure.database.models import AlunoModel


class SqlAlchemyAlunoRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def obter_por_id(self, aluno_id: UUID) -> Aluno | None:
        model = (
            self._session.query(AlunoModel)
            .options(joinedload(AlunoModel.usuario))
            .filter(AlunoModel.usuario_id == aluno_id)
            .one_or_none()
        )
        if model is None:
            return None
        return usuario_model_para_aluno(model)

    def salvar(self, aluno: Aluno) -> Aluno:
        model = (
            self._session.query(AlunoModel)
            .options(joinedload(AlunoModel.usuario))
            .filter(AlunoModel.usuario_id == aluno.id)
            .one_or_none()
        )
        if model is None:
            raise ValueError(f"Aluno {aluno.id} não existe no banco")
        aluno_para_model(aluno, model.usuario, model)
        self._session.commit()
        self._session.refresh(model)
        return usuario_model_para_aluno(model)
