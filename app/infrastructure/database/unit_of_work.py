from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy.orm import Session


class SqlAlchemyTransactionManager:
    def __init__(self, session: Session) -> None:
        self._session = session

    @contextmanager
    def begin(self) -> Iterator[None]:
        if self._session.in_transaction():
            yield
            return

        with self._session.begin():
            yield
