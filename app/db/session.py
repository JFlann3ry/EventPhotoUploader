from sqlmodel import create_engine, Session
from app.models import Event, FileMetadata

DATABASE_URL = "sqlite:///./database.db"
engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    from app.models import User  # Ensure models are imported
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(engine)

def SessionLocal():
    return Session(engine)
