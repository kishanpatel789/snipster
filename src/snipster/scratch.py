# %%
from sqlmodel import Field, Session, SQLModel, create_engine, select

# %%
engine = create_engine("sqlite:///db.sqlite", echo=False)


# %%
class Item(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    price: float


# %%
SQLModel.metadata.create_all(engine)

# %%
# create item
with Session(engine) as session:
    item = Item(name="thing", price=999.99)
    session.add(item)
    session.commit()
    session.refresh(item)

# %%
# get all items
with Session(engine) as session:
    items = session.execute(select(Item)).all()

# %%
# get item by id
with Session(engine) as session:
    item = session.get(Item, 1)

# %%
# filter by field
with Session(engine) as session:
    item = session.exec(select(Item).where(Item.name == "thing")).first()

# %%
# update item
with Session(engine) as session:
    item = session.get(Item, 1)
    if item is not None:
        item.price = item.price - 100
        session.add(item)
        session.commit()
    item = session.exec(select(Item).where(Item.name == "thing")).first()


# delete item
with Session(engine) as session:
    item = session.get(Item, 1)
    if item is not None:
        session.delete(item)
        session.commit()
