from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.application.dto import DashboardAlunoDTO
from app.application.use_cases.obter_dashboard_aluno import ObterDashboardAlunoUseCase
from app.domain.exceptions import DomainError, EntityNotFoundError
from app.infrastructure.repositories.sqlalchemy_aluno_repository import (
    SqlAlchemyAlunoRepository,
)
from app.infrastructure.repositories.sqlalchemy_badge_repository import (
    SqlAlchemyBadgeRepository,
)
from app.infrastructure.repositories.sqlalchemy_ranking_repository import (
    SqlAlchemyRankingRepository,
)
from app.infrastructure.repositories.sqlalchemy_submissao_repository import (
    SqlAlchemySubmissaoRepository,
)
from app.presentation.dependencies import (
    get_aluno_repo,
    get_badge_repo,
    get_obter_dashboard_use_case,
    get_ranking_repo,
    get_submissao_repo,
)
from app.presentation.schemas.aluno import (
    AlunoListResponse,
    AlunoResponse,
    BadgeResponse,
    DashboardAlunoResponse,
    EntradaRankingResponse,
    ProgressoMissaoResponse,
    RankingResponse,
)
from app.presentation.schemas.submissao import SubmissaoDetailResponse, SubmissaoListResponse

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
    "",
    response_model=AlunoListResponse,
    summary="Listar alunos (paginado)",
)
def listar_alunos(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    repo: SqlAlchemyAlunoRepository = Depends(get_aluno_repo),
) -> AlunoListResponse:
    alunos, total = repo.listar(offset=offset, limit=limit)
    return AlunoListResponse(
        items=[
            AlunoResponse(
                id=a.id,
                username=a.username,
                email=a.email,
                nivel=a.nivel,
                xp_total=a.xp_total,
                xp_semana=a.xp_semana,
                dias_ofensiva=a.dias_ofensiva,
            )
            for a in alunos
        ],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/ranking",
    response_model=RankingResponse,
    summary="Ranking global de alunos",
)
def obter_ranking(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    repo: SqlAlchemyRankingRepository = Depends(get_ranking_repo),
) -> RankingResponse:
    entries, total = repo.listar_top(offset=offset, limit=limit)
    return RankingResponse(
        ranking=[
            EntradaRankingResponse(
                aluno_id=e.aluno_id,
                username=e.username,
                xp_total=e.xp_total,
                posicao=e.posicao,
            )
            for e in entries
        ],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{aluno_id}",
    response_model=AlunoResponse,
    summary="Detalhe do aluno",
)
def obter_aluno(
    aluno_id: UUID,
    repo: SqlAlchemyAlunoRepository = Depends(get_aluno_repo),
) -> AlunoResponse:
    aluno = repo.obter_por_id(aluno_id)
    if aluno is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aluno não encontrado",
        )
    return AlunoResponse(
        id=aluno.id,
        username=aluno.username,
        email=aluno.email,
        nivel=aluno.nivel,
        xp_total=aluno.xp_total,
        xp_semana=aluno.xp_semana,
        dias_ofensiva=aluno.dias_ofensiva,
    )


@router.get(
    "/{aluno_id}/dashboard",
    response_model=DashboardAlunoResponse,
    summary="Dashboard gamificado do aluno",
)
def obter_dashboard_aluno(
    aluno_id: UUID,
    trilha_id: str | None = Query(
        default=None, description="ID da trilha (ex: STARTER_PACK_TRACK)"
    ),
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


@router.get(
    "/{aluno_id}/badges",
    response_model=list[BadgeResponse],
    summary="Badges conquistadas pelo aluno",
)
def listar_badges_aluno(
    aluno_id: UUID,
    repo: SqlAlchemyBadgeRepository = Depends(get_badge_repo),
) -> list[BadgeResponse]:
    pares = repo.listar_badges_detalhes(aluno_id)
    return [
        BadgeResponse(
            badge_id=conquista.badge_id,
            codigo=badge.codigo,
            nome=badge.nome,
            descricao=badge.descricao,
            icone_url=badge.icone_url,
            conquistado_em=conquista.conquistado_em,
        )
        for badge, conquista in pares
    ]


@router.get(
    "/{aluno_id}/submissoes",
    response_model=SubmissaoListResponse,
    summary="Submissões do aluno (paginado)",
)
def listar_submissoes_aluno(
    aluno_id: UUID,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    repo: SqlAlchemySubmissaoRepository = Depends(get_submissao_repo),
) -> SubmissaoListResponse:
    submissoes, total = repo.listar_por_aluno(aluno_id, offset=offset, limit=limit)
    return SubmissaoListResponse(
        items=[
            SubmissaoDetailResponse(
                id=s.id,
                aluno_id=s.aluno_id,
                missao_id=s.missao_id,
                conteudo_codigo=s.conteudo_codigo,
                status=s.status.value,
                criado_em=s.criado_em,
                atualizado_em=s.atualizado_em,
            )
            for s in submissoes
        ],
        total=total,
        offset=offset,
        limit=limit,
    )
