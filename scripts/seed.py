from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.database import SessionLocal
from app.domain.enums import DificuldadeMissao, PerfilUsuario, StatusMissao
from app.infrastructure.database.models import BadgeModel, MissaoModel, UsuarioModel

GESTOR_ID = UUID("11111111-1111-4111-8111-111111111111")
BADGE_FIRST_BLOOD_ID = UUID("22222222-2222-4222-8222-222222222222")
BADGE_CONTROL_FLOW_ID = UUID("33333333-3333-4333-8333-333333333333")
MISSAO_1_ID = UUID("44444444-4444-4444-8444-444444444401")
MISSAO_2_ID = UUID("44444444-4444-4444-8444-444444444402")
MISSAO_3_ID = UUID("44444444-4444-4444-8444-444444444403")
MISSAO_4_ID = UUID("44444444-4444-4444-8444-444444444404")

TRILHA_ID = "STARTER_PACK_TRACK"
GESTOR_SENHA_HASH = (
    "$2b$12$SEAcjHniPuFrxDww4HFmfeYMan9s6mukGWSIC/B2Dzt0WpE/m/zDm"
)


def seed() -> None:
    session = SessionLocal()
    try:
        if session.get(UsuarioModel, GESTOR_ID) is not None:
            print("Dados iniciais já existem. Seed ignorado.")
            return

        now = datetime.now(timezone.utc)
        deadline = now + timedelta(days=30)

        session.add_all(
            [
                BadgeModel(
                    id=BADGE_FIRST_BLOOD_ID,
                    codigo="FIRST_BLOOD",
                    nome="First Blood",
                    descricao="Primeira missão concluída na plataforma.",
                    icone_url="/badges/first-blood.svg",
                ),
                BadgeModel(
                    id=BADGE_CONTROL_FLOW_ID,
                    codigo="CONTROL_FLOW_MASTER",
                    nome="Control Flow Master",
                    descricao="Dominou estruturas condicionais e laços.",
                    icone_url="/badges/control-flow-master.svg",
                ),
            ]
        )

        session.add(
            UsuarioModel(
                id=GESTOR_ID,
                username="admin",
                email="admin@kappa.dev",
                senha_hash=GESTOR_SENHA_HASH,
                perfil=PerfilUsuario.GESTOR,
                departamento="Operações",
            )
        )

        session.add_all(
            [
                MissaoModel(
                    id=MISSAO_1_ID,
                    titulo="Hello World Protocol",
                    descricao="Implemente um programa que exibe a mensagem inicial do sistema.",
                    dificuldade=DificuldadeMissao.EASY,
                    xp_recompensa=500,
                    badge_id_recompensa=BADGE_FIRST_BLOOD_ID,
                    data_inicio=now,
                    deadline=deadline,
                    status=StatusMissao.ATIVA,
                    trilha_id=TRILHA_ID,
                    ordem=0,
                ),
                MissaoModel(
                    id=MISSAO_2_ID,
                    titulo="Variable Initialization",
                    descricao="Declare e utilize variáveis para processar entradas básicas.",
                    dificuldade=DificuldadeMissao.EASY,
                    xp_recompensa=750,
                    data_inicio=now,
                    deadline=deadline,
                    status=StatusMissao.ATIVA,
                    trilha_id=TRILHA_ID,
                    ordem=1,
                ),
                MissaoModel(
                    id=MISSAO_3_ID,
                    titulo="Control Flow Matrix",
                    descricao="Resolva desafios usando if/else e laços de repetição.",
                    dificuldade=DificuldadeMissao.MEDIUM,
                    xp_recompensa=1200,
                    badge_id_recompensa=BADGE_CONTROL_FLOW_ID,
                    data_inicio=now,
                    deadline=deadline,
                    status=StatusMissao.ATIVA,
                    trilha_id=TRILHA_ID,
                    ordem=2,
                ),
                MissaoModel(
                    id=MISSAO_4_ID,
                    titulo="Starter Pack Boss",
                    descricao="Desafio final da trilha inicial combinando lógica e estruturas de dados.",
                    dificuldade=DificuldadeMissao.BOSS,
                    xp_recompensa=2500,
                    data_inicio=now,
                    deadline=deadline,
                    status=StatusMissao.ATIVA,
                    trilha_id=TRILHA_ID,
                    ordem=3,
                ),
            ]
        )

        session.commit()
        print("Seed concluído com sucesso.")
        print("Gestor: admin@kappa.dev")
        print(f"Trilha: {TRILHA_ID} (4 missões ATIVA)")
        print("Badges: First Blood, Control Flow Master")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def main() -> int:
    try:
        seed()
    except Exception as exc:
        print(f"Erro ao executar seed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
