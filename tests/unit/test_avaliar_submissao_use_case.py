from uuid import UUID, uuid4

import pytest

from app.application.use_cases.avaliar_submissao import AvaliarSubmissaoUseCase
from app.domain.entities import Correcao, Submissao
from app.domain.exceptions import DomainError


class FakeSubmissaoRepo:
    def __init__(self, submissao: Submissao | None) -> None:
        self._submissao = submissao

    def obter_por_id(self, submissao_id: UUID) -> Submissao | None:
        if self._submissao is None or self._submissao.id != submissao_id:
            return None
        return self._submissao


class FakeCorrecaoRepo:
    def __init__(self) -> None:
        self.salvas: list[Correcao] = []

    def salvar(self, correcao: Correcao) -> Correcao:
        self.salvas.append(correcao)
        return correcao


def test_avalia_submissao_com_nota_valida() -> None:
    submissao = Submissao(
        id=uuid4(),
        aluno_id=uuid4(),
        missao_id=uuid4(),
        conteudo_codigo="print('ok')",
    )
    correcao_repo = FakeCorrecaoRepo()
    use_case = AvaliarSubmissaoUseCase(
        submissao_repo=FakeSubmissaoRepo(submissao),
        correcao_repo=correcao_repo,
    )

    correcao = use_case.executar(
        submissao_id=submissao.id,
        professor_id=uuid4(),
        nota=8.5,
        feedback="Boa solucao.",
    )

    assert correcao.nota == 8.5
    assert len(correcao_repo.salvas) == 1


def test_rejeita_nota_fora_do_intervalo_no_dominio() -> None:
    submissao = Submissao(
        id=uuid4(),
        aluno_id=uuid4(),
        missao_id=uuid4(),
        conteudo_codigo="print('ok')",
    )
    correcao_repo = FakeCorrecaoRepo()
    use_case = AvaliarSubmissaoUseCase(
        submissao_repo=FakeSubmissaoRepo(submissao),
        correcao_repo=correcao_repo,
    )

    with pytest.raises(DomainError, match="Nota deve estar entre 0 e 10"):
        use_case.executar(
            submissao_id=submissao.id,
            professor_id=uuid4(),
            nota=10.1,
            feedback="Revise a nota.",
        )

    assert correcao_repo.salvas == []
