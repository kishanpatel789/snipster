from decouple import config
from sqlmodel import Session, create_engine

from src.snipster.models import LangEnum, Snippet, SQLModel, Tag


def main() -> None:
    def get_engine():
        database_url = config("DATABASE_URL", default="sqlite:///snipster.sqlite")
        engine = create_engine(database_url, echo=True)
        return engine

    def create_db_and_tables(engine):
        SQLModel.metadata.drop_all(engine)
        SQLModel.metadata.create_all(engine)

    def create_snippets(engine):
        with Session(engine) as session:
            tag_beginner = Tag(name="beginner")
            tag_training = Tag(name="training")
            tag_query = Tag(name="query")

            s1 = Snippet(
                title="List comprehension",
                code="[x*x for x in range(10)]",
                description="Python's one-liner for generating lists",
                language=LangEnum.PYTHON,
                tags=[tag_beginner, tag_training],
            )
            s2 = Snippet(
                title="Filter a table",
                code="SELECT * FROM users WHERE age > 30;",
                description="Basic SQL query to select users older than 30",
                language=LangEnum.SQL,
                tags=[tag_query],
                favorite=True,
            )
            s3 = Snippet(
                title="F-Strings",
                code="name = 'Harry'\nprint(f'Hello, {name}!')",
                description="Python 3.6+ supports in-line string formtting",
                language=LangEnum.PYTHON,
                tags=[tag_training],
                favorite=True,
            )
            s4 = Snippet(
                title="Traits",
                code="trait Greet {\n    fn greet(&self);\n}",
                description="Traits define shared behavior in Rust",
                language=LangEnum.RUST,
                tags=[tag_training],
            )

            session.add_all([s1, s2, s3, s4])
            session.commit()

    engine = get_engine()
    create_db_and_tables(engine)
    create_snippets(engine)


if __name__ == "__main__":
    main()
