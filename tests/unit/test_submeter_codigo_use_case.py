from uuid import uuid4

import pytest

from app.application.ports.engine_ia import ResultadoValidacao
from app.application.use_cases.processar_evolucao import ProcessarEvolucaoUseCase
from app.application.use_cases.submeter_codigo import SubmeterCodigoUseCase
from app.domain.entities import Aluno, Missao, Submissao
from app.domain.enums import (
    DificuldadeMissao,
    PerfilUsuario,
    StatusMissao,
    StatusSubmissao,
)
from app.domain.exceptions import EntityNotFoundError, UnauthorizedActionError


class FakeAlunoRepo:
    def __init__(self, aluno: Aluno | None) -> None:
        self._aluno = aluno

    def obter_por_id(self, aluno_id):
        return self._aluno if self._aluno and self._aluno.id == aluno_id else None

    def salvar(self, aluno: Aluno) -> Aluno:
        self._aluno = aluno
        return aluno


class FakeMissaoRepo:
    def __init__(self, missao: Missao | None) -> None:
        self._missao = missao

    def obter_por_id(self, missao_id):
        return self._missao if self._missao and self._missao.id == missao_id else None

    def listar_ativas_por_trilha(self, trilha_id: str):
        return []

    def salvar(self, missao: Missao) -> Missao:
        self._missao = missao
        return missao


class FakeSubmissaoRepo:
    def __init__(self) -> None:
        self._store: dict = {}

    def obter_por_id(self, submissao_id):
        return self._store.get(submissao_id)

    def obter_por_aluno_e_missao(self, aluno_id, missao_id):
        for s in self._store.values():
            if s.aluno_id == aluno_id and s.missao_id == missao_id:
                return s
        return None

    def salvar(self, submissao: Submissao) -> Submissao:
        self._store[submissao.id] = submissao
        return submissao


class FakeEngineAprovada:
    def validar_codigo(self, missao_id, conteudo_codigo):
        return ResultadoValidacao(aprovado=True, testes_passados=2, testes_total=2)


class FakeEngineFalha:
    def validar_codigo(self, missao_id, conteudo_codigo):
        return ResultadoValidacao(
            aprovado=False, falha_teste=True, mensagem="Teste falhou"
        )


class FakeBadgeRepo:
    def obter_por_id(self, badge_id):
        return None

    def listar_conquistadas_aluno(self, aluno_id):
        return []

    def conceder_badge(self, aluno_id, badge_id):
        from app.domain.entities import BadgeConquistada

        return BadgeConquistada(aluno_id=aluno_id, badge_id=badge_id)


class FakeRankingRepo:
    def obter_posicao_aluno(self, aluno_id):
        return 1

    def listar_top(self, offset=0, limit=10):
        return [], 0

    def atualizar_entrada(self, aluno):
        pass


class FakeTransactionManager:
    def __init__(self) -> None:
        self.iniciada = False
        self.confirmada = False

    def begin(self):
        manager = self

        class _Transaction:
            def __enter__(self):
                manager.iniciada = True

            def __exit__(self, exc_type, exc, traceback):
                manager.confirmada = exc_type is None
                return False

        return _Transaction()


def _aluno(xp: int = 4200) -> Aluno:
    return Aluno(
        id=uuid4(),
        username="OPERATIVE_01",
        email="op@test.local",
        senha_hash="hash",
        perfil=PerfilUsuario.ALUNO,
        nivel=24,
        xp_total=xp,
    )


def _missao_ativa() -> Missao:
    return Missao(
        id=uuid4(),
        titulo="Control Flow",
        descricao="Master execution paths",
        dificuldade=DificuldadeMissao.MEDIUM,
        xp_recompensa=100,
        status=StatusMissao.ATIVA,
    )


def test_submissao_aprovada_ganha_xp() -> None:
    aluno = _aluno()
    missao = _missao_ativa()
    aluno_repo = FakeAlunoRepo(aluno)
    processar = ProcessarEvolucaoUseCase(
        aluno_repo, FakeMissaoRepo(missao), FakeBadgeRepo(), FakeRankingRepo()
    )
    use_case = SubmeterCodigoUseCase(
        aluno_repo,
        FakeMissaoRepo(missao),
        FakeSubmissaoRepo(),
        FakeEngineAprovada(),
        processar,
    )
    resultado = use_case.executar(aluno.id, missao.id, "def validate(): pass")
    assert resultado.status == StatusSubmissao.FINALIZADA.value
    assert resultado.xp_ganho == 100
    assert aluno.xp_total == 4300


def test_submissao_aprovada_roda_em_transacao() -> None:
    aluno = _aluno()
    missao = _missao_ativa()
    aluno_repo = FakeAlunoRepo(aluno)
    transaction_manager = FakeTransactionManager()
    processar = ProcessarEvolucaoUseCase(
        aluno_repo, FakeMissaoRepo(missao), FakeBadgeRepo(), FakeRankingRepo()
    )
    use_case = SubmeterCodigoUseCase(
        aluno_repo,
        FakeMissaoRepo(missao),
        FakeSubmissaoRepo(),
        FakeEngineAprovada(),
        processar,
        transaction_manager=transaction_manager,
    )

    use_case.executar(aluno.id, missao.id, "def validate(): pass")

    assert transaction_manager.iniciada is True
    assert transaction_manager.confirmada is True


def test_submissao_falha_teste() -> None:
    aluno = _aluno()
    missao = _missao_ativa()
    aluno_repo = FakeAlunoRepo(aluno)
    processar = ProcessarEvolucaoUseCase(
        aluno_repo, FakeMissaoRepo(missao), FakeBadgeRepo(), FakeRankingRepo()
    )
    use_case = SubmeterCodigoUseCase(
        aluno_repo,
        FakeMissaoRepo(missao),
        FakeSubmissaoRepo(),
        FakeEngineFalha(),
        processar,
    )
    resultado = use_case.executar(aluno.id, missao.id, "FAIL_TEST")
    assert resultado.status == StatusSubmissao.FALHA_TESTE.value
    assert resultado.xp_ganho == 0


def test_retry_apos_falha_de_teste_reaproveita_submissao() -> None:
    aluno = _aluno()
    missao = _missao_ativa()
    aluno_repo = FakeAlunoRepo(aluno)
    submissao_repo = FakeSubmissaoRepo()
    processar = ProcessarEvolucaoUseCase(
        aluno_repo, FakeMissaoRepo(missao), FakeBadgeRepo(), FakeRankingRepo()
    )
    use_case_falha = SubmeterCodigoUseCase(
        aluno_repo,
        FakeMissaoRepo(missao),
        submissao_repo,
        FakeEngineFalha(),
        processar,
    )
    primeira = use_case_falha.executar(aluno.id, missao.id, "FAIL_TEST")

    use_case_sucesso = SubmeterCodigoUseCase(
        aluno_repo,
        FakeMissaoRepo(missao),
        submissao_repo,
        FakeEngineAprovada(),
        processar,
    )
    segunda = use_case_sucesso.executar(aluno.id, missao.id, "def validate(): pass")

    assert segunda.submissao_id == primeira.submissao_id
    assert segunda.status == StatusSubmissao.FINALIZADA.value
    assert aluno.xp_total == 4300


def test_missao_inativa_rejeitada() -> None:
    aluno = _aluno()
    missao = _missao_ativa()
    missao.status = StatusMissao.EM_RASCUNHO
    with pytest.raises(UnauthorizedActionError):
        SubmeterCodigoUseCase(
            FakeAlunoRepo(aluno),
            FakeMissaoRepo(missao),
            FakeSubmissaoRepo(),
            FakeEngineAprovada(),
            ProcessarEvolucaoUseCase(
                FakeAlunoRepo(aluno),
                FakeMissaoRepo(missao),
                FakeBadgeRepo(),
                FakeRankingRepo(),
            ),
        ).executar(aluno.id, missao.id, "code")


def test_aluno_inexistente() -> None:
    missao = _missao_ativa()
    with pytest.raises(EntityNotFoundError):
        SubmeterCodigoUseCase(
            FakeAlunoRepo(None),
            FakeMissaoRepo(missao),
            FakeSubmissaoRepo(),
            FakeEngineAprovada(),
            ProcessarEvolucaoUseCase(
                FakeAlunoRepo(None),
                FakeMissaoRepo(missao),
                FakeBadgeRepo(),
                FakeRankingRepo(),
            ),
        ).executar(uuid4(), missao.id, "code")
