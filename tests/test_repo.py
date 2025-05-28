import pytest

from src.snipster.exceptions import SnippetNotFoundError
from src.snipster.models import LangEnum, Snippet, SQLModel, Tag, create_engine
from src.snipster.repo import (
    DBSnippetRepository,
    InMemorySnippetRepository,
    JSONSnippetRepository,
)


@pytest.fixture(scope="function", params=["memory", "db", "json"])
def repo(request, tmp_path) -> InMemorySnippetRepository:
    match request.param:
        case "memory":
            return InMemorySnippetRepository()
        case "db":
            engine = create_engine("sqlite:///:memory:")
            SQLModel.metadata.create_all(engine)
            return DBSnippetRepository(engine)
        case "json":
            return JSONSnippetRepository(tmp_path)
        case _:
            raise ValueError(f"Unknown repo: {request.param}")


@pytest.fixture()
def example_snippet_1() -> Snippet:
    tag_beginner = Tag(name="beginner")
    tag_training = Tag(name="training")
    snippet = Snippet(
        title="First snip",
        code="print('hello world')",
        description="Good day, Snipster!",
        language=LangEnum.PYTHON,
        tags=[tag_beginner, tag_training],
    )
    return snippet


@pytest.fixture()
def example_snippet_2() -> Snippet:
    snippet = Snippet(
        title="Get it all",
        code="SELECT * FROM MY_TABLE;",
        description="Get all records from MY_TABLE",
        language=LangEnum.SQL,
    )
    return snippet


@pytest.fixture()
def example_snippet_3() -> Snippet:
    snippet = Snippet(
        title="Get some of it",
        code="SELECT * FROM MY_TABLE LIMIT 10;",
        description="Get some records from MY_TABLE",
        language=LangEnum.SQL,
    )
    return snippet


@pytest.fixture(scope="function")
def add_snippet(repo, example_snippet_1) -> Snippet:
    repo.add(example_snippet_1)
    return example_snippet_1


@pytest.fixture(scope="function")
def add_another_snippet(repo, example_snippet_2) -> Snippet:
    repo.add(example_snippet_2)
    return example_snippet_2


@pytest.fixture(scope="function")
def add_snippets(
    repo, example_snippet_1, example_snippet_2, example_snippet_3
) -> list[Snippet]:
    repo.add(example_snippet_1)
    repo.add(example_snippet_2)
    repo.add(example_snippet_3)
    return [example_snippet_1, example_snippet_2, example_snippet_3]


def test_add_snippet(repo, add_snippet):
    assert repo.get(1) == add_snippet


def test_add_snippet_with_tags(repo, add_snippet):
    snippet = repo.get(1)
    assert snippet.tags == add_snippet.tags


def test_add_snippet_without_tags(repo, add_another_snippet):
    snippet = repo.get(1)
    assert snippet.tags == add_another_snippet.tags


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


def test_empty_dictionary_returned_new_json_repo(tmp_path):
    repo = JSONSnippetRepository(tmp_path)
    assert repo._read() == {}


def test_toggle_favorite(repo, add_snippet):
    assert add_snippet.favorite is False

    repo.toggle_favorite(add_snippet.id)
    updated_snippet = repo.get(add_snippet.id)
    assert updated_snippet.favorite is True
    assert updated_snippet.updated_at is not None

    repo.toggle_favorite(add_snippet.id)
    updated_snippet = repo.get(add_snippet.id)
    assert updated_snippet.favorite is False


def test_toggle_favorite_snippet_not_found(repo):
    with pytest.raises(SnippetNotFoundError):
        repo.toggle_favorite(99)


def test_search_snippet(repo, add_snippets):
    results = repo.search("select")
    assert len(results) == 2

    results = repo.search("hello")
    assert len(results) == 1

    results = repo.search("Non-existent snippet")
    assert len(results) == 0


def test_search_snippet_by_language(repo, add_snippets):
    results = repo.search("select", language=LangEnum.PYTHON)
    assert len(results) == 0

    results = repo.search("select", language=LangEnum.SQL)
    assert len(results) == 2

    results = repo.search("hello", language=LangEnum.PYTHON)
    assert len(results) == 1

    results = repo.search("", language=LangEnum.PYTHON)
    assert len(results) == 1

    results = repo.search("Non-existent snippet")
    assert len(results) == 0


def test_fuzzy_search_snippet(repo, add_snippets):
    results = repo.search("Get iT", fuzzy=True)
    assert len(results) == 2

    results = repo.search("ehllo world", fuzzy=True)
    assert len(results) == 1

    results = repo.search("Non-existent snippet")
    assert len(results) == 0


def test_add_tag(repo, add_another_snippet):
    tag1 = Tag(name="Test Tag")
    tag2 = Tag(name="Test Tag 2")
    repo.tag(add_another_snippet.id, tag1, tag2)
    snippet = repo.get(add_another_snippet.id)
    assert len(snippet.tags) == 2
    assert snippet.tags[0].name == "test-tag"


def test_remove_tag(repo, add_another_snippet):
    tag1 = Tag(name="Test Tag")
    tag2 = Tag(name="Test Tag 2")
    repo.tag(add_another_snippet.id, tag1, tag2)
    repo.tag(add_another_snippet.id, tag1, remove=True)
    snippet = repo.get(add_another_snippet.id)

    assert len(snippet.tags) == 1
    assert snippet.tags[0].name == "test-tag-2"


def test_tag_add_remove_snippet_not_found(repo):
    tag1 = Tag(name="Test Tag")
    with pytest.raises(SnippetNotFoundError):
        repo.tag(99, tag1)
