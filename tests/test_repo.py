import pytest

from src.snipster.exceptions import SnippetNotFoundError
from src.snipster.models import LangEnum, Snippet, Tag
from src.snipster.repo import InMemorySnippetRepository


@pytest.fixture()
def example_snippet() -> Snippet:
    tag_beginner = Tag(name="beginner")
    tag_training = Tag(name="training")

    snippet = Snippet(
        title="First snip",
        code="print('hello world')",
        description="Say hello snipster",
        language=LangEnum.PYTHON,
        tags=[tag_beginner, tag_training],
    )

    return snippet


def test_full_in_mem_implementation(example_snippet):
    repo = InMemorySnippetRepository()
    repo.add(example_snippet)
    assert len(repo.list()) == 1

    retrieved = repo.get(1)
    assert retrieved.id == 1
    assert retrieved.title == "First snip"
    assert retrieved.code == "print('hello world')"
    assert retrieved.description == "Say hello snipster"
    assert retrieved.language == LangEnum.PYTHON
    assert len(retrieved.tags) == 2
    assert retrieved.created_at is not None
    assert retrieved.updated_at is None
    assert retrieved.favorite is False

    with pytest.raises(SnippetNotFoundError):
        repo.delete(2)

    repo.delete(1)
    assert len(repo.list()) == 0
    assert repo.get(1) is None
