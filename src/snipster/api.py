from typing import Annotated

from decouple import config
from fastapi import Depends, FastAPI, HTTPException
from sqlmodel import create_engine

from .exceptions import SnippetNotFoundError
from .models import DeleteResponse, LangEnum, Snippet, SnippetCreate, SnippetRead
from .repo import DBSnippetRepository

app = FastAPI()

database_url = config("DATABASE_URL", default="sqlite:///snipster.sqlite")
engine = create_engine(database_url, echo=False)


def get_repo():
    repo = DBSnippetRepository(engine)
    yield repo
    del repo


RepoDep = Annotated[DBSnippetRepository, Depends(get_repo)]


@app.get("/")
def root():
    return {"message": "Snipster API is alive!"}


@app.get("/snippets", response_model=list[SnippetRead])
def get_snippets(repo: RepoDep):
    return repo.list()


@app.get("/snippets/{snippet_id}", response_model=SnippetRead)
def get_snippet(snippet_id: int, repo: RepoDep):
    snippet = repo.get(snippet_id)
    if snippet is None:
        raise HTTPException(
            status_code=404, detail=f"Snippet with ID {snippet_id} not found"
        )
    return snippet


@app.post("/snippets", response_model=SnippetRead)
def create_snippet(snippet: SnippetCreate, repo: RepoDep):
    new_snippet = Snippet.create(**snippet.model_dump())
    repo.add(new_snippet)
    return new_snippet


@app.delete("/snippets/{snippet_id}")
def delete_snippet(snippet_id: int, repo: RepoDep) -> DeleteResponse:
    try:
        repo.delete(snippet_id)
    except SnippetNotFoundError:
        raise HTTPException(
            status_code=404, detail=f"Snippet with ID {snippet_id} not found"
        )
    return {"detail": f"Snippet with ID {snippet_id} deleted successfully"}


@app.post("/snippets/{snippet_id}/favorite", response_model=SnippetRead)
def toggle_favorite(snippet_id: int, repo: RepoDep):
    try:
        snippet = repo.toggle_favorite(snippet_id)
    except SnippetNotFoundError:
        raise HTTPException(
            status_code=404, detail=f"Snippet with ID {snippet_id} not found"
        )
    snippet = repo.get(snippet_id)
    return snippet


@app.get("/snippets/search/", response_model=list[SnippetRead])
def search_snippets(
    term: str,
    repo: RepoDep,
    tag_name: str | None = None,
    language: LangEnum | None = None,
    fuzzy: bool = False,
):
    snippets = repo.search(term, tag_name=tag_name, language=language, fuzzy=fuzzy)
    return snippets
