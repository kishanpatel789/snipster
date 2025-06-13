import pytest
from fastapi.testclient import TestClient

from src.snipster.api import app, create_engine, get_repo
from src.snipster.models import SQLModel
from src.snipster.repo import DBSnippetRepository


@pytest.fixture()
def test_repo(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", echo=True)

    SQLModel.metadata.create_all(engine)
    repo = DBSnippetRepository(engine)

    yield repo

    del repo


@pytest.fixture(name="client")
def test_client(test_repo: DBSnippetRepository):
    def get_test_repo():
        return test_repo

    app.dependency_overrides[get_repo] = get_test_repo
    client = TestClient(app)

    yield client

    app.dependency_overrides.clear()


def test_root(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Snipster API is alive!"}


# get snippets
# create snippet
# get snippet by id
# delete snippet
# toggle favorite
# search snippets
# tag

# errors 404 422


def test_add_snippet(client: TestClient):
    payload = {
        "title": "First snip",
        "code": "print('hello world')",
        "description": "Good day, Snipster!",
        "language": "py",
    }
    response = client.post("/snippets", json=payload)
    data = response.json()

    assert response.status_code == 200
    assert data["id"] == 1
    assert data["title"] == "First snip"


def test_get_snippet(client: TestClient):
    payload = {
        "title": "First snip",
        "code": "print('hello world')",
        "description": "Good day, Snipster!",
        "language": "py",
    }
    client.post("/snippets", json=payload)

    response = client.get("/snippets/1")
    data = response.json()

    assert response.status_code == 200
    assert data["title"] == "First snip"


def test_get_snippet_not_found(client: TestClient):
    response = client.get("/snippet/99")

    assert response.status_code == 404
