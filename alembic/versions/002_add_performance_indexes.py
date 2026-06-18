"""add performance indexes

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-18 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_submissoes_aluno_id", "submissoes", ["aluno_id"])
    op.create_index("ix_submissoes_missao_id", "submissoes", ["missao_id"])
    op.create_index("ix_alunos_xp_total", "alunos", ["xp_total"])
    op.create_index(
        "ix_badges_conquistadas_aluno_id", "badges_conquistadas", ["aluno_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_badges_conquistadas_aluno_id", table_name="badges_conquistadas")
    op.drop_index("ix_alunos_xp_total", table_name="alunos")
    op.drop_index("ix_submissoes_missao_id", table_name="submissoes")
    op.drop_index("ix_submissoes_aluno_id", table_name="submissoes")
