from sqlalchemy.ext.declarative import declarative_base
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, List

# Base should be defined here for SQLAlchemy
Base = declarative_base()

# Define the File model
class File(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="event.id")
    filename: str
    file_type: str  # 'photo' or 'video'
    uploaded_by: Optional[str] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

    # Define the relationship here without the need to manually set it later
    event: "Event" = Relationship(back_populates="files")


# Define the Event model
class Event(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    slug: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    storage_path: str

    # Define the relationship here
    files: List[File] = Relationship(back_populates="event")
