import typer
from sqlmodel import create_engine
from typer import Typer

from .models import LangEnum, Snippet
from .repo import DBSnippetRepository

app = Typer()


@app.callback()
def init(ctx: typer.Context):
    engine = create_engine("sqlite:///snipster.sqlite", echo=False)
    ctx.obj = DBSnippetRepository(engine)


@app.command()
def add(title: str, code: str, ctx: typer.Context):
    repo: DBSnippetRepository = ctx.obj
    snippet = Snippet.create(
        title=title,
        code=code,
        description="A new snippet",
        language=LangEnum.PYTHON,
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
    repo.delete(snippet_id)
    print(f"Snippet {snippet_id} is deleted.")


@app.command()
def search(ctx: typer.Context):
    pass


@app.command()
def toggle_favorite(ctx: typer.Context):
    pass


@app.command()
def tag(ctx: typer.Context):
    pass
