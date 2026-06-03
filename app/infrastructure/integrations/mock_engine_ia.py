from uuid import UUID

from app.application.ports.engine_ia import ResultadoValidacao


class MockEngineIA:
    """Implementação mock da Engine IA para desenvolvimento e testes."""

    def validar_codigo(
        self, missao_id: UUID, conteudo_codigo: str
    ) -> ResultadoValidacao:
        codigo = conteudo_codigo.strip()

        if not codigo:
            return ResultadoValidacao(
                aprovado=False,
                falha_compilacao=True,
                mensagem="Código vazio — falha de compilação simulada.",
            )

        if "SyntaxError" in codigo or "raise SyntaxError" in codigo:
            return ResultadoValidacao(
                aprovado=False,
                falha_compilacao=True,
                mensagem="Erro de sintaxe detectado.",
            )

        if "FAIL_TEST" in codigo:
            return ResultadoValidacao(
                aprovado=False,
                falha_teste=True,
                mensagem="Testes falharam — lógica incorreta.",
                testes_passados=0,
                testes_total=2,
            )

        return ResultadoValidacao(
            aprovado=True,
            mensagem="Todos os testes passaram.",
            testes_passados=2,
            testes_total=2,
        )
