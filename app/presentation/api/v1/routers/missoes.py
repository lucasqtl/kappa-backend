from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.application.use_cases.avaliar_submissao import AvaliarSubmissaoUseCase
from app.application.use_cases.criar_missao import CriarMissaoUseCase
from app.application.use_cases.submeter_codigo import SubmeterCodigoUseCase
from app.domain.exceptions import (
    DomainError,
    EntityNotFoundError,
    InvalidStateTransitionError,
    UnauthorizedActionError,
)
from app.presentation.dependencies import (
    get_avaliar_submissao_use_case,
    get_criar_missao_use_case,
    get_submeter_codigo_use_case,
)
from app.presentation.schemas.missao import CriarMissaoRequest, MissaoResponse
from app.presentation.schemas.submissao import (
    SubmissaoResultadoResponse,
    SubmeterCodigoRequest,
)

router = APIRouter(prefix="/missoes", tags=["Missões"])


@router.post(
    "",
    response_model=MissaoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar missão (professor)",
)
def criar_missao(
    body: CriarMissaoRequest,
    use_case: CriarMissaoUseCase = Depends(get_criar_missao_use_case),
) -> MissaoResponse:
    missao = use_case.executar(
        titulo=body.titulo,
        descricao=body.descricao,
        dificuldade=body.dificuldade,
        xp_recompensa=body.xp_recompensa,
        agendar=body.agendar,
        badge_id_recompensa=body.badge_id_recompensa,
        data_inicio=body.data_inicio,
        deadline=body.deadline,
        trilha_id=body.trilha_id,
        ordem=body.ordem,
    )
    return MissaoResponse(
        id=missao.id,
        titulo=missao.titulo,
        descricao=missao.descricao,
        dificuldade=missao.dificuldade.value,
        xp_recompensa=missao.xp_recompensa,
        status=missao.status.value,
        trilha_id=missao.trilha_id,
        ordem=missao.ordem,
    )


@router.post(
    "/{missao_id}/submeter",
    response_model=SubmissaoResultadoResponse,
    summary="Submeter código para validação",
)
def submeter_codigo(
    missao_id: UUID,
    aluno_id: UUID,
    body: SubmeterCodigoRequest,
    use_case: SubmeterCodigoUseCase = Depends(get_submeter_codigo_use_case),
) -> SubmissaoResultadoResponse:
    try:
        resultado = use_case.executar(
            aluno_id=aluno_id,
            missao_id=missao_id,
            conteudo_codigo=body.conteudo_codigo,
            submissao_id=body.submissao_id,
        )
        return SubmissaoResultadoResponse(
            submissao_id=resultado.submissao_id,
            status=resultado.status,
            xp_ganho=resultado.xp_ganho,
            level_up=resultado.level_up,
            novo_nivel=resultado.novo_nivel,
            mensagem=resultado.mensagem,
        )
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=exc.message
        ) from exc
    except UnauthorizedActionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=exc.message
        ) from exc
    except InvalidStateTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=exc.message
        ) from exc
    except DomainError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message
        ) from exc


@router.post(
    "/submissoes/{submissao_id}/avaliar",
    status_code=status.HTTP_201_CREATED,
    summary="Avaliação manual pelo professor",
)
def avaliar_submissao(
    submissao_id: UUID,
    professor_id: UUID,
    nota: float,
    feedback: str,
    use_case: AvaliarSubmissaoUseCase = Depends(get_avaliar_submissao_use_case),
) -> dict[str, str | float]:
    try:
        correcao = use_case.executar(
            submissao_id=submissao_id,
            professor_id=professor_id,
            nota=nota,
            feedback=feedback,
        )
        return {
            "correcao_id": str(correcao.id),
            "nota": correcao.nota,
            "feedback": correcao.feedback,
        }
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=exc.message
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
