import pytest
import typer
from typer.testing import CliRunner

from src.snipster.cli import app

runner = CliRunner()


@pytest.fixture()
def app_with_db(create_db_repo):
    """Overwrite app context with in-memory database."""

    @app.callback()
    def override_init(ctx: typer.Context):
        ctx.obj = create_db_repo

    return app


def test_add_snippet(app_with_db):
    result = runner.invoke(
        app_with_db,
        [
            "add",
            "Test Snippet",
            "print('Hello, world!')",
            "py",
            "--description",
            "A simple Python snippet",
        ],
    )
    assert result.exit_code == 0
    assert "Snippet 'Test Snippet' added" in result.output
