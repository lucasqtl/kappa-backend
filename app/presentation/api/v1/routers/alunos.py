from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.application.dto import DashboardAlunoDTO
from app.application.use_cases.obter_dashboard_aluno import ObterDashboardAlunoUseCase
from app.domain.exceptions import DomainError, EntityNotFoundError
from app.presentation.dependencies import get_obter_dashboard_use_case
from app.presentation.schemas.aluno import (
    DashboardAlunoResponse,
    EntradaRankingResponse,
    ProgressoMissaoResponse,
)

router = APIRouter(prefix="/alunos", tags=["Alunos"])


def _map_dashboard(dto: DashboardAlunoDTO) -> DashboardAlunoResponse:
    xp_por_nivel = ObterDashboardAlunoUseCase.XP_POR_NIVEL
    xp_no_nivel = dto.xp_total % xp_por_nivel
    return DashboardAlunoResponse(
        aluno_id=dto.aluno_id,
        username=dto.username,
        nivel=dto.nivel,
        xp_total=dto.xp_total,
        xp_no_nivel=xp_no_nivel,
        xp_para_proximo_nivel=dto.xp_para_proximo_nivel,
        xp_semana=dto.xp_semana,
        dias_ofensiva=dto.dias_ofensiva,
        titulo_rank=dto.titulo_rank,
        objetivo_atual=dto.objetivo_atual,
        missoes=[
            ProgressoMissaoResponse(
                missao_id=p.missao.id,
                titulo=p.missao.titulo,
                dificuldade=p.missao.dificuldade.value,
                progresso_percentual=p.progresso_percentual,
                bloqueada=p.bloqueada,
                motivo_bloqueio=p.motivo_bloqueio,
                submissao_id=p.submissao_id,
                xp_recompensa=p.missao.xp_recompensa,
            )
            for p in dto.missoes
        ],
        posicao_ranking=dto.posicao_ranking,
        ranking_top=[
            EntradaRankingResponse(
                aluno_id=e.aluno_id,
                username=e.username,
                xp_total=e.xp_total,
                posicao=e.posicao,
            )
            for e in dto.ranking_top
        ],
    )


@router.get(
    "/{aluno_id}/dashboard",
    response_model=DashboardAlunoResponse,
    summary="Dashboard gamificado do aluno",
)
def obter_dashboard_aluno(
    aluno_id: UUID,
    trilha_id: str | None = Query(default=None, description="ID da trilha (ex: STARTER_PACK_TRACK)"),
    use_case: ObterDashboardAlunoUseCase = Depends(get_obter_dashboard_use_case),
) -> DashboardAlunoResponse:
    try:
        dto = use_case.executar(aluno_id, trilha_id=trilha_id)
        return _map_dashboard(dto)
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=exc.message
        ) from exc
    except DomainError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message
        ) from exc
