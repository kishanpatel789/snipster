from sqlmodel import Field, SQLModel, create_engine

engine = create_engine("sqlite:///db.sqlite", echo=False)


class Item(SQLModel, table=True):
    id: int | None = Field(default=None, echo=False)
    name: str
    price: float
