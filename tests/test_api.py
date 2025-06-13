import pytest
from fastapi.testclient import TestClient

from src.snipster.api import app
from src.snipster.models import SQLModel, create_engine
from src.snipster.repo import DBSnippetRepository


@pytest.fixture()
def get_test_repo():
    engine = create_engine("sqlite:///:memory:", echo=True)
    SQLModel.metadata.create_all(engine)
    repo = DBSnippetRepository(engine)
    yield repo
    del repo


@pytest.fixture(name="client")
def test_client(get_test_repo: DBSnippetRepository):
    app.dependency_overrides["get_repo"] = get_test_repo
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_root(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Snipster API is alive!"}
