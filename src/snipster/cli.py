import typer
from dotenv import dotenv_values
from sqlmodel import create_engine
from typer import Typer

from .exceptions import SnippetNotFoundError
from .models import LangEnum, Snippet
from .repo import DBSnippetRepository

config = dotenv_values()
app = Typer()


@app.callback()
def init(ctx: typer.Context):
    engine = create_engine(config["DATABASE_URL"], echo=False)
    ctx.obj = DBSnippetRepository(engine)


@app.command()
def add(
    title: str,
    code: str,
    language: LangEnum,
    ctx: typer.Context,
    description: str | None = None,
):
    repo: DBSnippetRepository = ctx.obj
    snippet = Snippet.create(
        title=title,
        code=code,
        description=description,
        language=language,
    )
    repo.add(snippet)


@app.command()
def list(ctx: typer.Context):
    repo: DBSnippetRepository = ctx.obj
    snippets = repo.list()
    if snippets:
        print(snippets)
    else:
        print("No snippets found.")


@app.command()
def get(snippet_id: int, ctx: typer.Context):
    repo: DBSnippetRepository = ctx.obj
    snippet = repo.get(snippet_id)
    if snippet:
        # print(f"Snippet ID: {snippet.id}, Title: {snippet.title}, Code: {snippet.code}")
        print(snippet)
    else:
        print(f"No snippet found with ID {snippet_id}")


@app.command()
def delete(snippet_id: int, ctx: typer.Context):
    repo: DBSnippetRepository = ctx.obj
    try:
        repo.delete(snippet_id)
        print(f"Snippet {snippet_id} is deleted.")
    except SnippetNotFoundError:
        print(f"Snippet {snippet_id} not found.")
        typer.Exit(code=1)


@app.command()
def search(ctx: typer.Context):
    pass


@app.command()
def toggle_favorite(ctx: typer.Context):
    pass


@app.command()
def tag(ctx: typer.Context):
    pass
