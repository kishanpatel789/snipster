from datetime import datetime, timezone
from enum import IntEnum

from sqlmodel import Field, Relationship, Session, SQLModel, create_engine


class LangEnum(IntEnum):
    PY = 1
    SQL = 2


class SnippetTagLink(SQLModel, table=True):
    snippet_id: int | None = Field(
        default=None, foreign_key="snippet.id", primary_key=True
    )
    tag_id: int | None = Field(default=None, foreign_key="tag.id", primary_key=True)


class Snippet(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    code: str
    description: str | None = None
    language: LangEnum
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime | None = None
    favorite: bool = False

    tags: list["Tag"] = Relationship(
        back_populates="snippets", link_model=SnippetTagLink
    )

    @classmethod
    def create(cls, **kwargs):
        snippet = cls(**kwargs)
        return snippet


class Tag(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    active: bool = True

    snippets: list["Snippet"] = Relationship(
        back_populates="tags", link_model=SnippetTagLink
    )


def get_engine():
    engine = create_engine("sqlite:///snipster.sqlite", echo=True)
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
            language=LangEnum.PY,
            tags=[tag_beginner, tag_training],
        )

        session.add(snippet)
        session.commit()


def main():
    engine = get_engine()
    create_db_and_tables(engine)
    create_snippets(engine)


if __name__ == "__main__":
    main()
