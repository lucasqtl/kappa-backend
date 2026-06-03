import pytest

from app.domain.enums import StatusMissao, StatusSubmissao
from app.domain.exceptions import InvalidStateTransitionError
from app.domain.state_machines import (
    validar_transicao_missao,
    validar_transicao_submissao,
)


def test_transicao_missao_rascunho_para_agendada() -> None:
    validar_transicao_missao(StatusMissao.EM_RASCUNHO, StatusMissao.AGENDADA)


def test_transicao_missao_invalida() -> None:
    with pytest.raises(InvalidStateTransitionError):
        validar_transicao_missao(StatusMissao.EM_RASCUNHO, StatusMissao.ATIVA)


def test_fluxo_submissao_sucesso() -> None:
    validar_transicao_submissao(
        StatusSubmissao.EM_RASCUNHO, StatusSubmissao.VALIDANDO
    )
    validar_transicao_submissao(
        StatusSubmissao.VALIDANDO, StatusSubmissao.PROCESSANDO_EVOLUCAO
    )
    validar_transicao_submissao(
        StatusSubmissao.PROCESSANDO_EVOLUCAO, StatusSubmissao.FINALIZADA
    )


def test_transicao_submissao_invalida() -> None:
    with pytest.raises(InvalidStateTransitionError):
        validar_transicao_submissao(
            StatusSubmissao.EM_RASCUNHO, StatusSubmissao.FINALIZADA
        )
