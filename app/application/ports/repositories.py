from typing import Protocol
from uuid import UUID

from app.domain.entities import (
    Aluno,
    Badge,
    BadgeConquistada,
    Correcao,
    EntradaRanking,
    Missao,
    ProgressoMissao,
    Submissao,
)


class AlunoRepository(Protocol):
    def obter_por_id(self, aluno_id: UUID) -> Aluno | None: ...

    def salvar(self, aluno: Aluno) -> Aluno: ...


class MissaoRepository(Protocol):
    def obter_por_id(self, missao_id: UUID) -> Missao | None: ...

    def listar_ativas_por_trilha(self, trilha_id: str) -> list[Missao]: ...

    def salvar(self, missao: Missao) -> Missao: ...


class SubmissaoRepository(Protocol):
    def obter_por_id(self, submissao_id: UUID) -> Submissao | None: ...

    def obter_por_aluno_e_missao(
        self, aluno_id: UUID, missao_id: UUID
    ) -> Submissao | None: ...

    def salvar(self, submissao: Submissao) -> Submissao: ...


class ProgressoMissaoRepository(Protocol):
    def listar_progresso_aluno(
        self, aluno_id: UUID, trilha_id: str | None = None
    ) -> list[ProgressoMissao]: ...


class RankingRepository(Protocol):
    def obter_posicao_aluno(self, aluno_id: UUID) -> int | None: ...

    def listar_top(self, limite: int = 10) -> list[EntradaRanking]: ...

    def atualizar_entrada(self, aluno: Aluno) -> None: ...


class BadgeRepository(Protocol):
    def obter_por_id(self, badge_id: UUID) -> Badge | None: ...

    def listar_conquistadas_aluno(self, aluno_id: UUID) -> list[BadgeConquistada]: ...

    def conceder_badge(self, aluno_id: UUID, badge_id: UUID) -> BadgeConquistada: ...


class CorrecaoRepository(Protocol):
    def salvar(self, correcao: Correcao) -> Correcao: ...
