from contextlib import AbstractContextManager
from typing import Protocol
from uuid import UUID

from app.domain.entities import (
    Aluno,
    Badge,
    BadgeConquistada,
    Correcao,
    EntradaRanking,
    Missao,
    Professor,
    ProgressoMissao,
    Submissao,
)
from app.domain.enums import DificuldadeMissao, StatusMissao


class AlunoRepository(Protocol):
    def obter_por_id(self, aluno_id: UUID) -> Aluno | None: ...

    def obter_por_email(self, email: str) -> Aluno | None: ...

    def listar(self, offset: int = 0, limit: int = 20) -> tuple[list[Aluno], int]: ...

    def criar(self, aluno: Aluno) -> Aluno: ...

    def salvar(self, aluno: Aluno) -> Aluno: ...


class MissaoRepository(Protocol):
    def obter_por_id(self, missao_id: UUID) -> Missao | None: ...

    def listar_ativas_por_trilha(self, trilha_id: str) -> list[Missao]: ...

    def listar_todas(
        self,
        status: StatusMissao | None = None,
        dificuldade: DificuldadeMissao | None = None,
        trilha_id: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Missao], int]: ...

    def listar(
        self,
        status: StatusMissao | None = None,
        trilha_id: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Missao], int]: ...

    def deletar(self, missao_id: UUID) -> None: ...

    def salvar(self, missao: Missao) -> Missao: ...


class SubmissaoRepository(Protocol):
    def obter_por_id(self, submissao_id: UUID) -> Submissao | None: ...

    def obter_por_aluno_e_missao(
        self, aluno_id: UUID, missao_id: UUID
    ) -> Submissao | None: ...

    def listar_por_aluno(
        self, aluno_id: UUID, offset: int = 0, limit: int = 20
    ) -> tuple[list[Submissao], int]: ...

    def salvar(self, submissao: Submissao) -> Submissao: ...


class ProgressoMissaoRepository(Protocol):
    def listar_progresso_aluno(
        self, aluno_id: UUID, trilha_id: str | None = None
    ) -> list[ProgressoMissao]: ...


class RankingRepository(Protocol):
    def obter_posicao_aluno(self, aluno_id: UUID) -> int | None: ...

    def listar_top(
        self, offset: int = 0, limit: int = 10
    ) -> tuple[list[EntradaRanking], int]: ...

    def atualizar_entrada(self, aluno: Aluno) -> None: ...


class BadgeRepository(Protocol):
    def obter_por_id(self, badge_id: UUID) -> Badge | None: ...

    def listar_conquistadas_aluno(self, aluno_id: UUID) -> list[BadgeConquistada]: ...

    def listar_badges_detalhes(
        self, aluno_id: UUID
    ) -> list[tuple[Badge, BadgeConquistada]]: ...

    def conceder_badge(self, aluno_id: UUID, badge_id: UUID) -> BadgeConquistada: ...


class CorrecaoRepository(Protocol):
    def salvar(self, correcao: Correcao) -> Correcao: ...


class ProfessorRepository(Protocol):
    def obter_por_id(self, professor_id: UUID) -> Professor | None: ...

    def criar(self, professor: Professor) -> Professor: ...


class TransactionManager(Protocol):
    def begin(self) -> AbstractContextManager[None]: ...
