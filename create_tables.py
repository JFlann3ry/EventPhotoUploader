0.3from sqlmodel import create_engine
from app.models import FileMetadata, Event

# Set up the correct database URL
DATABASE_URL = "sqlite:///./database.db"  # Ensure the path to your database is correct

# Create the engine to connect to the database
engine = create_engine(DATABASE_URL, echo=True)

# Create all tables defined in Base (this includes FileMetadata, File, and Event models)
Base.metadata.create_all(engine)

print("Tables created successfully!")
