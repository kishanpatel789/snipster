import json
from abc import ABC, abstractmethod
from pathlib import Path
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
    def __init__(self, file_dir: Path) -> None:
        self._file_path = file_dir / "snippets.json"

        if not self._file_path.exists():
            self._file_path.write_text("{}")

    def _read(self) -> dict[str, Snippet]:
        try:
            with open(self._file_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _write(self, data: dict) -> None:
        with open(self._file_path, "w") as f:
            return json.dump(data, f, indent=4)

    def add(self, snippet: Snippet) -> None:
        data = self._read()
        existing_ids = [int(k) for k in data.keys()]
        if snippet.id is None:
            snippet.id = max(existing_ids, default=0) + 1
        data[str(snippet.id)] = snippet.model_dump(mode="json")
        self._write(data)

    def list(self) -> Sequence[Snippet]:
        data = self._read()
        return [Snippet.model_validate(snippet_dict) for snippet_dict in data.values()]

    def get(self, snippet_id: int) -> Snippet | None:
        snippet_dict = self._read().get(str(snippet_id))
        if snippet_dict is not None:
            return Snippet.model_validate(snippet_dict)

    def delete(self, snippet_id: int) -> None:
        data = self._read()
        if str(snippet_id) in data:
            del data[str(snippet_id)]
            self._write(data)
        else:
            raise SnippetNotFoundError
