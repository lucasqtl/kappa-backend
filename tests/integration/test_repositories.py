from uuid import uuid4

import pytest

from app.domain.entities import Aluno, Missao
from app.domain.enums import DificuldadeMissao, PerfilUsuario, StatusMissao
from app.infrastructure.database.models import MissaoModel
from app.infrastructure.database.unit_of_work import SqlAlchemyTransactionManager
from app.infrastructure.repositories.sqlalchemy_aluno_repository import (
    SqlAlchemyAlunoRepository,
)
from app.infrastructure.repositories.sqlalchemy_missao_repository import (
    SqlAlchemyMissaoRepository,
)
from app.infrastructure.repositories.sqlalchemy_ranking_repository import (
    SqlAlchemyRankingRepository,
)


def _missao(status: StatusMissao = StatusMissao.EM_RASCUNHO) -> Missao:
    return Missao(
        id=uuid4(),
        titulo="Missão Teste",
        descricao="Descrição de teste",
        dificuldade=DificuldadeMissao.EASY,
        xp_recompensa=100,
        status=status,
    )


def _aluno(xp_total: int = 0) -> Aluno:
    uid = uuid4()
    return Aluno(
        id=uid,
        username=f"aluno_{uid.hex[:6]}",
        email=f"{uid.hex[:6]}@test.local",
        senha_hash="hash",
        perfil=PerfilUsuario.ALUNO,
        xp_total=xp_total,
    )


def test_missao_repository_salva_e_recupera(db_session) -> None:
    repo = SqlAlchemyMissaoRepository(db_session)
    missao = _missao()

    salva = repo.salvar(missao)
    recuperada = repo.obter_por_id(salva.id)

    assert recuperada is not None
    assert recuperada.id == salva.id
    assert recuperada.titulo == "Missão Teste"
    assert recuperada.status == StatusMissao.EM_RASCUNHO


def test_missao_repository_listar_com_paginacao(db_session) -> None:
    repo = SqlAlchemyMissaoRepository(db_session)
    for i in range(3):
        m = _missao()
        m.titulo = f"Missão {i}"
        repo.salvar(m)

    items, total = repo.listar_todas(offset=0, limit=2)

    assert total == 3
    assert len(items) == 2


def test_missao_repository_listar_com_filtro_status(db_session) -> None:
    repo = SqlAlchemyMissaoRepository(db_session)
    repo.salvar(_missao(status=StatusMissao.EM_RASCUNHO))
    repo.salvar(_missao(status=StatusMissao.EM_RASCUNHO))
    repo.salvar(_missao(status=StatusMissao.ATIVA))

    items, total = repo.listar_todas(status=StatusMissao.EM_RASCUNHO)

    assert total == 2
    assert all(m.status == StatusMissao.EM_RASCUNHO for m in items)


def test_aluno_repository_criar_e_obter(db_session) -> None:
    repo = SqlAlchemyAlunoRepository(db_session)
    aluno = _aluno(xp_total=500)

    criado = repo.criar(aluno)
    obtido = repo.obter_por_id(criado.id)

    assert obtido is not None
    assert obtido.xp_total == 500
    assert obtido.perfil == PerfilUsuario.ALUNO


def test_transaction_manager_commit_persiste_dados(db_session) -> None:
    repo = SqlAlchemyMissaoRepository(db_session, auto_commit=False)
    tm = SqlAlchemyTransactionManager(db_session)
    missao = _missao()

    with tm.begin():
        repo.salvar(missao)

    recuperada = db_session.get(MissaoModel, missao.id)
    assert recuperada is not None
    assert recuperada.titulo == "Missão Teste"


def test_transaction_manager_rollback_descarta_em_excecao(db_session) -> None:
    repo = SqlAlchemyMissaoRepository(db_session, auto_commit=False)
    tm = SqlAlchemyTransactionManager(db_session)
    missao = _missao()

    with pytest.raises(RuntimeError):
        with tm.begin():
            repo.salvar(missao)
            raise RuntimeError("falha simulada")

    recuperada = db_session.get(MissaoModel, missao.id)
    assert recuperada is None


def test_ranking_repository_listar_top_paginado(db_session) -> None:
    aluno_repo = SqlAlchemyAlunoRepository(db_session)
    ranking_repo = SqlAlchemyRankingRepository(db_session)

    a1 = _aluno(xp_total=1000)
    a2 = _aluno(xp_total=2000)
    a3 = _aluno(xp_total=500)
    for a in [a1, a2, a3]:
        aluno_repo.criar(a)

    top2, total = ranking_repo.listar_top(offset=0, limit=2)

    assert total == 3
    assert len(top2) == 2
    assert top2[0].xp_total == 2000
    assert top2[0].posicao == 1
    assert top2[1].xp_total == 1000
    assert top2[1].posicao == 2
