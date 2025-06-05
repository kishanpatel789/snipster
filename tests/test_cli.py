import pytest
import typer
from typer.testing import CliRunner, Result

from src.snipster.cli import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def test_app(create_db_repo):
    """Overwrite app context with in-memory database."""

    @app.callback()
    def override_init(ctx: typer.Context):
        ctx.obj = create_db_repo


# @pytest.fixture(autouse=True)
# def db_setup(tmp_path, monkeypatch):
#     db_path = tmp_path / "test.db"
#     monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")


@pytest.fixture()
def add_snippet() -> Result:
    result = runner.invoke(
        app,
        [
            "add",
            "First snip",
            "print('hello world')",
            "py",
            "--description",
            "Good day, Snipster!",
        ],
    )
    return result


@pytest.fixture()
def add_another_snippet() -> Result:
    result = runner.invoke(
        app,
        [
            "add",
            "Get it all",
            "SELECT * FROM MY_TABLE;",
            "sql",
            "--description",
            "Get all records from MY_TABLE",
        ],
    )
    return result


def test_add_snippet(add_snippet):
    assert add_snippet.exit_code == 0
    assert "Snippet 'First snip' added" in add_snippet.output
    assert "(py)" in add_snippet.output
    assert "print('hello world')" in add_snippet.output
    assert "Good day, Snipster!" in add_snippet.output


# TODO: test to add snippet with failing conditions


def test_list_snippets(add_snippet, add_another_snippet):
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "First snip (py)" in result.output
    assert "Get it all (sql)" in result.output
    assert "print('hello world')" in result.output
    assert "SELECT * FROM MY_TABLE;" in result.output


def test_list_no_snippets():
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "No snippets found." in result.output


def test_get_snippet(add_snippet):
    result = runner.invoke(app, ["get", "1"])
    assert result.exit_code == 0
    assert "First snip (py)" in result.output
    assert "print('hello world')" in result.output
    assert "Good day, Snipster!" in result.output


def test_get_snippet_not_found(add_snippet):
    result = runner.invoke(app, ["get", "99"])
    assert result.exit_code == 1
    assert "No snippet found with ID 99." in result.output


def test_delete_snippet(add_snippet):
    result = runner.invoke(app, ["delete", "1"])
    assert result.exit_code == 0
    assert "Snippet 1 is deleted." in result.output


def test_delete_snippet_not_found(add_snippet, add_another_snippet):
    result = runner.invoke(app, ["delete", "99"])
    assert result.exit_code == 1
    assert "Snippet 99 not found." in result.output
