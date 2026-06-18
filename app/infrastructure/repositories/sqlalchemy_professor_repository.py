from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.entities import Professor
from app.domain.enums import PerfilUsuario
from app.infrastructure.database.mappers import usuario_model_para_professor
from app.infrastructure.database.models import UsuarioModel


class SqlAlchemyProfessorRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def obter_por_id(self, professor_id: UUID) -> Professor | None:
        model = self._session.get(UsuarioModel, professor_id)
        if model is None or model.perfil != PerfilUsuario.PROFESSOR:
            return None
        return usuario_model_para_professor(model)

    def criar(self, professor: Professor) -> Professor:
        model = UsuarioModel(
            id=professor.id,
            username=professor.username,
            email=professor.email,
            senha_hash=professor.senha_hash,
            perfil=PerfilUsuario.PROFESSOR,
            departamento=professor.departamento,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return usuario_model_para_professor(model)
