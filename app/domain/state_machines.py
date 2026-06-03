from app.domain.enums import StatusMissao, StatusSubmissao
from app.domain.exceptions import InvalidStateTransitionError

TRANSICOES_MISSAO: dict[StatusMissao, frozenset[StatusMissao]] = {
    StatusMissao.EM_RASCUNHO: frozenset({StatusMissao.AGENDADA, StatusMissao.SUSPENSA}),
    StatusMissao.AGENDADA: frozenset({StatusMissao.ATIVA, StatusMissao.SUSPENSA}),
    StatusMissao.ATIVA: frozenset({StatusMissao.EXPIRADA, StatusMissao.SUSPENSA}),
    StatusMissao.EXPIRADA: frozenset(),
    StatusMissao.SUSPENSA: frozenset({StatusMissao.ATIVA, StatusMissao.AGENDADA}),
}

TRANSICOES_SUBMISSAO: dict[StatusSubmissao, frozenset[StatusSubmissao]] = {
    StatusSubmissao.EM_RASCUNHO: frozenset({StatusSubmissao.VALIDANDO}),
    StatusSubmissao.VALIDANDO: frozenset(
        {
            StatusSubmissao.FALHA_COMPILACAO,
            StatusSubmissao.FALHA_TESTE,
            StatusSubmissao.PROCESSANDO_EVOLUCAO,
        }
    ),
    StatusSubmissao.FALHA_COMPILACAO: frozenset({StatusSubmissao.EM_RASCUNHO}),
    StatusSubmissao.FALHA_TESTE: frozenset({StatusSubmissao.EM_RASCUNHO}),
    StatusSubmissao.PROCESSANDO_EVOLUCAO: frozenset(
        {StatusSubmissao.LEVEL_UP, StatusSubmissao.FINALIZADA}
    ),
    StatusSubmissao.LEVEL_UP: frozenset({StatusSubmissao.FINALIZADA}),
    StatusSubmissao.FINALIZADA: frozenset(),
}


def validar_transicao_missao(atual: StatusMissao, novo: StatusMissao) -> None:
    if atual == novo:
        return
    permitidos = TRANSICOES_MISSAO.get(atual, frozenset())
    if novo not in permitidos:
        raise InvalidStateTransitionError(
            f"Transição de missão inválida: {atual.value} -> {novo.value}"
        )


def validar_transicao_submissao(atual: StatusSubmissao, novo: StatusSubmissao) -> None:
    if atual == novo:
        return
    permitidos = TRANSICOES_SUBMISSAO.get(atual, frozenset())
    if novo not in permitidos:
        raise InvalidStateTransitionError(
            f"Transição de submissão inválida: {atual.value} -> {novo.value}"
        )
