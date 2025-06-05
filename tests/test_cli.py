import pytest
import typer
from typer.testing import CliRunner

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


def test_add_snippet():
    result = runner.invoke(
        app,
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
