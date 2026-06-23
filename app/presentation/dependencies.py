from collections.abc import Callable
from typing import TypeVar
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.application.use_cases.avaliar_submissao import AvaliarSubmissaoUseCase
from app.application.use_cases.criar_missao import CriarMissaoUseCase
from app.application.use_cases.obter_dashboard_aluno import ObterDashboardAlunoUseCase
from app.application.use_cases.processar_evolucao import ProcessarEvolucaoUseCase
from app.application.use_cases.submeter_codigo import SubmeterCodigoUseCase
from app.domain.entities import Usuario
from app.domain.enums import PerfilUsuario
from app.infrastructure.database.models import UsuarioModel
from app.infrastructure.database.unit_of_work import SqlAlchemyTransactionManager
from app.infrastructure.integrations.mock_engine_ia import MockEngineIA
from app.infrastructure.repositories.sqlalchemy_aluno_repository import (
    SqlAlchemyAlunoRepository,
)
from app.infrastructure.repositories.sqlalchemy_badge_repository import (
    SqlAlchemyBadgeRepository,
)
from app.infrastructure.repositories.sqlalchemy_correcao_repository import (
    SqlAlchemyCorrecaoRepository,
)
from app.infrastructure.repositories.sqlalchemy_missao_repository import (
    SqlAlchemyMissaoRepository,
)
from app.infrastructure.repositories.sqlalchemy_professor_repository import (
    SqlAlchemyProfessorRepository,
)
from app.infrastructure.repositories.sqlalchemy_progresso_repository import (
    SqlAlchemyProgressoMissaoRepository,
)
from app.infrastructure.repositories.sqlalchemy_ranking_repository import (
    SqlAlchemyRankingRepository,
)
from app.infrastructure.repositories.sqlalchemy_submissao_repository import (
    SqlAlchemySubmissaoRepository,
)
from core.database import get_db
from core.security import decode_token

T = TypeVar("T")
_bearer = HTTPBearer()


def _use_case_factory(factory: Callable[[Session], T]) -> Callable[[Session], T]:
    def _dependency(db: Session = Depends(get_db)) -> T:
        return factory(db)

    return _dependency


def get_aluno_repo(db: Session = Depends(get_db)) -> SqlAlchemyAlunoRepository:
    return SqlAlchemyAlunoRepository(db)


def get_missao_repo(db: Session = Depends(get_db)) -> SqlAlchemyMissaoRepository:
    return SqlAlchemyMissaoRepository(db)


def get_submissao_repo(db: Session = Depends(get_db)) -> SqlAlchemySubmissaoRepository:
    return SqlAlchemySubmissaoRepository(db)


def get_badge_repo(db: Session = Depends(get_db)) -> SqlAlchemyBadgeRepository:
    return SqlAlchemyBadgeRepository(db)


def get_ranking_repo(db: Session = Depends(get_db)) -> SqlAlchemyRankingRepository:
    return SqlAlchemyRankingRepository(db)


def get_professor_repo(db: Session = Depends(get_db)) -> SqlAlchemyProfessorRepository:
    return SqlAlchemyProfessorRepository(db)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    payload = decode_token(credentials.credentials)
    if payload is None or payload.get("type") != "access":
        raise _unauthorized("Token invalido ou expirado")

    sub = payload.get("sub")
    if not sub:
        raise _unauthorized("Token malformado")

    try:
        user_id = UUID(sub)
    except ValueError:
        raise _unauthorized("Token malformado")

    model = db.get(UsuarioModel, user_id)
    if model is None:
        raise _unauthorized("Usuario nao encontrado")

    return Usuario(
        id=model.id,
        username=model.username,
        email=model.email,
        senha_hash=model.senha_hash,
        perfil=model.perfil,
    )


def require_perfil(*perfis: PerfilUsuario) -> Callable[[Usuario], Usuario]:
    allowed = set(perfis)

    def _dependency(current_user: Usuario = Depends(get_current_user)) -> Usuario:
        if current_user.perfil not in allowed:
            perfis_permitidos = ", ".join(perfil.value for perfil in perfis)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Perfil nao autorizado. Requer: {perfis_permitidos}",
            )
        return current_user

    return _dependency


def require_aluno_owner(
    aluno_id: UUID,
    current_user: Usuario = Depends(require_perfil(PerfilUsuario.ALUNO)),
) -> Usuario:
    if current_user.id != aluno_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Aluno so pode acessar seus proprios dados",
        )
    return current_user


def require_aluno_owner_or_staff(
    aluno_id: UUID,
    current_user: Usuario = Depends(get_current_user),
) -> Usuario:
    if current_user.perfil in {PerfilUsuario.PROFESSOR, PerfilUsuario.GESTOR}:
        return current_user
    if current_user.perfil == PerfilUsuario.ALUNO and current_user.id == aluno_id:
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Aluno so pode acessar seus proprios dados",
    )


def get_obter_dashboard_use_case(
    db: Session = Depends(get_db),
) -> ObterDashboardAlunoUseCase:
    return ObterDashboardAlunoUseCase(
        aluno_repo=SqlAlchemyAlunoRepository(db),
        progresso_repo=SqlAlchemyProgressoMissaoRepository(db),
        ranking_repo=SqlAlchemyRankingRepository(db),
    )


def get_submeter_codigo_use_case(
    db: Session = Depends(get_db),
) -> SubmeterCodigoUseCase:
    aluno_repo = SqlAlchemyAlunoRepository(db, auto_commit=False)
    missao_repo = SqlAlchemyMissaoRepository(db, auto_commit=False)
    submissao_repo = SqlAlchemySubmissaoRepository(db, auto_commit=False)
    badge_repo = SqlAlchemyBadgeRepository(db, auto_commit=False)
    ranking_repo = SqlAlchemyRankingRepository(db)
    processar_evolucao = ProcessarEvolucaoUseCase(
        aluno_repo=aluno_repo,
        missao_repo=missao_repo,
        badge_repo=badge_repo,
        ranking_repo=ranking_repo,
    )
    return SubmeterCodigoUseCase(
        aluno_repo=aluno_repo,
        missao_repo=missao_repo,
        submissao_repo=submissao_repo,
        engine_ia=MockEngineIA(),
        processar_evolucao=processar_evolucao,
        transaction_manager=SqlAlchemyTransactionManager(db),
    )


def get_criar_missao_use_case(
    db: Session = Depends(get_db),
) -> CriarMissaoUseCase:
    return CriarMissaoUseCase(missao_repo=SqlAlchemyMissaoRepository(db))


def get_avaliar_submissao_use_case(
    db: Session = Depends(get_db),
) -> AvaliarSubmissaoUseCase:
    return AvaliarSubmissaoUseCase(
        submissao_repo=SqlAlchemySubmissaoRepository(db),
        correcao_repo=SqlAlchemyCorrecaoRepository(db),
    )
