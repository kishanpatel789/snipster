import pytest
from sqlmodel import Session, SQLModel, create_engine

from src.snipster.models import LangEnum, Snippet, Tag

engine = create_engine("sqlite:///:memory:", echo=True)


@pytest.fixture(scope="function", autouse=True)
def set_up_database():
    SQLModel.metadata.create_all(engine)


def test_create_snipster_model():
    tag_beginner = Tag(name="beginner")
    tag_training = Tag(name="training")

    snippet = Snippet(
        title="First snip",
        code="print('hello world')",
        description="Say hello snipster",
        language=LangEnum.PYTHON,
        tags=[tag_beginner, tag_training],
    )

    with Session(engine) as session:
        session.add(snippet)
        session.commit()
        session.refresh(snippet)

        assert snippet.id is not None
        assert snippet.title == "First snip"
        assert snippet.code == "print('hello world')"
        assert snippet.description == "Say hello snipster"
        assert snippet.language == LangEnum.PYTHON
        assert len(snippet.tags) == 2
        assert snippet.created_at is not None
        assert snippet.updated_at is None
        assert snippet.favorite is False


def test_create_snippet_with_cls_method():
    tag_beginner = Tag(name="beginner")
    tag_training = Tag(name="training")

    data = dict(
        title="First snip",
        code="print('hello world')",
        description="Say hello snipster",
        language=LangEnum.PYTHON,
        tags=[tag_beginner, tag_training],
    )

    snippet = Snippet.create(**data)

    with Session(engine) as session:
        session.add(snippet)
        session.commit()
        session.refresh(snippet)

        assert snippet.id is not None
        assert snippet.title == "First snip"
        assert snippet.code == "print('hello world')"
        assert snippet.description == "Say hello snipster"
        assert snippet.language == LangEnum.PYTHON
        assert len(snippet.tags) == 2
        assert snippet.created_at is not None
        assert snippet.updated_at is None
        assert snippet.favorite is False
