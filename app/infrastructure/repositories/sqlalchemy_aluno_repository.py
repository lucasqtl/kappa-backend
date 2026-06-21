import uuid
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.domain.entities import Aluno
from app.domain.enums import PerfilUsuario
from app.infrastructure.database.mappers import aluno_para_model, usuario_model_para_aluno
from app.infrastructure.database.models import AlunoModel, UsuarioModel


class SqlAlchemyAlunoRepository:
    def __init__(self, session: Session, auto_commit: bool = True) -> None:
        self._session = session
        self._auto_commit = auto_commit

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

    def obter_por_email(self, email: str) -> Aluno | None:
        model = (
            self._session.query(AlunoModel)
            .join(AlunoModel.usuario)
            .options(joinedload(AlunoModel.usuario))
            .filter(UsuarioModel.email == email)
            .one_or_none()
        )
        if model is None:
            return None
        return usuario_model_para_aluno(model)

    def listar(self, offset: int = 0, limit: int = 20) -> tuple[list[Aluno], int]:
        total = (
            self._session.query(func.count(AlunoModel.usuario_id)).scalar() or 0
        )
        models = (
            self._session.query(AlunoModel)
            .options(joinedload(AlunoModel.usuario))
            .order_by(AlunoModel.xp_total.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [usuario_model_para_aluno(m) for m in models], int(total)

    def criar(self, aluno: Aluno) -> Aluno:
        usuario_model = UsuarioModel(
            id=aluno.id,
            username=aluno.username,
            email=aluno.email,
            senha_hash=aluno.senha_hash,
            perfil=PerfilUsuario.ALUNO,
        )
        aluno_model = AlunoModel(
            usuario_id=aluno.id,
            nivel=aluno.nivel,
            xp_total=aluno.xp_total,
            xp_semana=aluno.xp_semana,
            dias_ofensiva=aluno.dias_ofensiva,
        )
        self._session.add(usuario_model)
        self._session.flush()
        self._session.add(aluno_model)
        if self._auto_commit:
            self._session.commit()
        else:
            self._session.flush()
        self._session.refresh(aluno_model)
        return usuario_model_para_aluno(aluno_model)

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
        if self._auto_commit:
            self._session.commit()
        else:
            self._session.flush()
        self._session.refresh(model)
        return usuario_model_para_aluno(model)
