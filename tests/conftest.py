import pytest
from sqlmodel import create_engine

from src.snipster.models import SQLModel
from src.snipster.repo import DBSnippetRepository


@pytest.fixture()
def create_db_repo() -> DBSnippetRepository:
    engine = create_engine("sqlite:///:memory:", echo=True)
    SQLModel.metadata.create_all(engine)
    return DBSnippetRepository(engine)
