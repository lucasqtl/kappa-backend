from sqlalchemy.orm import Session

from app.domain.entities import Correcao
from app.infrastructure.database.mappers import correcao_model_para_entidade
from app.infrastructure.database.models import CorrecaoModel


class SqlAlchemyCorrecaoRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def salvar(self, correcao: Correcao) -> Correcao:
        model = CorrecaoModel(
            id=correcao.id,
            submissao_id=correcao.submissao_id,
            professor_id=correcao.professor_id,
            nota=correcao.nota,
            feedback=correcao.feedback,
            criado_em=correcao.criado_em,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return correcao_model_para_entidade(model)
