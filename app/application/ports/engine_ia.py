from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True)
class ResultadoValidacao:
    aprovado: bool
    falha_compilacao: bool = False
    falha_teste: bool = False
    mensagem: str = ""
    testes_passados: int = 0
    testes_total: int = 0


class EngineIA(Protocol):
    """Porta para validação automática de código (Engine IA / test suite)."""

    def validar_codigo(
        self, missao_id: UUID, conteudo_codigo: str
    ) -> ResultadoValidacao: ...
