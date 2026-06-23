from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.entities import ProgressoMissao
from app.domain.enums import StatusMissao, StatusSubmissao
from app.infrastructure.database.mappers import missao_model_para_entidade
from app.infrastructure.database.mission_status import sincronizar_status_missoes_por_datas
from app.infrastructure.database.models import MissaoModel, SubmissaoModel


class SqlAlchemyProgressoMissaoRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def listar_progresso_aluno(
        self, aluno_id: UUID, trilha_id: str | None = None
    ) -> list[ProgressoMissao]:
        sincronizar_status_missoes_por_datas(self._session)
        query = self._session.query(MissaoModel).order_by(MissaoModel.ordem)
        if trilha_id:
            query = query.filter(MissaoModel.trilha_id == trilha_id)

        missoes = query.all()
        resultado: list[ProgressoMissao] = []
        missao_anterior_concluida = True

        for missao_model in missoes:
            missao = missao_model_para_entidade(missao_model)
            submissao = (
                self._session.query(SubmissaoModel)
                .filter(
                    SubmissaoModel.aluno_id == aluno_id,
                    SubmissaoModel.missao_id == missao.id,
                )
                .order_by(SubmissaoModel.atualizado_em.desc())
                .first()
            )

            progresso = 0
            bloqueada = False
            motivo: str | None = None
            submissao_id: UUID | None = None

            if missao.status != StatusMissao.ATIVA:
                bloqueada = True
                motivo = f"Missão {missao.status.value}"
            elif not missao_anterior_concluida:
                bloqueada = True
                motivo = "REQUIRES PREVIOUS MODULE"
            elif submissao:
                submissao_id = submissao.id
                if submissao.status == StatusSubmissao.FINALIZADA:
                    progresso = 100
                    missao_anterior_concluida = True
                elif submissao.status in (
                    StatusSubmissao.VALIDANDO,
                    StatusSubmissao.PROCESSANDO_EVOLUCAO,
                ):
                    progresso = 50
                    missao_anterior_concluida = False
                else:
                    progresso = 45
                    missao_anterior_concluida = False
            else:
                if missao.ordem == 0 or missao_anterior_concluida:
                    progresso = 0
                    missao_anterior_concluida = False
                else:
                    bloqueada = True
                    motivo = "REQUIRES PREVIOUS MODULE"

            if submissao and submissao.status == StatusSubmissao.FINALIZADA:
                missao_anterior_concluida = True

            resultado.append(
                ProgressoMissao(
                    missao=missao,
                    progresso_percentual=progresso,
                    bloqueada=bloqueada,
                    motivo_bloqueio=motivo,
                    submissao_id=submissao_id,
                )
            )

        return resultado
