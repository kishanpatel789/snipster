import pytest

from src.snipster.exceptions import SnippetNotFoundError
from src.snipster.models import LangEnum, Snippet, Tag
from src.snipster.repo import InMemorySnippetRepository


@pytest.fixture(scope="function")
def repo() -> InMemorySnippetRepository:
    return InMemorySnippetRepository()


@pytest.fixture(scope="function")
def add_snippet(repo) -> Snippet:
    tag_beginner = Tag(name="beginner")
    tag_training = Tag(name="training")
    snippet = Snippet(
        title="First snip",
        code="print('hello world')",
        description="Say hello snipster",
        language=LangEnum.PYTHON,
        tags=[tag_beginner, tag_training],
    )
    repo.add(snippet)
    return snippet


@pytest.fixture(scope="function")
def add_another_snippet(repo) -> Snippet:
    snippet = Snippet(
        title="Get it all",
        code="SELECT * FROM MY_TABLE;",
        description="Get all records from MY_TABLE",
        language=LangEnum.SQL,
    )
    repo.add(snippet)
    return snippet


def test_add_snippet(repo, add_snippet):
    assert repo._snippets[1] == add_snippet


def test_list_snippets_one_snippet(repo, add_snippet):
    assert len(repo.list()) == 1


def test_list_two_snippets_two_snippets(repo, add_snippet, add_another_snippet):
    assert len(repo.list()) == 2


def test_get_snippet(repo, add_snippet):
    assert repo.get(1) == add_snippet


def test_get_snippet_not_found(repo, add_snippet):
    assert repo.get(99) is None


def test_delete_snippet(repo, add_snippet):
    repo.delete(1)
    assert len(repo.list()) == 0


def test_delete_snippet_not_found(repo):
    with pytest.raises(SnippetNotFoundError):
        repo.delete(99)
