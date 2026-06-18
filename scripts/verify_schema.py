from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import inspect

from core.database import engine

EXPECTED_TABLES = frozenset(
    {
        "usuarios",
        "alunos",
        "badges",
        "missoes",
        "submissoes",
        "correcoes",
        "badges_conquistadas",
        "alembic_version",
    }
)

EXPECTED_FOREIGN_KEYS: tuple[tuple[str, str, str, str], ...] = (
    ("alunos", "usuario_id", "usuarios", "id"),
    ("missoes", "badge_id_recompensa", "badges", "id"),
    ("submissoes", "aluno_id", "alunos", "usuario_id"),
    ("submissoes", "missao_id", "missoes", "id"),
    ("correcoes", "submissao_id", "submissoes", "id"),
    ("correcoes", "professor_id", "usuarios", "id"),
    ("badges_conquistadas", "aluno_id", "alunos", "usuario_id"),
    ("badges_conquistadas", "badge_id", "badges", "id"),
)

EXPECTED_UNIQUE_COLUMNS: dict[str, set[str]] = {
    "usuarios": {"username", "email"},
    "badges": {"codigo"},
}

EXPECTED_INDEXES = frozenset(
    {
        "ix_submissoes_aluno_id",
        "ix_submissoes_missao_id",
        "ix_alunos_xp_total",
        "ix_badges_conquistadas_aluno_id",
    }
)


class SchemaVerificationError(Exception):
    pass


def verify_schema() -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    missing_tables = EXPECTED_TABLES - tables
    if missing_tables:
        raise SchemaVerificationError(
            f"Tabelas ausentes: {', '.join(sorted(missing_tables))}"
        )

    actual_foreign_keys: set[tuple[str, str, str, str]] = set()
    for table in tables:
        for fk in inspector.get_foreign_keys(table):
            for local_col, referred_col in zip(
                fk["constrained_columns"], fk["referred_columns"]
            ):
                actual_foreign_keys.add(
                    (table, local_col, fk["referred_table"], referred_col)
                )

    for expected_fk in EXPECTED_FOREIGN_KEYS:
        if expected_fk not in actual_foreign_keys:
            table, local_col, referred_table, referred_col = expected_fk
            raise SchemaVerificationError(
                f"FK ausente: {table}.{local_col} -> {referred_table}.{referred_col}"
            )

    for table, expected_columns in EXPECTED_UNIQUE_COLUMNS.items():
        unique_sets = {
            frozenset(item["column_names"])
            for item in inspector.get_unique_constraints(table)
        }
        unique_sets.update(
            frozenset(index["column_names"])
            for index in inspector.get_indexes(table)
            if index.get("unique")
        )
        for column in expected_columns:
            if not any(column in unique_set for unique_set in unique_sets):
                raise SchemaVerificationError(
                    f"Constraint UNIQUE ausente em {table}.{column}"
                )

    indexes = {
        index["name"]
        for table in tables
        for index in inspector.get_indexes(table)
        if index["name"]
    }
    missing_indexes = EXPECTED_INDEXES - indexes
    if missing_indexes:
        raise SchemaVerificationError(
            f"Índices ausentes: {', '.join(sorted(missing_indexes))}"
        )


def main() -> int:
    try:
        verify_schema()
    except SchemaVerificationError as exc:
        print(f"Falha na verificação do schema: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Erro ao conectar ou inspecionar o banco: {exc}", file=sys.stderr)
        return 1

    print("Schema verificado com sucesso.")
    print(f"Tabelas: {', '.join(sorted(EXPECTED_TABLES - {'alembic_version'}))}")
    print(f"Índices de performance: {', '.join(sorted(EXPECTED_INDEXES))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
