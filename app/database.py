from sqlmodel import SQLModel, create_engine
from sqlalchemy.orm import sessionmaker  # <-- Import sessionmaker here
from .models import Event, File

sqlite_file_name = "event_photo_uploader.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# Create engine
engine = create_engine(sqlite_url, echo=True)

# Create a session maker for interacting with the database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Function to create the database and tables
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
