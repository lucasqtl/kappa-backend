from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy.orm import Session


class SqlAlchemyTransactionManager:
    def __init__(self, session: Session) -> None:
        self._session = session

    @contextmanager
    def begin(self) -> Iterator[None]:
        """Executa o bloco como uma unidade de trabalho atômica.

        Faz commit ao final em caso de sucesso e rollback em caso de erro.
        Funciona mesmo quando a sessão já abriu uma transação implícita
        (autobegin) — por exemplo, por uma query de autenticação executada
        antes na mesma sessão do request. Depender de ``session.begin()`` aqui
        seria incorreto: se a transação já estivesse aberta, o commit nunca
        aconteceria e os dados do request seriam descartados no ``close()``.
        """
        try:
            yield
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise
