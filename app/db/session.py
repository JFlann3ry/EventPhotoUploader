from sqlmodel import create_engine, Session
from app.models import Event, FileMetadata
from contextlib import contextmanager

DATABASE_URL = "sqlite:///./database.db"
engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    from app.models import User  # Ensure models are imported
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(engine)

def SessionLocal():
    return Session(engine)


@contextmanager
def get_session():
    with Session(engine) as session:
        yield session