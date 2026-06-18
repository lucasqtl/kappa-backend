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
from app.domain.entities import Aluno
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


# ── Repositórios diretos ───────────────────────────────────────────────────────

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


# ── Auth ───────────────────────────────────────────────────────────────────────

def get_current_aluno(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Aluno:
    payload = decode_token(credentials.credentials)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token malformado",
        )
    try:
        aluno_id = UUID(sub)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token malformado",
        )
    aluno = SqlAlchemyAlunoRepository(db).obter_por_id(aluno_id)
    if aluno is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado",
        )
    return aluno


# ── Use cases ─────────────────────────────────────────────────────────────────

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
    aluno_repo = SqlAlchemyAlunoRepository(db)
    missao_repo = SqlAlchemyMissaoRepository(db)
    submissao_repo = SqlAlchemySubmissaoRepository(db)
    badge_repo = SqlAlchemyBadgeRepository(db)
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
