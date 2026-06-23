from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.domain.entities import Usuario
from app.domain.enums import PerfilUsuario
from app.domain.exceptions import EntityNotFoundError
from app.infrastructure.repositories.sqlalchemy_submissao_repository import (
    SqlAlchemySubmissaoRepository,
)
from app.presentation.dependencies import get_current_user, get_submissao_repo
from app.presentation.schemas.submissao import SubmissaoDetailResponse

router = APIRouter(prefix="/submissoes", tags=["Submissões"])


def _map_submissao(s) -> SubmissaoDetailResponse:
    return SubmissaoDetailResponse(
        id=s.id,
        aluno_id=s.aluno_id,
        missao_id=s.missao_id,
        conteudo_codigo=s.conteudo_codigo,
        status=s.status.value,
        criado_em=s.criado_em,
        atualizado_em=s.atualizado_em,
    )


@router.get(
    "/{submissao_id}",
    response_model=SubmissaoDetailResponse,
    summary="Detalhe de uma submissão",
)
def obter_submissao(
    submissao_id: UUID,
    current_user: Usuario = Depends(get_current_user),
    repo: SqlAlchemySubmissaoRepository = Depends(get_submissao_repo),
) -> SubmissaoDetailResponse:
    submissao = repo.obter_por_id(submissao_id)
    if submissao is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submissão não encontrada",
        )
    if (
        current_user.perfil == PerfilUsuario.ALUNO
        and current_user.id != submissao.aluno_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Aluno so pode acessar suas proprias submissoes",
        )
    return _map_submissao(submissao)
