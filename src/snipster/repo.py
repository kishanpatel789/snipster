import json
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Sequence

from sqlalchemy import Engine  # for typing
from sqlmodel import Session, or_, select

from .exceptions import SnippetNotFoundError
from .models import LangEnum, Snippet, Tag


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

    @abstractmethod
    def search(
        self, term: str, language: LangEnum | None = None, fuzzy: bool = False
    ) -> Sequence[Snippet]:
        pass

    @abstractmethod
    def toggle_favorite(self, snippet_id: int) -> None:
        pass

    @abstractmethod
    def tag(self, snippet_id: int, /, *tags: Tag, remove: bool = False) -> None:
        pass

    def _fuzzy_search(
        self, snippets: Sequence[Snippet], term: str, language: LangEnum | None = None
    ) -> Sequence[Snippet]:
        PASS_THRESHOLD = 0.6
        results = []
        for snippet in snippets:
            if any(
                [
                    SequenceMatcher(a=term, b=snippet.title.lower()).ratio()
                    >= PASS_THRESHOLD,
                    SequenceMatcher(a=term, b=snippet.code.lower()).ratio()
                    >= PASS_THRESHOLD,
                    SequenceMatcher(a=term, b=snippet.description.lower()).ratio()
                    >= PASS_THRESHOLD,
                ]
            ):
                if language is None or snippet.language == language:
                    results.append(snippet)
        return results

    def _update_tags(self, snippet: Snippet, tags: Sequence[Tag], remove: bool) -> None:
        if remove:
            snippet.tags = [tag for tag in snippet.tags if tag not in tags]
        else:
            for tag in tags:
                if tag not in snippet.tags:
                    snippet.tags.append(tag)
        snippet.updated_at = datetime.now(timezone.utc)
        return snippet


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

    def search(
        self, term: str, language: LangEnum | None = None, fuzzy: bool = False
    ) -> Sequence[Snippet]:
        snippets = self._snippets.values()
        term_lower = term.lower()

        if fuzzy:
            return self._fuzzy_search(snippets, term_lower, language)
        else:
            results = []
            for snippet in snippets:
                if any(
                    [
                        term_lower in snippet.title.lower(),
                        term_lower in snippet.code.lower(),
                        term_lower in snippet.description.lower(),
                    ]
                ):
                    if language is None or snippet.language == language:
                        results.append(snippet)
            return results

    def toggle_favorite(self, snippet_id: int) -> None:
        snippet = self.get(snippet_id)
        if snippet is None:
            raise SnippetNotFoundError
        snippet.favorite = not snippet.favorite
        snippet.updated_at = datetime.now(timezone.utc)

    def tag(self, snippet_id: int, /, *tags: Tag, remove: bool = False) -> None:
        snippet = self.get(snippet_id)
        if snippet is None:
            raise SnippetNotFoundError
        self._update_tags(snippet, tags, remove)


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

    def search(
        self, term: str, language: LangEnum | None = None, fuzzy: bool = False
    ) -> Sequence[Snippet]:
        term_lower = term.lower()

        if fuzzy:
            with Session(self._engine) as session:
                all_records = session.exec(select(Snippet)).all()
                results = self._fuzzy_search(all_records, term_lower, language)
                return results
        else:
            results = []
            with Session(self._engine) as session:
                query = select(Snippet).where(
                    or_(
                        Snippet.title.ilike(f"%{term_lower}%"),
                        Snippet.code.ilike(f"%{term_lower}%"),
                        Snippet.description.ilike(f"%{term_lower}%"),
                    )
                )
                if language is not None:
                    query = query.where(Snippet.language == language)
                results = session.exec(query).all()
            return results

    def toggle_favorite(self, snippet_id: int) -> None:
        with Session(self._engine) as session:
            snippet = session.get(Snippet, snippet_id)
            if snippet is None:
                raise SnippetNotFoundError
            snippet.favorite = not snippet.favorite
            snippet.updated_at = datetime.now(timezone.utc)
            session.add(snippet)
            session.commit()
            session.refresh(snippet)

    def tag(self, snippet_id: int, /, *tags: Tag, remove: bool = False) -> None:
        with Session(self._engine) as session:
            snippet = session.get(Snippet, snippet_id)
            if snippet is None:
                raise SnippetNotFoundError
            self._update_tags(snippet, tags, remove)
            session.add(snippet)
            session.commit()
            session.refresh(snippet)


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

    def _serialize(self, snippet: Snippet) -> dict:
        snippet_dict = snippet.model_dump(mode="json")
        snippet_dict["tags"] = [tag.model_dump(mode="json") for tag in snippet.tags]
        return snippet_dict

    def _deserialize(self, snippet_dict: dict) -> Snippet:
        tags_dict = snippet_dict.pop("tags", [])
        snippet = Snippet.model_validate(snippet_dict)
        snippet.tags = [Tag.model_validate(tag) for tag in tags_dict]
        return snippet

    def add(self, snippet: Snippet) -> None:
        data = self._read()
        existing_ids = [int(k) for k in data.keys()]
        if snippet.id is None:
            snippet.id = max(existing_ids, default=0) + 1
        snippet_dict = self._serialize(snippet)
        data[str(snippet.id)] = snippet_dict
        self._write(data)

    def list(self) -> Sequence[Snippet]:
        data = self._read()
        return [self._deserialize(snippet_dict) for snippet_dict in data.values()]

    def get(self, snippet_id: int) -> Snippet | None:
        snippet_dict = self._read().get(str(snippet_id))
        if snippet_dict is not None:
            return self._deserialize(snippet_dict)

    def delete(self, snippet_id: int) -> None:
        data = self._read()
        if str(snippet_id) in data:
            del data[str(snippet_id)]
            self._write(data)
        else:
            raise SnippetNotFoundError

    def search(
        self, term: str, language: LangEnum | None = None, fuzzy: bool = False
    ) -> Sequence[Snippet]:
        data = self._read()
        snippets = [self._deserialize(snippet_dict) for snippet_dict in data.values()]
        term_lower = term.lower()

        if fuzzy:
            return self._fuzzy_search(snippets, term_lower, language)
        else:
            results = []
            for snippet in snippets:
                if any(
                    [
                        term_lower in snippet.title.lower(),
                        term_lower in snippet.code.lower(),
                        term_lower in snippet.description.lower(),
                    ]
                ):
                    if language is None or snippet.language == language:
                        results.append(snippet)
            return results

    def toggle_favorite(self, snippet_id: int) -> None:
        data = self._read()
        if str(snippet_id) in data:
            snippet_dict = data[str(snippet_id)]
            snippet = self._deserialize(snippet_dict)
        else:
            raise SnippetNotFoundError
        snippet.favorite = not snippet.favorite
        snippet.updated_at = datetime.now(timezone.utc)
        snippet_dict = self._serialize(snippet)
        data[str(snippet.id)] = snippet_dict
        self._write(data)

    def tag(self, snippet_id: int, /, *tags: Tag, remove: bool = False) -> None:
        data = self._read()
        if str(snippet_id) in data:
            snippet_dict = data[str(snippet_id)]
            snippet = self._deserialize(snippet_dict)
        else:
            raise SnippetNotFoundError
        self._update_tags(snippet, tags, remove)
        snippet_dict = self._serialize(snippet)
        data[str(snippet.id)] = snippet_dict
        self._write(data)
