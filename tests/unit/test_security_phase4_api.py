from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from app.application.dto import DashboardAlunoDTO
from app.domain.entities import Correcao, Missao, Usuario
from app.domain.enums import DificuldadeMissao, PerfilUsuario, StatusMissao
from app.presentation import dependencies
from core.config import Settings
from main import app


ALUNO_ID = uuid4()
OUTRO_ALUNO_ID = uuid4()
PROFESSOR_ID = uuid4()
GESTOR_ID = uuid4()
MISSAO_ID = uuid4()
SUBMISSAO_ID = uuid4()


def _usuario(user_id: UUID, perfil: PerfilUsuario) -> Usuario:
    return Usuario(
        id=user_id,
        username=perfil.value.lower(),
        email=f"{perfil.value.lower()}@test.local",
        senha_hash="hash",
        perfil=perfil,
    )


ALUNO = _usuario(ALUNO_ID, PerfilUsuario.ALUNO)
OUTRO_ALUNO = _usuario(OUTRO_ALUNO_ID, PerfilUsuario.ALUNO)
PROFESSOR = _usuario(PROFESSOR_ID, PerfilUsuario.PROFESSOR)
GESTOR = _usuario(GESTOR_ID, PerfilUsuario.GESTOR)


def _missao(status: StatusMissao = StatusMissao.EM_RASCUNHO) -> Missao:
    return Missao(
        id=MISSAO_ID,
        titulo="Loops",
        descricao="Treine repeticoes.",
        dificuldade=DificuldadeMissao.EASY,
        xp_recompensa=100,
        status=status,
    )


class FakeCriarMissaoUseCase:
    def executar(self, **kwargs) -> Missao:
        return Missao(
            id=MISSAO_ID,
            titulo=kwargs["titulo"],
            descricao=kwargs["descricao"],
            dificuldade=kwargs["dificuldade"],
            xp_recompensa=kwargs["xp_recompensa"],
            status=StatusMissao.EM_RASCUNHO,
            badge_id_recompensa=kwargs.get("badge_id_recompensa"),
            data_inicio=kwargs.get("data_inicio"),
            deadline=kwargs.get("deadline"),
            trilha_id=kwargs.get("trilha_id"),
            ordem=kwargs.get("ordem", 0),
        )


class FakeMissaoRepo:
    def __init__(self, missao: Missao | None = None) -> None:
        self.missao = missao or _missao()
        self.deletada: UUID | None = None

    def obter_por_id(self, missao_id: UUID) -> Missao | None:
        return self.missao if missao_id == self.missao.id else None

    def salvar(self, missao: Missao) -> Missao:
        self.missao = missao
        return missao

    def deletar(self, missao_id: UUID) -> None:
        self.deletada = missao_id


class FakeDashboardUseCase:
    def executar(self, aluno_id: UUID, trilha_id: str | None = None) -> DashboardAlunoDTO:
        return DashboardAlunoDTO(
            aluno_id=aluno_id,
            username="aluno",
            nivel=1,
            xp_total=0,
            xp_para_proximo_nivel=0,
            xp_semana=0,
            dias_ofensiva=0,
            titulo_rank="Iniciante",
            objetivo_atual="Comecar",
            missoes=[],
            posicao_ranking=None,
            ranking_top=[],
        )


class FakeSubmeterCodigoUseCase:
    def executar(self, aluno_id, missao_id, conteudo_codigo, submissao_id=None):
        from app.application.dto import SubmissaoResultadoDTO

        return SubmissaoResultadoDTO(
            submissao_id=uuid4(),
            status="FINALIZADA",
            xp_ganho=100,
            level_up=False,
            novo_nivel=None,
            mensagem="Todos os testes passaram.",
        )


class FakeAvaliarSubmissaoUseCase:
    def __init__(self) -> None:
        self.professor_id: UUID | None = None

    def executar(
        self,
        submissao_id: UUID,
        professor_id: UUID,
        nota: float,
        feedback: str,
    ) -> Correcao:
        self.professor_id = professor_id
        return Correcao(
            id=uuid4(),
            submissao_id=submissao_id,
            professor_id=professor_id,
            nota=nota,
            feedback=feedback,
        )


@pytest.fixture(autouse=True)
def _clean_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _autenticar_com(usuario: Usuario) -> None:
    app.dependency_overrides[dependencies.get_current_user] = lambda: usuario


def _payload_missao() -> dict[str, object]:
    return {
        "titulo": "Loops",
        "descricao": "Treine repeticoes.",
        "dificuldade": "EASY",
        "xp_recompensa": 100,
    }


def test_aluno_nao_cria_missao(client: TestClient) -> None:
    _autenticar_com(ALUNO)
    app.dependency_overrides[dependencies.get_criar_missao_use_case] = (
        lambda: FakeCriarMissaoUseCase()
    )

    response = client.post("/api/v1/missoes", json=_payload_missao())

    assert response.status_code == 403


def test_professor_cria_edita_e_altera_status_missao(client: TestClient) -> None:
    _autenticar_com(PROFESSOR)
    repo = FakeMissaoRepo(_missao())
    app.dependency_overrides[dependencies.get_criar_missao_use_case] = (
        lambda: FakeCriarMissaoUseCase()
    )
    app.dependency_overrides[dependencies.get_missao_repo] = lambda: repo

    create_response = client.post("/api/v1/missoes", json=_payload_missao())
    update_response = client.put(
        f"/api/v1/missoes/{MISSAO_ID}",
        json={"titulo": "Loops atualizados"},
    )
    patch_response = client.patch(
        f"/api/v1/missoes/{MISSAO_ID}/status",
        json={"novo_status": "AGENDADA"},
    )

    assert create_response.status_code == 201
    assert update_response.status_code == 200
    assert update_response.json()["titulo"] == "Loops atualizados"
    assert patch_response.status_code == 200
    assert patch_response.json()["status"] == "AGENDADA"


def test_professor_nao_deleta_missao(client: TestClient) -> None:
    _autenticar_com(PROFESSOR)
    app.dependency_overrides[dependencies.get_missao_repo] = lambda: FakeMissaoRepo()

    response = client.delete(f"/api/v1/missoes/{MISSAO_ID}")

    assert response.status_code == 403


def test_gestor_deleta_missao_em_rascunho(client: TestClient) -> None:
    _autenticar_com(GESTOR)
    repo = FakeMissaoRepo(_missao(StatusMissao.EM_RASCUNHO))
    app.dependency_overrides[dependencies.get_missao_repo] = lambda: repo

    response = client.delete(f"/api/v1/missoes/{MISSAO_ID}")

    assert response.status_code == 204
    assert repo.deletada == MISSAO_ID


def test_aluno_nao_acessa_dashboard_de_outro_aluno(client: TestClient) -> None:
    _autenticar_com(ALUNO)
    app.dependency_overrides[dependencies.get_obter_dashboard_use_case] = (
        lambda: FakeDashboardUseCase()
    )

    response = client.get(f"/api/v1/alunos/{OUTRO_ALUNO_ID}/dashboard")

    assert response.status_code == 403


def test_professor_nao_acessa_dashboard_como_aluno(client: TestClient) -> None:
    _autenticar_com(PROFESSOR)
    app.dependency_overrides[dependencies.get_obter_dashboard_use_case] = (
        lambda: FakeDashboardUseCase()
    )

    response = client.get(f"/api/v1/alunos/{ALUNO_ID}/dashboard")

    assert response.status_code == 403


def test_avaliacao_usa_professor_do_token(client: TestClient) -> None:
    _autenticar_com(PROFESSOR)
    use_case = FakeAvaliarSubmissaoUseCase()
    app.dependency_overrides[dependencies.get_avaliar_submissao_use_case] = (
        lambda: use_case
    )

    response = client.post(
        f"/api/v1/missoes/submissoes/{SUBMISSAO_ID}/avaliar",
        json={"nota": 9.0, "feedback": "Muito bom."},
    )

    assert response.status_code == 201
    assert use_case.professor_id == PROFESSOR_ID


def test_avaliacao_rejeita_nota_invalida(client: TestClient) -> None:
    _autenticar_com(PROFESSOR)
    app.dependency_overrides[dependencies.get_avaliar_submissao_use_case] = (
        lambda: FakeAvaliarSubmissaoUseCase()
    )

    response = client.post(
        f"/api/v1/missoes/submissoes/{SUBMISSAO_ID}/avaliar",
        json={"nota": 10.1, "feedback": "Nota invalida."},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Nota deve estar entre 0 e 10"


def test_obter_missao_nao_encontrada_retorna_404(client: TestClient) -> None:
    _autenticar_com(PROFESSOR)
    app.dependency_overrides[dependencies.get_missao_repo] = lambda: FakeMissaoRepo()

    response = client.get(f"/api/v1/missoes/{uuid4()}")

    assert response.status_code == 404


def test_alterar_status_transicao_invalida_retorna_409(client: TestClient) -> None:
    _autenticar_com(PROFESSOR)
    repo = FakeMissaoRepo(_missao(StatusMissao.EM_RASCUNHO))
    app.dependency_overrides[dependencies.get_missao_repo] = lambda: repo

    response = client.patch(
        f"/api/v1/missoes/{MISSAO_ID}/status",
        json={"novo_status": "EXPIRADA"},
    )

    assert response.status_code == 409


def test_aluno_submete_codigo_para_missao(client: TestClient) -> None:
    _autenticar_com(ALUNO)
    app.dependency_overrides[dependencies.get_submeter_codigo_use_case] = (
        lambda: FakeSubmeterCodigoUseCase()
    )

    response = client.post(
        f"/api/v1/missoes/{MISSAO_ID}/submeter",
        params={"aluno_id": str(ALUNO_ID)},
        json={"conteudo_codigo": "print('hello')"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "FINALIZADA"
    assert response.json()["xp_ganho"] == 100


def test_cors_permite_wildcard_em_debug() -> None:
    test_app = FastAPI()
    settings = Settings(debug=True)
    assert settings.cors_origins == ["*"]
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @test_app.get("/")
    def root() -> dict[str, str]:
        return {"status": "ok"}

    response = TestClient(test_app).get("/", headers={"Origin": "https://front.test"})

    assert response.headers["access-control-allow-origin"] == "https://front.test"


def test_cors_usa_origens_configuradas_fora_de_debug() -> None:
    test_app = FastAPI()
    settings = Settings(
        debug=False,
        cors_allow_origins="https://front.test,https://admin.test",
    )
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @test_app.get("/")
    def root() -> dict[str, str]:
        return {"status": "ok"}

    client = TestClient(test_app)
    allowed = client.get("/", headers={"Origin": "https://front.test"})
    blocked = client.get("/", headers={"Origin": "https://evil.test"})

    assert allowed.headers["access-control-allow-origin"] == "https://front.test"
    assert "access-control-allow-origin" not in blocked.headers
