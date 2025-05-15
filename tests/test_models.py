import pytest
from sqlmodel import Session, SQLModel, create_engine

from src.snipster.models import LangEnum, Snippet

engine = create_engine("sqlite:///:memory:", echo=True)


@pytest.fixture(scope="module", autouse=True)
def set_up_database():
    SQLModel.metadata.create_all(engine)


def test_create_snipster_model():
    snippet = Snippet(
        title="First snip",
        code="print('hello world')",
        description="Say hello snipster",
        language=LangEnum.PY,
        tags="beginner,training",
    )

    with Session(engine) as session:
        session.add(snippet)
        session.commit()
        session.refresh(snippet)

    assert snippet.id is not None
    assert snippet.title == "First snip"
    assert snippet.code == "print('hello world')"
    assert snippet.description == "Say hello snipster"
    assert snippet.language == LangEnum.PY
    assert snippet.tags == "beginner,training"
    assert snippet.created_at is not None
    assert snippet.updated_at is None
    assert snippet.favorite is False
