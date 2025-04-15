from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, List

# Define the Base for SQLModel
Base = SQLModel

# Define the FileMetadata model
class FileMetadata(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    file_name: str
    file_type: str
    guest_id: int  # Assuming you have a Guest model or table to link here
    event_id: int = Field(foreign_key="event.id")
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow)
    file_size: int  # File size in bytes

    # Define the relationships
    event: "Event" = Relationship(back_populates="files_metadata")

# Define the File model (your original model)
class File(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="event.id")
    filename: str
    file_type: str  # 'photo' or 'video'
    uploaded_by: Optional[str] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

    # Define the relationship here
    event: "Event" = Relationship(back_populates="files")


# Define the Event model (your original model)
class Event(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    slug: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    storage_path: str

    # Define the relationships
    files: List[File] = Relationship(back_populates="event")
    files_metadata: List[FileMetadata] = Relationship(back_populates="event")

