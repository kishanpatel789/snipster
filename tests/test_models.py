import pytest
from sqlmodel import SQLModel, create_engine

engine = create_engine("sqlite:///:memory:", echo=True)


@pytest.fixture(scope="module", autouse=True)
def set_up_database():
    SQLModel.metadata.create_all(engine)
