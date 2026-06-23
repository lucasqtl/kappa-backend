from datetime import datetime, timezone
from uuid import uuid4

from app.application.use_cases.criar_missao import CriarMissaoUseCase
from app.domain.entities import Missao
from app.domain.enums import DificuldadeMissao, StatusMissao


class FakeMissaoRepo:
    def __init__(self) -> None:
        self.salva: Missao | None = None

    def salvar(self, missao: Missao) -> Missao:
        self.salva = missao
        return missao


def test_criar_sem_agendar_retorna_em_rascunho() -> None:
    repo = FakeMissaoRepo()
    use_case = CriarMissaoUseCase(missao_repo=repo)

    missao = use_case.executar(
        titulo="Variáveis",
        descricao="Aprenda variáveis",
        dificuldade=DificuldadeMissao.EASY,
        xp_recompensa=50,
    )

    assert missao.status == StatusMissao.EM_RASCUNHO
    assert repo.salva is not None


def test_criar_com_agendar_retorna_agendada() -> None:
    repo = FakeMissaoRepo()
    use_case = CriarMissaoUseCase(missao_repo=repo)

    missao = use_case.executar(
        titulo="Loops",
        descricao="Estruturas de repetição",
        dificuldade=DificuldadeMissao.MEDIUM,
        xp_recompensa=100,
        agendar=True,
    )

    assert missao.status == StatusMissao.AGENDADA


def test_criar_com_campos_opcionais_passados_corretamente() -> None:
    repo = FakeMissaoRepo()
    use_case = CriarMissaoUseCase(missao_repo=repo)
    badge_id = uuid4()
    inicio = datetime(2025, 1, 1, tzinfo=timezone.utc)
    deadline = datetime(2025, 3, 31, tzinfo=timezone.utc)

    missao = use_case.executar(
        titulo="Funções",
        descricao="Módulos reutilizáveis",
        dificuldade=DificuldadeMissao.BOSS,
        xp_recompensa=200,
        agendar=False,
        badge_id_recompensa=badge_id,
        data_inicio=inicio,
        deadline=deadline,
        trilha_id="trilha-python",
        ordem=3,
    )

    assert missao.badge_id_recompensa == badge_id
    assert missao.data_inicio == inicio
    assert missao.deadline == deadline
    assert missao.trilha_id == "trilha-python"
    assert missao.ordem == 3
