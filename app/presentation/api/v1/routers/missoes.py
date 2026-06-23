from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.application.use_cases.avaliar_submissao import AvaliarSubmissaoUseCase
from app.application.use_cases.criar_missao import CriarMissaoUseCase
from app.application.use_cases.submeter_codigo import SubmeterCodigoUseCase
from app.domain.exceptions import (
    DomainError,
    EntityNotFoundError,
    InvalidStateTransitionError,
    UnauthorizedActionError,
)
from app.domain.entities import Usuario
from app.domain.enums import DificuldadeMissao, PerfilUsuario, StatusMissao
from app.infrastructure.repositories.sqlalchemy_missao_repository import (
    SqlAlchemyMissaoRepository,
)
from app.presentation.dependencies import (
    get_avaliar_submissao_use_case,
    get_criar_missao_use_case,
    get_missao_repo,
    get_submeter_codigo_use_case,
    require_perfil,
)
from app.presentation.schemas.missao import (
    AtualizarMissaoRequest,
    CriarMissaoRequest,
    MissaoListResponse,
    MissaoResponse,
    PatchMissaoStatusRequest,
)
from app.presentation.schemas.submissao import (
    AvaliarSubmissaoRequest,
    SubmissaoResultadoResponse,
    SubmeterCodigoRequest,
)

router = APIRouter(prefix="/missoes", tags=["Missões"])


def _map_missao(missao) -> MissaoResponse:
    return MissaoResponse(
        id=missao.id,
        titulo=missao.titulo,
        descricao=missao.descricao,
        dificuldade=missao.dificuldade.value,
        xp_recompensa=missao.xp_recompensa,
        status=missao.status.value,
        badge_id_recompensa=missao.badge_id_recompensa,
        data_inicio=missao.data_inicio,
        deadline=missao.deadline,
        trilha_id=missao.trilha_id,
        ordem=missao.ordem,
    )


@router.post(
    "",
    response_model=MissaoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar missão (professor)",
)
def criar_missao(
    body: CriarMissaoRequest,
    _current_user: Usuario = Depends(
        require_perfil(PerfilUsuario.PROFESSOR, PerfilUsuario.GESTOR)
    ),
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
    return _map_missao(missao)


@router.get(
    "",
    response_model=MissaoListResponse,
    summary="Listar missões (com filtros opcionais)",
)
def listar_missoes(
    status_filtro: StatusMissao | None = Query(default=None, alias="status"),
    dificuldade: DificuldadeMissao | None = Query(default=None),
    trilha_id: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    repo: SqlAlchemyMissaoRepository = Depends(get_missao_repo),
) -> MissaoListResponse:
    missoes, total = repo.listar_todas(
        status=status_filtro,
        dificuldade=dificuldade,
        trilha_id=trilha_id,
        offset=offset,
        limit=limit,
    )
    return MissaoListResponse(
        items=[_map_missao(m) for m in missoes],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{missao_id}",
    response_model=MissaoResponse,
    summary="Detalhe de uma missão",
)
def obter_missao(
    missao_id: UUID,
    repo: SqlAlchemyMissaoRepository = Depends(get_missao_repo),
) -> MissaoResponse:
    missao = repo.obter_por_id(missao_id)
    if missao is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Missão não encontrada",
        )
    return _map_missao(missao)


@router.put(
    "/{missao_id}",
    response_model=MissaoResponse,
    summary="Atualizar missão",
)
def atualizar_missao(
    missao_id: UUID,
    body: AtualizarMissaoRequest,
    _current_user: Usuario = Depends(
        require_perfil(PerfilUsuario.PROFESSOR, PerfilUsuario.GESTOR)
    ),
    repo: SqlAlchemyMissaoRepository = Depends(get_missao_repo),
) -> MissaoResponse:
    missao = repo.obter_por_id(missao_id)
    if missao is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Missão não encontrada",
        )
    if missao.status not in {StatusMissao.EM_RASCUNHO, StatusMissao.AGENDADA}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Missao so pode ser editada em rascunho ou agendada",
        )
    if body.titulo is not None:
        missao.titulo = body.titulo
    if body.descricao is not None:
        missao.descricao = body.descricao
    if body.dificuldade is not None:
        missao.dificuldade = body.dificuldade
    if body.xp_recompensa is not None:
        missao.xp_recompensa = body.xp_recompensa
    if body.badge_id_recompensa is not None:
        missao.badge_id_recompensa = body.badge_id_recompensa
    if body.data_inicio is not None:
        missao.data_inicio = body.data_inicio
    if body.deadline is not None:
        missao.deadline = body.deadline
    if body.trilha_id is not None:
        missao.trilha_id = body.trilha_id
    if body.ordem is not None:
        missao.ordem = body.ordem
    missao = repo.salvar(missao)
    return _map_missao(missao)


@router.patch(
    "/{missao_id}/status",
    response_model=MissaoResponse,
    summary="Alterar status da missão (state machine)",
)
def alterar_status_missao(
    missao_id: UUID,
    body: PatchMissaoStatusRequest,
    _current_user: Usuario = Depends(
        require_perfil(PerfilUsuario.PROFESSOR, PerfilUsuario.GESTOR)
    ),
    repo: SqlAlchemyMissaoRepository = Depends(get_missao_repo),
) -> MissaoResponse:
    missao = repo.obter_por_id(missao_id)
    if missao is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Missão não encontrada",
        )
    try:
        missao.alterar_status(body.novo_status)
    except InvalidStateTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message,
        ) from exc
    missao = repo.salvar(missao)
    return _map_missao(missao)


@router.delete(
    "/{missao_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deletar missão",
)
def deletar_missao(
    missao_id: UUID,
    _current_user: Usuario = Depends(require_perfil(PerfilUsuario.GESTOR)),
    repo: SqlAlchemyMissaoRepository = Depends(get_missao_repo),
) -> None:
    missao = repo.obter_por_id(missao_id)
    if missao is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Missão não encontrada",
        )
    if missao.status != StatusMissao.EM_RASCUNHO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Missao so pode ser deletada em rascunho",
        )
    repo.deletar(missao_id)


@router.post(
    "/{missao_id}/submeter",
    response_model=SubmissaoResultadoResponse,
    summary="Submeter código para validação",
)
def submeter_codigo(
    missao_id: UUID,
    aluno_id: UUID,
    body: SubmeterCodigoRequest,
    current_user: Usuario = Depends(require_perfil(PerfilUsuario.ALUNO)),
    use_case: SubmeterCodigoUseCase = Depends(get_submeter_codigo_use_case),
) -> SubmissaoResultadoResponse:
    if current_user.id != aluno_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Aluno so pode submeter codigo para si proprio",
        )
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
    body: AvaliarSubmissaoRequest,
    current_user: Usuario = Depends(require_perfil(PerfilUsuario.PROFESSOR)),
    use_case: AvaliarSubmissaoUseCase = Depends(get_avaliar_submissao_use_case),
) -> dict[str, str | float]:
    try:
        correcao = use_case.executar(
            submissao_id=submissao_id,
            professor_id=current_user.id,
            nota=body.nota,
            feedback=body.feedback,
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
    except DomainError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message
        ) from exc
