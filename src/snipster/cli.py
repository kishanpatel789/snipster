from typing import List

import typer
from dotenv import dotenv_values
from sqlmodel import create_engine
from typer import Typer
from typing_extensions import Annotated

from .exceptions import SnippetNotFoundError
from .models import LangEnum, Snippet, Tag
from .repo import DBSnippetRepository

config = dotenv_values()
app = Typer()


@app.callback()
def init(ctx: typer.Context):
    engine = create_engine(config["DATABASE_URL"], echo=False)
    ctx.obj = DBSnippetRepository(engine)


@app.command()
def add(
    title: Annotated[str, typer.Argument(help="Title of the code snippet")],
    code: Annotated[str, typer.Argument(help="Code written as text")],
    language: Annotated[LangEnum, typer.Argument(help="Language of the code")],
    ctx: typer.Context,
    description: Annotated[
        str | None, typer.Option(help="Brief description of what code does")
    ] = None,
):
    """Add a code snippet."""
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
    """List all code snippets."""
    repo: DBSnippetRepository = ctx.obj
    snippets = repo.list()
    if snippets:
        print(snippets)  # TODO: format output with rich panels
    else:
        print("No snippets found.")


@app.command()
def get(
    snippet_id: Annotated[int, typer.Argument(help="ID of snippet to retrieve")],
    ctx: typer.Context,
):
    """Get a code snippet by its ID."""
    repo: DBSnippetRepository = ctx.obj
    snippet = repo.get(snippet_id)
    if snippet:
        # print(f"Snippet ID: {snippet.id}, Title: {snippet.title}, Code: {snippet.code}")
        print(snippet)
    else:
        print(f"No snippet found with ID {snippet_id}.")


@app.command()
def delete(
    snippet_id: Annotated[int, typer.Argument(help="ID of snippet to delete")],
    ctx: typer.Context,
):
    """Delete a code snippet by its ID."""
    repo: DBSnippetRepository = ctx.obj
    try:
        repo.delete(snippet_id)
        print(f"Snippet {snippet_id} is deleted.")
    except SnippetNotFoundError:
        print(f"Snippet {snippet_id} not found.")
        typer.Exit(code=1)


@app.command()
def search(
    term: Annotated[
        str,
        typer.Argument(help="Text to search title, code, and description of snippets"),
    ],
    ctx: typer.Context,
    tag: Annotated[str | None, typer.Option(help="Filter results by tag name")] = None,
    language: Annotated[
        LangEnum | None, typer.Option(help="Filter results by language")
    ] = None,
    fuzzy: Annotated[
        bool, typer.Option(help="Perform fuzzy search instead of strict search")
    ] = False,
):
    """Search for code snippets by title, code, description, tag, or language."""
    repo: DBSnippetRepository = ctx.obj
    results = repo.search(term, tag_name=tag, language=language, fuzzy=fuzzy)
    if results:
        print(results)
    else:
        print("No snippets found matching the search criteria.")


@app.command()
def toggle_favorite(
    snippet_id: Annotated[int, typer.Argument(help="ID of snippet to toggle")],
    ctx: typer.Context,
):
    """Toggle favorite status of a code snippet by its ID."""
    repo: DBSnippetRepository = ctx.obj
    try:
        repo.toggle_favorite(snippet_id)
        snippet = repo.get(snippet_id)
        print(snippet)
    except SnippetNotFoundError:
        print(f"Snippet {snippet_id} not found.")
        typer.Exit(code=1)


@app.command()
def tag(
    snippet_id: Annotated[int, typer.Argument(help="ID of snippet to update")],
    tags: Annotated[List[str], typer.Argument(help="Tags to add or remove")],
    ctx: typer.Context,
    remove: Annotated[
        bool, typer.Option("--remove", help="Remove tag instead of adding")
    ] = False,
):
    """Add or remove tags from a code snippet."""
    repo: DBSnippetRepository = ctx.obj
    try:
        tag_objs = [
            Tag(name=tag) for tag in tags
        ]  # TODO: stop duplicate tag entries in db
        repo.tag(snippet_id, *tag_objs, remove=remove)
        snippet = repo.get(snippet_id)
        print(snippet)
    except SnippetNotFoundError:
        print(f"Snippet {snippet_id} not found.")
        typer.Exit(code=1)
