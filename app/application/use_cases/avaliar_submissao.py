from uuid import UUID, uuid4

from app.application.ports.repositories import CorrecaoRepository, SubmissaoRepository
from app.domain.entities import Correcao
from app.domain.exceptions import EntityNotFoundError
from core.logging_config import log_use_case


class AvaliarSubmissaoUseCase:
    def __init__(
        self,
        submissao_repo: SubmissaoRepository,
        correcao_repo: CorrecaoRepository,
    ) -> None:
        self._submissao_repo = submissao_repo
        self._correcao_repo = correcao_repo

    @log_use_case("AvaliarSubmissaoUseCase")
    def executar(
        self,
        submissao_id: UUID,
        professor_id: UUID,
        nota: float,
        feedback: str,
    ) -> Correcao:
        submissao = self._submissao_repo.obter_por_id(submissao_id)
        if submissao is None:
            raise EntityNotFoundError(f"Submissão {submissao_id} não encontrada")

        if not 0.0 <= nota <= 10.0:
            raise ValueError("Nota deve estar entre 0 e 10")

        correcao = Correcao(
            id=uuid4(),
            submissao_id=submissao_id,
            professor_id=professor_id,
            nota=nota,
            feedback=feedback,
        )
        return self._correcao_repo.salvar(correcao)
