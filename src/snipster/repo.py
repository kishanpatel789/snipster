from abc import ABC, abstractmethod
from typing import Sequence

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
        self.snippets: dict[int, Snippet] = {}

    def add(self, snippet: Snippet) -> None:
        if snippet.id is None:
            if len(self.snippets) > 0:
                snippet.id = max(self.snippets.keys()) + 1
            else:
                snippet.id = 1
        self.snippets[snippet.id] = snippet

    def list(self) -> Sequence[Snippet]:
        return list(self.snippets.values())

    def get(self, snippet_id: int) -> Snippet | None:
        return self.snippets.get(snippet_id)

    def delete(self, snippet_id: int) -> None:
        if snippet_id in self.snippets:
            self.snippets.pop(snippet_id)
        else:
            raise SnippetNotFoundError


class DBSnippetRepository(SnippetRepository):
    pass


class JSONSnippetRepository(SnippetRepository):
    pass
