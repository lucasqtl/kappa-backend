import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import (
    DificuldadeMissao,
    PerfilUsuario,
    StatusMissao,
    StatusSubmissao,
)
from core.database import Base


class UsuarioModel(Base):
    __tablename__ = "usuarios"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    perfil: Mapped[PerfilUsuario] = mapped_column(
        Enum(PerfilUsuario, name="perfil_usuario"), nullable=False
    )
    departamento: Mapped[str | None] = mapped_column(String(128), nullable=True)

    aluno: Mapped["AlunoModel | None"] = relationship(
        back_populates="usuario", uselist=False
    )


class AlunoModel(Base):
    __tablename__ = "alunos"

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        primary_key=True,
    )
    nivel: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    xp_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    xp_semana: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    dias_ofensiva: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    usuario: Mapped[UsuarioModel] = relationship(back_populates="aluno")


class MissaoModel(Base):
    __tablename__ = "missoes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    dificuldade: Mapped[DificuldadeMissao] = mapped_column(
        Enum(DificuldadeMissao, name="dificuldade_missao"), nullable=False
    )
    xp_recompensa: Mapped[int] = mapped_column(Integer, nullable=False)
    badge_id_recompensa: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("badges.id"), nullable=True
    )
    data_inicio: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[StatusMissao] = mapped_column(
        Enum(StatusMissao, name="status_missao"), nullable=False
    )
    trilha_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    ordem: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class SubmissaoModel(Base):
    __tablename__ = "submissoes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    aluno_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("alunos.usuario_id"), nullable=False
    )
    missao_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("missoes.id"), nullable=False
    )
    conteudo_codigo: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[StatusSubmissao] = mapped_column(
        Enum(StatusSubmissao, name="status_submissao"), nullable=False
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )


class CorrecaoModel(Base):
    __tablename__ = "correcoes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    submissao_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("submissoes.id"), nullable=False
    )
    professor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False
    )
    nota: Mapped[float] = mapped_column(Float, nullable=False)
    feedback: Mapped[str] = mapped_column(Text, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )


class BadgeModel(Base):
    __tablename__ = "badges"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    codigo: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(128), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    icone_url: Mapped[str | None] = mapped_column(String(512), nullable=True)


class BadgeConquistadaModel(Base):
    __tablename__ = "badges_conquistadas"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    aluno_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("alunos.usuario_id"), nullable=False
    )
    badge_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("badges.id"), nullable=False
    )
    conquistado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
