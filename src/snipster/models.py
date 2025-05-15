from datetime import datetime, timezone
from enum import Enum

from sqlmodel import Field, SQLModel, create_engine


def get_engine():
    engine = create_engine("sqlite:///snipster.sqlite", echo=False)
    return engine


class LangEnum(Enum):
    PY = 1
    SQL = 2


class Snippet(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    code: str
    description: str | None = None
    language: LangEnum
    tags: str  # relationship
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime | None = None
    favorite: bool = False


if __name__ == "__main__":
    engine = get_engine()
    SQLModel.metadata.create_all(engine)

    snippet = Snippet(
        title="First snip",
        code="print('hello world')",
        description="Say hello snipster",
        language=LangEnum.PY,
        tags="beginner,training",
    )

    snippet.model_dump()
