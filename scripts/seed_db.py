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
            tag_sql = Tag(name="sql")

            s1 = Snippet(
                title="List comprehension",
                code="[x*x for x in range(10)]",
                description="Python's one-liner for generating lists",
                language=LangEnum.PYTHON,
                tags=[tag_beginner, tag_training],
            )
            s2 = Snippet(
                title="SQL SELECT",
                code="SELECT * FROM users WHERE age > 30;",
                description="Basic SQL query to select users older than 30",
                language=LangEnum.SQL,
                tags=[tag_sql],
            )

            session.add_all([s1, s2])
            session.commit()

    engine = get_engine()
    create_db_and_tables(engine)
    create_snippets(engine)


if __name__ == "__main__":
    main()
