from abc import ABC, abstractmethod
from typing import Sequence

from sqlalchemy import Engine  # for typing
from sqlmodel import Session, select

from .exceptions import SnippetNotFoundError
from .models import Snippet


class SnippetRepository(ABC):  # pragma: no cover
    @abstractmethod
    def add(self, snippet: Snippet) -> None:
        pass

    @abstractmethod
    def list(self) -> Sequence[Snippet]:
        pass

    @abstractmethod
    def get(self, snippet_id: int) -> Snippet | None:
        pass

    @abstractmethod
    def delete(self, snippet_id: int) -> None:
        pass


class InMemorySnippetRepository(SnippetRepository):
    def __init__(self) -> None:
        self._snippets: dict[int, Snippet] = {}

    def add(self, snippet: Snippet) -> None:
        if snippet.id is None:
            snippet.id = max(self._snippets.keys(), default=0) + 1
        self._snippets[snippet.id] = snippet

    def list(self) -> Sequence[Snippet]:
        return list(self._snippets.values())

    def get(self, snippet_id: int) -> Snippet | None:
        return self._snippets.get(snippet_id)

    def delete(self, snippet_id: int) -> None:
        if snippet_id in self._snippets:
            self._snippets.pop(snippet_id)
        else:
            raise SnippetNotFoundError


class DBSnippetRepository(SnippetRepository):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add(self, snippet: Snippet) -> None:
        with Session(self._engine) as session:
            session.add(snippet)
            session.commit()
            session.refresh(snippet)

    def list(self) -> Sequence[Snippet]:
        with Session(self._engine) as session:
            snippets = session.exec(select(Snippet)).all()
        return snippets

    def get(self, snippet_id: int) -> Snippet | None:
        with Session(self._engine) as session:
            snippet = session.get(Snippet, snippet_id)
        return snippet

    def delete(self, snippet_id: int) -> None:
        with Session(self._engine) as session:
            snippet = session.get(Snippet, snippet_id)
            if snippet is not None:
                session.delete(snippet)
                session.commit()
            else:
                raise SnippetNotFoundError


class JSONSnippetRepository(SnippetRepository):
    pass
