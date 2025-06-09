from typing import Annotated

from decouple import config
from fastapi import Depends, FastAPI, HTTPException
from sqlmodel import create_engine

from .models import Snippet
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


@app.get("/snippets")
def get_snippets(repo: RepoDep) -> list[Snippet]:
    return repo.list()


@app.get("/snippets/{snippet_id}")
def get_snippet(snippet_id: int, repo: RepoDep) -> Snippet:
    snippet = repo.get(snippet_id)
    if snippet is None:
        raise HTTPException(
            status_code=404, detail=f"Snippet with ID {snippet_id} not found"
        )
    return snippet
