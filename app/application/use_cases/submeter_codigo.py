from uuid import UUID, uuid4

from app.application.dto import SubmissaoResultadoDTO
from app.application.ports.engine_ia import EngineIA
from app.application.ports.repositories import (
    AlunoRepository,
    MissaoRepository,
    SubmissaoRepository,
)
from app.application.use_cases.processar_evolucao import ProcessarEvolucaoUseCase
from app.domain.entities import Submissao
from app.domain.enums import StatusMissao, StatusSubmissao
from app.domain.exceptions import EntityNotFoundError, UnauthorizedActionError
from app.domain.state_machines import validar_transicao_submissao
from core.logging_config import log_use_case


class SubmeterCodigoUseCase:
    def __init__(
        self,
        aluno_repo: AlunoRepository,
        missao_repo: MissaoRepository,
        submissao_repo: SubmissaoRepository,
        engine_ia: EngineIA,
        processar_evolucao: ProcessarEvolucaoUseCase,
    ) -> None:
        self._aluno_repo = aluno_repo
        self._missao_repo = missao_repo
        self._submissao_repo = submissao_repo
        self._engine_ia = engine_ia
        self._processar_evolucao = processar_evolucao

    @log_use_case("SubmeterCodigoUseCase")
    def executar(
        self,
        aluno_id: UUID,
        missao_id: UUID,
        conteudo_codigo: str,
        submissao_id: UUID | None = None,
    ) -> SubmissaoResultadoDTO:
        aluno = self._aluno_repo.obter_por_id(aluno_id)
        if aluno is None:
            raise EntityNotFoundError(f"Aluno {aluno_id} não encontrado")

        missao = self._missao_repo.obter_por_id(missao_id)
        if missao is None:
            raise EntityNotFoundError(f"Missão {missao_id} não encontrada")

        if missao.status != StatusMissao.ATIVA:
            raise UnauthorizedActionError(
                f"Missão {missao_id} não está ativa (status: {missao.status.value})"
            )

        submissao = self._resolver_submissao(
            aluno_id, missao_id, conteudo_codigo, submissao_id
        )
        submissao.conteudo_codigo = conteudo_codigo
        submissao.alterar_status(StatusSubmissao.VALIDANDO)
        submissao = self._submissao_repo.salvar(submissao)

        resultado = self._engine_ia.validar_codigo(missao_id, conteudo_codigo)

        if resultado.falha_compilacao:
            return self._finalizar_falha(
                submissao, StatusSubmissao.FALHA_COMPILACAO, resultado.mensagem
            )

        if resultado.falha_teste or not resultado.aprovado:
            return self._finalizar_falha(
                submissao, StatusSubmissao.FALHA_TESTE, resultado.mensagem
            )

        submissao.alterar_status(StatusSubmissao.PROCESSANDO_EVOLUCAO)
        submissao = self._submissao_repo.salvar(submissao)

        aluno_atualizado, xp_ganho, level_up = self._processar_evolucao.executar(
            aluno_id, missao_id
        )

        if level_up:
            validar_transicao_submissao(
                submissao.status, StatusSubmissao.LEVEL_UP
            )
            submissao.alterar_status(StatusSubmissao.LEVEL_UP)
            submissao = self._submissao_repo.salvar(submissao)

        submissao.alterar_status(StatusSubmissao.FINALIZADA)
        submissao = self._submissao_repo.salvar(submissao)

        mensagem = (
            f"Código aprovado! +{xp_ganho} XP."
            if not level_up
            else f"Level up! Agora nível {aluno_atualizado.nivel}. +{xp_ganho} XP."
        )

        return SubmissaoResultadoDTO(
            submissao_id=submissao.id,
            status=submissao.status.value,
            xp_ganho=xp_ganho,
            level_up=level_up,
            novo_nivel=aluno_atualizado.nivel if level_up else None,
            mensagem=mensagem,
        )

    def _resolver_submissao(
        self,
        aluno_id: UUID,
        missao_id: UUID,
        conteudo_codigo: str,
        submissao_id: UUID | None,
    ) -> Submissao:
        if submissao_id is not None:
            submissao = self._submissao_repo.obter_por_id(submissao_id)
            if submissao is None:
                raise EntityNotFoundError(f"Submissão {submissao_id} não encontrada")
            if submissao.aluno_id != aluno_id:
                raise UnauthorizedActionError("Submissão não pertence ao aluno")
            return submissao

        existente = self._submissao_repo.obter_por_aluno_e_missao(aluno_id, missao_id)
        if existente is not None:
            if existente.status == StatusSubmissao.FINALIZADA:
                raise UnauthorizedActionError("Missão já concluída")
            return existente

        return Submissao(
            id=uuid4(),
            aluno_id=aluno_id,
            missao_id=missao_id,
            conteudo_codigo=conteudo_codigo,
            status=StatusSubmissao.EM_RASCUNHO,
        )

    def _finalizar_falha(
        self,
        submissao: Submissao,
        status: StatusSubmissao,
        mensagem: str,
    ) -> SubmissaoResultadoDTO:
        submissao.alterar_status(status)
        submissao = self._submissao_repo.salvar(submissao)
        return SubmissaoResultadoDTO(
            submissao_id=submissao.id,
            status=submissao.status.value,
            xp_ganho=0,
            level_up=False,
            novo_nivel=None,
            mensagem=mensagem or status.value,
        )
