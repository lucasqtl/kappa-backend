from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from app.domain.enums import (
    DificuldadeMissao,
    PerfilUsuario,
    StatusMissao,
    StatusSubmissao,
)
from app.domain.state_machines import (
    validar_transicao_missao,
    validar_transicao_submissao,
)


@dataclass
class Usuario:
    id: UUID
    username: str
    email: str
    senha_hash: str
    perfil: PerfilUsuario


@dataclass
class Aluno(Usuario):
    nivel: int = 1
    xp_total: int = 0
    xp_semana: int = 0
    dias_ofensiva: int = 0

    def xp_no_nivel_atual(self, xp_por_nivel: int = 5000) -> int:
        return self.xp_total % xp_por_nivel

    def xp_para_proximo_nivel(self, xp_por_nivel: int = 5000) -> int:
        """XP restante até o próximo nível (barra 4200/5000 → 800 restantes)."""
        resto = self.xp_no_nivel_atual(xp_por_nivel)
        return xp_por_nivel - resto if resto != 0 else 0

@dataclass
class Professor(Usuario):
    departamento: str | None = None


@dataclass
class Missao:
    id: UUID
    titulo: str
    descricao: str
    dificuldade: DificuldadeMissao
    xp_recompensa: int
    status: StatusMissao
    badge_id_recompensa: UUID | None = None
    data_inicio: datetime | None = None
    deadline: datetime | None = None
    trilha_id: str | None = None
    ordem: int = 0

    def alterar_status(self, novo_status: StatusMissao) -> None:
        validar_transicao_missao(self.status, novo_status)
        self.status = novo_status


@dataclass
class Submissao:
    id: UUID
    aluno_id: UUID
    missao_id: UUID
    conteudo_codigo: str
    status: StatusSubmissao = StatusSubmissao.EM_RASCUNHO
    criado_em: datetime = field(default_factory=datetime.utcnow)
    atualizado_em: datetime = field(default_factory=datetime.utcnow)

    def alterar_status(self, novo_status: StatusSubmissao) -> None:
        validar_transicao_submissao(self.status, novo_status)
        self.status = novo_status
        self.atualizado_em = datetime.utcnow()


@dataclass
class Correcao:
    id: UUID
    submissao_id: UUID
    professor_id: UUID
    nota: float
    feedback: str
    criado_em: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Badge:
    id: UUID
    codigo: str
    nome: str
    descricao: str
    icone_url: str | None = None


@dataclass
class BadgeConquistada:
    aluno_id: UUID
    badge_id: UUID
    conquistado_em: datetime = field(default_factory=datetime.utcnow)


@dataclass
class EntradaRanking:
    aluno_id: UUID
    username: str
    xp_total: int
    posicao: int


@dataclass
class ProgressoMissao:
    """Estado da missão para um aluno específico (visão do dashboard)."""

    missao: Missao
    progresso_percentual: int
    bloqueada: bool
    motivo_bloqueio: str | None = None
    submissao_id: UUID | None = None
