from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from fastapi import FastAPI, Form, UploadFile, HTTPException
from sqlmodel import Session
import uuid
import aiofiles
from pathlib import Path

STORAGE_ROOT = Path("/path/to/storage/root")
engine = None  # Replace with your actual SQLModel engine instance

app = FastAPI()

class Event(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    slug: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    storage_path: str
    password: Optional[str] = None  # Password is optional based on your schema

    # Relationships
    files_metadata: List["FileMetadata"] = Relationship(back_populates="event")
    files: List["File"] = Relationship(back_populates="event")


class FileMetadata(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    file_name: str
    file_type: str
    guest_id: int
    event_id: int = Field(foreign_key="event.id")
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow)
    file_size: int

    # Relationships
    event: Optional[Event] = Relationship(back_populates="files_metadata")


class File(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="event.id")
    filename: str
    file_type: str
    uploaded_by: Optional[str] = None  # Optional field for the uploader
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    event: Optional[Event] = Relationship(back_populates="files")


@app.post("/upload")
async def upload_file(event_code: str = Form(...), password: str = Form(...), file: UploadFile = File(...)):
    """
    Handle file uploads with event code and password authentication.
    """
    # Query the database for the event
    with Session(engine) as session:
        event = session.query(Event).filter(Event.slug == event_code).first()

        if not event or event.password != password:  # Validate password from the database
            raise HTTPException(status_code=403, detail="Invalid event code or password")

    # Proceed with file upload logic
    event_path = STORAGE_ROOT / event_code
    if not event_path.exists():
        raise HTTPException(status_code=404, detail="Event not found")

    unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_location = event_path / unique_filename

    # Save the file to disk
    async with aiofiles.open(file_location, 'wb') as f:
        content = await file.read()
        await f.write(content)

    return {"filename": unique_filename, "location": str(file_location)}

