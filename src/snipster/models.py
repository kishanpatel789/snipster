import re
from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy import Column
from sqlalchemy import Enum as SaEnum
from sqlmodel import Field, Relationship, Session, SQLModel, create_engine


def enum_column(enum_cls):
    return Column(SaEnum(enum_cls, values_callable=lambda x: [e.value for e in x]))


class LangEnum(StrEnum):
    PYTHON = "py"
    SQL = "sql"
    RUST = "rs"


class SnippetTagLink(SQLModel, table=True):
    snippet_id: int | None = Field(
        default=None, foreign_key="snippet.id", primary_key=True
    )
    tag_id: int | None = Field(default=None, foreign_key="tag.id", primary_key=True)


class SnippetBase(SQLModel):
    title: str
    code: str
    description: str | None = None
    language: LangEnum = Field(sa_column=enum_column(LangEnum))
    favorite: bool = False


class Snippet(SnippetBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime | None = None

    tags: list["Tag"] = Relationship(
        back_populates="snippets",
        link_model=SnippetTagLink,
        sa_relationship_kwargs={
            "lazy": "selectin",
        },
    )

    def __init__(self, **data):
        super().__init__(**data)
        if not hasattr(self, "tags") or self.tags is None:
            self.tags = []

    @classmethod
    def create(cls, **kwargs):
        snippet = cls(**kwargs)
        return snippet


class SnippetCreate(SnippetBase):
    pass


class SnippetRead(SnippetBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None
    tags: list["TagRead"]


class TagBase(SQLModel):
    name: str = Field(min_length=1, max_length=20)

    @field_validator("name", mode="before")
    @classmethod
    def clean_tag_name(cls, value: str) -> str:
        value = value.strip().lower()
        value = re.sub(r"\s+", "-", value)
        return value

    model_config = ConfigDict(validate_assignment=True)


class Tag(TagBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    snippets: list["Snippet"] = Relationship(
        back_populates="tags", link_model=SnippetTagLink
    )


class TagRead(TagBase):
    id: int


class DeleteResponse(BaseModel):
    detail: str


def main():  # pragma: no cover
    from decouple import config

    def get_engine():
        engine = create_engine(config["DATABASE_URL"], echo=True)
        return engine

    def create_db_and_tables(engine):
        SQLModel.metadata.create_all(engine)

    def create_snippets(engine):
        with Session(engine) as session:
            tag_beginner = Tag(name="beginner")
            tag_training = Tag(name="training")

            snippet = Snippet(
                title="First snip",
                code="print('hello world')",
                description="Say hello snipster",
                language=LangEnum.PYTHON,
                tags=[tag_beginner, tag_training],
            )
            session.add(snippet)
            session.commit()

    engine = get_engine()
    create_db_and_tables(engine)
    create_snippets(engine)


if __name__ == "__main__":
    main()
