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


@pytest.fixture()
def add_snippet(client: TestClient):
    payload = {
        "title": "First snip",
        "code": "print('hello world')",
        "description": "Good day, Snipster!",
        "language": "py",
    }
    response = client.post("/snippets", json=payload)
    return response


@pytest.fixture()
def add_another_snippet(client: TestClient):
    payload = {
        "title": "Get it all",
        "code": "SELECT * FROM MY_TABLE;",
        "description": "Get all records from MY_TABLE",
        "language": "sql",
    }
    response = client.post("/snippets", json=payload)
    return response


def test_add_snippet(client: TestClient, add_snippet):
    response = add_snippet
    data = response.json()

    assert response.status_code == 200
    assert data["id"] == 1
    assert data["title"] == "First snip"


def test_add_snippet_422(client: TestClient):
    payload = {}
    response = client.post("/snippets", json=payload)

    assert response.status_code == 422


def test_get_snippets(client: TestClient, add_snippet, add_another_snippet):
    response = client.get("/snippets")
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 2


def test_get_snippet(client: TestClient, add_snippet):
    response = client.get("/snippets/1")
    data = response.json()

    assert response.status_code == 200
    assert data["id"] == 1
    assert data["title"] == "First snip"


def test_get_snippet_not_found(client: TestClient):
    response = client.get("/snippets/99")
    data = response.json()

    assert response.status_code == 404
    assert data["detail"] == "Snippet with ID 99 not found"


def test_delete_snippet(client: TestClient, add_snippet):
    response = client.delete("/snippets/1")
    data = response.json()

    assert response.status_code == 200
    assert data["detail"] == "Snippet with ID 1 deleted successfully"

    response = client.get("/snippets/1")

    assert response.status_code == 404


def test_delete_snippet_not_found(client: TestClient):
    response = client.delete("/snippets/99")
    data = response.json()

    assert response.status_code == 404
    assert data["detail"] == "Snippet with ID 99 not found"


def test_toggle_favorite(client: TestClient, add_snippet):
    response = add_snippet
    data = response.json()
    assert not data["favorite"]

    response = client.post("/snippets/1/favorite")
    data = response.json()
    assert data["favorite"]
    assert data["updated_at"] is not None

    response = client.post("/snippets/1/favorite")
    data = response.json()
    assert not data["favorite"]


def test_toggle_favorite_not_found(client: TestClient):
    response = client.post("/snippets/99/favorite")
    data = response.json()

    assert response.status_code == 404
    assert data["detail"] == "Snippet with ID 99 not found"


def test_add_tag(client: TestClient, add_snippet):
    payload = ["training", "beginner"]
    response = client.post("snippets/1/tags", json=payload)
    data = response.json()

    assert response.status_code == 200
    assert len(data["tags"]) == 2

    response = client.get("snippets/1")
    data = response.json()

    assert response.status_code == 200
    assert len(data["tags"]) == 2


def test_remove_tag(client: TestClient, add_snippet):
    payload = ["training", "beginner"]
    response = client.post("snippets/1/tags", json=payload)
    data = response.json()

    assert len(data["tags"]) == 2

    payload = ["training"]
    response = client.post("snippets/1/tags?remove=true", json=payload)
    data = response.json()

    assert response.status_code == 200
    assert len(data["tags"]) == 1
    assert data["tags"][0]["name"] == "beginner"


def test_no_duplicate_tag_added(client: TestClient, add_snippet):
    payload = ["training", "training"]
    response = client.post("snippets/1/tags", json=payload)
    data = response.json()

    assert len(data["tags"]) == 1

    payload = ["training"]
    response = client.post("snippets/1/tags", json=payload)
    data = response.json()

    assert response.status_code == 200
    assert len(data["tags"]) == 1
    assert data["tags"][0]["name"] == "training"


def test_tag_snippet_not_found(client: TestClient):
    payload = ["training"]
    response = client.post("/snippets/99/tags", json=payload)
    data = response.json()

    assert response.status_code == 404
    assert data["detail"] == "Snippet with ID 99 not found"


def test_tag_snippet_422(client: TestClient):
    payload = {}
    response = client.post("/snippets", json=payload)

    assert response.status_code == 422


# TODO: add tests for search endpoint
