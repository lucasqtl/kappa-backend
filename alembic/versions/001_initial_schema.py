"""initial schema

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-06-18 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    perfil_usuario = postgresql.ENUM(
        "ALUNO", "PROFESSOR", "GESTOR", name="perfil_usuario"
    )
    dificuldade_missao = postgresql.ENUM(
        "EASY", "MEDIUM", "BOSS", name="dificuldade_missao"
    )
    status_missao = postgresql.ENUM(
        "EM_RASCUNHO",
        "AGENDADA",
        "ATIVA",
        "EXPIRADA",
        "SUSPENSA",
        name="status_missao",
    )
    status_submissao = postgresql.ENUM(
        "EM_RASCUNHO",
        "VALIDANDO",
        "FALHA_COMPILACAO",
        "FALHA_TESTE",
        "PROCESSANDO_EVOLUCAO",
        "LEVEL_UP",
        "FINALIZADA",
        name="status_submissao",
    )

    bind = op.get_bind()
    perfil_usuario.create(bind, checkfirst=True)
    dificuldade_missao.create(bind, checkfirst=True)
    status_missao.create(bind, checkfirst=True)
    status_submissao.create(bind, checkfirst=True)

    op.create_table(
        "usuarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("username", sa.String(64), unique=True, nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("senha_hash", sa.String(255), nullable=False),
        sa.Column(
            "perfil",
            postgresql.ENUM(
                "ALUNO",
                "PROFESSOR",
                "GESTOR",
                name="perfil_usuario",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("departamento", sa.String(128), nullable=True),
    )

    op.create_table(
        "alunos",
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("nivel", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("xp_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("xp_semana", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("dias_ofensiva", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "badges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("codigo", sa.String(64), unique=True, nullable=False),
        sa.Column("nome", sa.String(128), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=False),
        sa.Column("icone_url", sa.String(512), nullable=True),
    )

    op.create_table(
        "missoes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("titulo", sa.String(255), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=False),
        sa.Column(
            "dificuldade",
            postgresql.ENUM(
                "EASY",
                "MEDIUM",
                "BOSS",
                name="dificuldade_missao",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("xp_recompensa", sa.Integer(), nullable=False),
        sa.Column(
            "badge_id_recompensa",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("badges.id"),
            nullable=True,
        ),
        sa.Column("data_inicio", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "EM_RASCUNHO",
                "AGENDADA",
                "ATIVA",
                "EXPIRADA",
                "SUSPENSA",
                name="status_missao",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("trilha_id", sa.String(128), nullable=True),
        sa.Column("ordem", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "submissoes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "aluno_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("alunos.usuario_id"),
            nullable=False,
        ),
        sa.Column(
            "missao_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("missoes.id"),
            nullable=False,
        ),
        sa.Column("conteudo_codigo", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "status",
            postgresql.ENUM(
                "EM_RASCUNHO",
                "VALIDANDO",
                "FALHA_COMPILACAO",
                "FALHA_TESTE",
                "PROCESSANDO_EVOLUCAO",
                "LEVEL_UP",
                "FINALIZADA",
                name="status_submissao",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "correcoes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "submissao_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("submissoes.id"),
            nullable=False,
        ),
        sa.Column(
            "professor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id"),
            nullable=False,
        ),
        sa.Column("nota", sa.Float(), nullable=False),
        sa.Column("feedback", sa.Text(), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "badges_conquistadas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "aluno_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("alunos.usuario_id"),
            nullable=False,
        ),
        sa.Column(
            "badge_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("badges.id"),
            nullable=False,
        ),
        sa.Column("conquistado_em", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("badges_conquistadas")
    op.drop_table("correcoes")
    op.drop_table("submissoes")
    op.drop_table("missoes")
    op.drop_table("badges")
    op.drop_table("alunos")
    op.drop_table("usuarios")
    op.execute("DROP TYPE status_submissao")
    op.execute("DROP TYPE status_missao")
    op.execute("DROP TYPE dificuldade_missao")
    op.execute("DROP TYPE perfil_usuario")
