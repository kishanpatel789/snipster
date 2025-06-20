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
    """An Abstract Base Class for Snippet repositories.
    Declares abstract methods that should be implemented by subclasses.
    Also contains helper methods that are common between subclasses.
    """

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
        self,
        term: str,
        tag_name: str | None = None,
        language: LangEnum | None = None,
        fuzzy: bool = False,
    ) -> Sequence[Snippet]:
        pass

    @abstractmethod
    def toggle_favorite(self, snippet_id: int) -> None:
        pass

    @abstractmethod
    def tag(self, snippet_id: int, /, *tags: Tag, remove: bool = False) -> None:
        pass

    def _simple_search(
        self,
        snippets: Sequence[Snippet],
        term: str,
        tag_name: str | None = None,
        language: LangEnum | None = None,
    ) -> Sequence[Snippet]:
        """Perform a search of snippets using a simple "is in" filter.
        Expects to receive snippets to search across and term to search by.
        Also allows filtering by tag or language.

        Args:
            snippets (Sequence[Snippet]): sequence of snippets to search
            term (str): search term
            tag_name (str | None): name of tag to filter by
            language (LangEnum | None): language to filter by

        Returns:
            Sequence[Snippet]: list of snippets matching search criteria
        """
        results = []
        term_lower = term.lower()
        for snippet in snippets:
            has_term_match = any(
                [
                    term_lower in snippet.title.lower(),
                    term_lower in snippet.code.lower(),
                    term_lower in snippet.description.lower(),
                ]
            )
            has_language_match = language is None or snippet.language == language
            has_tag_match = tag_name is None or tag_name in (
                t.name for t in snippet.tags
            )
            if all([has_term_match, has_language_match, has_tag_match]):
                results.append(snippet)
        return results

    def _fuzzy_search(
        self,
        snippets: Sequence[Snippet],
        term: str,
        tag_name: str | None = None,
        language: LangEnum | None = None,
    ) -> Sequence[Snippet]:
        """Perform a fuzzy search of snippets.
        Uses SequenceMatcher from `difflib` package to perform search
        against title, description, and code of snippets.
        Expects to receive snippets to search across and term to search by.
        Also allows filtering by tag or language.

        Args:
            snippets (Sequence[Snippet]): sequence of snippets to search
            term (str): search term
            tag_name (str | None): name of tag to filter by
            language (LangEnum | None): language to filter by

        Returns:
            Sequence[Snippet]: list of snippets matching search criteria
        """
        PASS_THRESHOLD = 0.6
        results = []
        term_lower = term.lower()
        for snippet in snippets:
            has_term_match = any(
                [
                    SequenceMatcher(a=term_lower, b=snippet.title.lower()).ratio()
                    >= PASS_THRESHOLD,
                    SequenceMatcher(a=term_lower, b=snippet.code.lower()).ratio()
                    >= PASS_THRESHOLD,
                    SequenceMatcher(a=term_lower, b=snippet.description.lower()).ratio()
                    >= PASS_THRESHOLD,
                ]
            )
            has_language_match = language is None or snippet.language == language
            has_tag_match = tag_name is None or tag_name in (
                t.name for t in snippet.tags
            )
            if all([has_term_match, has_language_match, has_tag_match]):
                results.append(snippet)
        return results

    def _update_favorite(self, snippet: Snippet) -> None:
        """Updates the snippet's favorite status and updated_at timestamp.

        Args:
            snippet (Snippet): snippet to toggle favorite status

        Returns:
            None:
        """
        snippet.favorite = not snippet.favorite
        snippet.updated_at = datetime.now(timezone.utc)

    def _update_tags(self, snippet: Snippet, tags: Sequence[Tag], remove: bool) -> None:
        """Updates the snippet's tags in-place. Modifies snippet.tags and updated_at.
        Method either adds tags provided or removes tags provided depending on `remove`.

        Args:
            snippet (Snippet): snippet on which to update tags
            tags (Sequence[Tag]): tags to either add or remove (depending on `remove`)
            remove (bool): if True, removes tags given in `tags`; else adds those tags

        Returns:
            None:
        """
        # O(m+n) instead of O(m*n)
        current_tags: dict[str, Tag] = {tag.name: tag for tag in snippet.tags}
        incoming_tags: dict[str, Tag] = {tag.name: tag for tag in tags}

        if remove:
            updated_tags = [
                tag
                for tag_name, tag in current_tags.items()
                if tag_name not in incoming_tags
            ]
        else:
            updated_tags = list(current_tags.values())
            for tag_name, tag in incoming_tags.items():
                if tag_name not in current_tags:
                    updated_tags.append(tag)

        snippet.tags = updated_tags
        snippet.updated_at = datetime.now(timezone.utc)


class InMemorySnippetRepository(SnippetRepository):
    """In-memory implementation of Snippet repository.
    Maintains storage in an internal `_snippets` dictionary.
    """

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
        self,
        term: str,
        tag_name: str | None = None,
        language: LangEnum | None = None,
        fuzzy: bool = False,
    ) -> Sequence[Snippet]:
        snippets = self._snippets.values()

        if fuzzy:
            return self._fuzzy_search(snippets, term, tag_name, language)
        else:
            return self._simple_search(snippets, term, tag_name, language)

    def toggle_favorite(self, snippet_id: int) -> None:
        snippet = self.get(snippet_id)
        if snippet is None:
            raise SnippetNotFoundError
        self._update_favorite(snippet)

    def tag(self, snippet_id: int, /, *tags: Tag, remove: bool = False) -> None:
        snippet = self.get(snippet_id)
        if snippet is None:
            raise SnippetNotFoundError
        self._update_tags(snippet, tags, remove)


class DBSnippetRepository(SnippetRepository):
    """Database implementation of Snippet repository.
    Maintains storage in an external database. An internal `_engine` attribute
    points to a SQLAlchemy engine object that communicate with the database.
    The engine must be defined before this class is instantiated.
    """

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def _store_snippet(self, snippet: Snippet) -> None:
        with Session(self._engine) as session:
            session.add(snippet)
            session.commit()
            session.refresh(snippet)

    def add(self, snippet: Snippet) -> None:
        self._store_snippet(snippet)

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
        self,
        term: str,
        tag_name: str | None = None,
        language: LangEnum | None = None,
        fuzzy: bool = False,
    ) -> Sequence[Snippet]:
        if fuzzy:
            with Session(self._engine) as session:
                all_records = session.exec(select(Snippet)).all()
                results = self._fuzzy_search(all_records, term, tag_name, language)
                return results
        else:
            results = []
            term_lower = term.lower()
            with Session(self._engine) as session:
                query = select(Snippet).where(
                    or_(
                        Snippet.title.ilike(f"%{term_lower}%"),
                        Snippet.code.ilike(f"%{term_lower}%"),
                        Snippet.description.ilike(f"%{term_lower}%"),
                    )
                )
                if tag_name is not None:
                    query = query.where(Snippet.tags.any(Tag.name == tag_name))
                if language is not None:
                    query = query.where(Snippet.language == language)
                results = session.exec(query).all()
            return results

    def toggle_favorite(self, snippet_id: int) -> None:
        snippet = self.get(snippet_id)
        if snippet is None:
            raise SnippetNotFoundError
        self._update_favorite(snippet)
        self._store_snippet(snippet)

    def tag(self, snippet_id: int, /, *tags: Tag, remove: bool = False) -> None:
        snippet = self.get(snippet_id)
        if snippet is None:
            raise SnippetNotFoundError

        # get existing tags from database, if applicable
        tag_names = {tag.name for tag in tags}
        with Session(self._engine) as session:
            existing_tags = session.exec(
                select(Tag).where(Tag.name.in_(tag_names))
            ).all()
            existing_tags_dict = {tag.name: tag for tag in existing_tags}
            tags_tracked = tuple(
                [existing_tags_dict.get(tag.name, tag) for tag in tags]
            )

        self._update_tags(snippet, tags_tracked, remove)
        self._store_snippet(snippet)


class JSONSnippetRepository(SnippetRepository):
    """File-based JSON implementation of Snippet repository.
    Maintains storage in an external local file. An internal `_file_path` attribute
    points to the file location.
    The file path must be defined before this class is instantiated.

    A series of helper methods handle the writing and reading of the file
    as well as the serialization and deserialization between Snippet objects
    and JSON-compatible python dictionaries.
    """

    def __init__(self, file_dir: Path) -> None:
        self._file_path = file_dir / "snippets.json"

        if not self._file_path.exists():
            self._file_path.write_text("{}")

    def _read(self) -> dict[str, Snippet]:
        """Read JSON file and return content as dictionary."""
        try:
            with open(self._file_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _write(self, data: dict) -> None:
        """Write dictionary of snippets to JSON file."""
        with open(self._file_path, "w") as f:
            return json.dump(data, f, indent=4)

    def _serialize(self, snippet: Snippet) -> dict:
        """Serialize a Snippet object into a JSON-compatible dictionary."""
        snippet_dict = snippet.model_dump(mode="json")
        snippet_dict["tags"] = [tag.model_dump(mode="json") for tag in snippet.tags]
        return snippet_dict

    def _deserialize(self, snippet_dict: dict) -> Snippet:
        """Deserialize a dictionary into a Snippet object."""
        tags_dict = snippet_dict.pop("tags", [])
        snippet = Snippet.model_validate(snippet_dict)
        snippet.tags = [Tag.model_validate(tag) for tag in tags_dict]
        return snippet

    def _store_snippet(self, snippet: Snippet) -> None:
        """Helper method to store an update to a single Snippet."""
        data = self._read()
        snippet_dict = self._serialize(snippet)
        data[str(snippet.id)] = snippet_dict
        self._write(data)

    def add(self, snippet: Snippet) -> None:
        data = self._read()
        existing_ids = [int(k) for k in data.keys()]
        if snippet.id is None:
            snippet.id = max(existing_ids, default=0) + 1
        self._store_snippet(snippet)

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
        self,
        term: str,
        tag_name: str | None = None,
        language: LangEnum | None = None,
        fuzzy: bool = False,
    ) -> Sequence[Snippet]:
        data = self._read()
        snippets = [self._deserialize(snippet_dict) for snippet_dict in data.values()]

        if fuzzy:
            return self._fuzzy_search(snippets, term, tag_name, language)
        else:
            return self._simple_search(snippets, term, tag_name, language)

    def toggle_favorite(self, snippet_id: int) -> None:
        snippet = self.get(snippet_id)
        if snippet is None:
            raise SnippetNotFoundError
        self._update_favorite(snippet)
        self._store_snippet(snippet)

    def tag(self, snippet_id: int, /, *tags: Tag, remove: bool = False) -> None:
        snippet = self.get(snippet_id)
        if snippet is None:
            raise SnippetNotFoundError
        self._update_tags(snippet, tags, remove)
        self._store_snippet(snippet)
