from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from alembic import command
from alembic.config import Config

from scripts.verify_schema import SchemaVerificationError, verify_schema


def main() -> int:
    alembic_cfg = Config(str(ROOT / "alembic.ini"))
    try:
        command.upgrade(alembic_cfg, "head")
        verify_schema()
    except SchemaVerificationError as exc:
        print(f"Falha na verificação do schema: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Erro ao configurar o banco: {exc}", file=sys.stderr)
        return 1

    print("Migrações aplicadas e schema verificado com sucesso.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
