class DomainError(Exception):
    """Erro base do domínio."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class EntityNotFoundError(DomainError):
    """Entidade não encontrada."""


class InvalidStateTransitionError(DomainError):
    """Transição de estado inválida."""


class UnauthorizedActionError(DomainError):
    """Ação não permitida para o perfil ou contexto atual."""


class CredentialsError(DomainError):
    """Credenciais inválidas."""
