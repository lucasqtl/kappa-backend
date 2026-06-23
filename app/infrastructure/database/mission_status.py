from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.domain.enums import StatusMissao
from app.infrastructure.database.models import MissaoModel


def sincronizar_status_missoes_por_datas(
    session: Session, auto_commit: bool = True
) -> None:
    now = datetime.now(timezone.utc)
    alterou = False

    agendadas = (
        session.query(MissaoModel)
        .filter(
            MissaoModel.status == StatusMissao.AGENDADA,
            MissaoModel.data_inicio.is_not(None),
            MissaoModel.data_inicio <= now,
        )
        .all()
    )
    for missao in agendadas:
        missao.status = StatusMissao.ATIVA
        alterou = True

    expiradas = (
        session.query(MissaoModel)
        .filter(
            MissaoModel.status == StatusMissao.ATIVA,
            MissaoModel.deadline.is_not(None),
            MissaoModel.deadline <= now,
        )
        .all()
    )
    for missao in expiradas:
        missao.status = StatusMissao.EXPIRADA
        alterou = True

    if not alterou:
        return

    if auto_commit:
        session.commit()
    else:
        session.flush()
