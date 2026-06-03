from enum import Enum


class PerfilUsuario(str, Enum):
    ALUNO = "ALUNO"
    PROFESSOR = "PROFESSOR"
    GESTOR = "GESTOR"


class DificuldadeMissao(str, Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    BOSS = "BOSS"


class StatusMissao(str, Enum):
    EM_RASCUNHO = "EM_RASCUNHO"
    AGENDADA = "AGENDADA"
    ATIVA = "ATIVA"
    EXPIRADA = "EXPIRADA"
    SUSPENSA = "SUSPENSA"


class StatusSubmissao(str, Enum):
    EM_RASCUNHO = "EM_RASCUNHO"
    VALIDANDO = "VALIDANDO"
    FALHA_COMPILACAO = "FALHA_COMPILACAO"
    FALHA_TESTE = "FALHA_TESTE"
    PROCESSANDO_EVOLUCAO = "PROCESSANDO_EVOLUCAO"
    LEVEL_UP = "LEVEL_UP"
    FINALIZADA = "FINALIZADA"
