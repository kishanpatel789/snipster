from datetime import datetime, timezone
from enum import Enum

from sqlmodel import Field, SQLModel

# engine = create_engine("sqlite:///snipster.sqlite", echo=False)


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
