from uuid import UUID, uuid4

from app.application.use_cases.processar_evolucao import ProcessarEvolucaoUseCase
from app.domain.entities import Aluno, BadgeConquistada, Missao
from app.domain.enums import DificuldadeMissao, PerfilUsuario, StatusMissao


class FakeAlunoRepo:
    def __init__(self, aluno: Aluno) -> None:
        self._aluno = aluno

    def obter_por_id(self, aluno_id: UUID) -> Aluno | None:
        return self._aluno if self._aluno.id == aluno_id else None

    def salvar(self, aluno: Aluno) -> Aluno:
        self._aluno = aluno
        return aluno


class FakeMissaoRepo:
    def __init__(self, missao: Missao) -> None:
        self._missao = missao

    def obter_por_id(self, missao_id: UUID) -> Missao | None:
        return self._missao if self._missao.id == missao_id else None


class FakeBadgeRepo:
    def __init__(self, conquistadas: list[BadgeConquistada] | None = None) -> None:
        self.conquistadas = conquistadas or []

    def listar_conquistadas_aluno(self, aluno_id: UUID) -> list[BadgeConquistada]:
        return self.conquistadas

    def conceder_badge(self, aluno_id: UUID, badge_id: UUID) -> BadgeConquistada:
        conquista = BadgeConquistada(aluno_id=aluno_id, badge_id=badge_id)
        self.conquistadas.append(conquista)
        return conquista


class FakeRankingRepo:
    def atualizar_entrada(self, aluno: Aluno) -> None:
        pass


def _aluno(xp_total: int, nivel: int = 1) -> Aluno:
    return Aluno(
        id=uuid4(),
        username="OPERATIVE_01",
        email="op@test.local",
        senha_hash="hash",
        perfil=PerfilUsuario.ALUNO,
        nivel=nivel,
        xp_total=xp_total,
    )


def _missao(xp_recompensa: int, badge_id=None) -> Missao:
    return Missao(
        id=uuid4(),
        titulo="Control Flow",
        descricao="Master execution paths",
        dificuldade=DificuldadeMissao.MEDIUM,
        xp_recompensa=xp_recompensa,
        status=StatusMissao.ATIVA,
        badge_id_recompensa=badge_id,
    )


def test_level_up_quando_ultrapassa_threshold_sem_multiplo_exato() -> None:
    aluno = _aluno(xp_total=4900, nivel=1)
    missao = _missao(xp_recompensa=200)
    use_case = ProcessarEvolucaoUseCase(
        FakeAlunoRepo(aluno),
        FakeMissaoRepo(missao),
        FakeBadgeRepo(),
        FakeRankingRepo(),
    )

    aluno_atualizado, xp_ganho, level_up = use_case.executar(aluno.id, missao.id)

    assert xp_ganho == 200
    assert level_up is True
    assert aluno_atualizado.xp_total == 5100
    assert aluno_atualizado.nivel == 2


def test_sem_level_up_quando_xp_insuficiente() -> None:
    aluno = _aluno(xp_total=100, nivel=1)
    missao = _missao(xp_recompensa=100)
    use_case = ProcessarEvolucaoUseCase(
        FakeAlunoRepo(aluno),
        FakeMissaoRepo(missao),
        FakeBadgeRepo(),
        FakeRankingRepo(),
    )

    aluno_atualizado, xp_ganho, level_up = use_case.executar(aluno.id, missao.id)

    assert xp_ganho == 100
    assert level_up is False
    assert aluno_atualizado.nivel == 1


def test_level_up_exato_no_threshold() -> None:
    aluno = _aluno(xp_total=4900, nivel=1)
    missao = _missao(xp_recompensa=100)
    use_case = ProcessarEvolucaoUseCase(
        FakeAlunoRepo(aluno),
        FakeMissaoRepo(missao),
        FakeBadgeRepo(),
        FakeRankingRepo(),
    )

    aluno_atualizado, xp_ganho, level_up = use_case.executar(aluno.id, missao.id)

    assert aluno_atualizado.xp_total == 5000
    assert level_up is True
    assert aluno_atualizado.nivel == 2


def test_concede_badge_nova() -> None:
    badge_id = uuid4()
    aluno = _aluno(xp_total=0)
    missao = _missao(xp_recompensa=50, badge_id=badge_id)
    badge_repo = FakeBadgeRepo()
    use_case = ProcessarEvolucaoUseCase(
        FakeAlunoRepo(aluno),
        FakeMissaoRepo(missao),
        badge_repo,
        FakeRankingRepo(),
    )

    use_case.executar(aluno.id, missao.id)

    assert len(badge_repo.conquistadas) == 1
    assert badge_repo.conquistadas[0].badge_id == badge_id


def test_nao_concede_badge_repetida() -> None:
    badge_id = uuid4()
    aluno = _aluno(xp_total=0)
    missao = _missao(xp_recompensa=100, badge_id=badge_id)
    badge_repo = FakeBadgeRepo(
        [BadgeConquistada(aluno_id=aluno.id, badge_id=badge_id)]
    )
    use_case = ProcessarEvolucaoUseCase(
        FakeAlunoRepo(aluno),
        FakeMissaoRepo(missao),
        badge_repo,
        FakeRankingRepo(),
    )

    use_case.executar(aluno.id, missao.id)

    assert len(badge_repo.conquistadas) == 1
