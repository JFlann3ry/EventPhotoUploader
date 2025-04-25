from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime, date
from fastapi import FastAPI, Form, UploadFile, HTTPException
from sqlmodel import Session
import uuid
import aiofiles
from pathlib import Path
from app.config import STORAGE_ROOT

engine = None  # Replace with your actual SQLModel engine instance

app = FastAPI()

class Event(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    event_type_id: int = Field(default=None, foreign_key="eventtype.id")
    name: str = Field(default="")  # <-- Add this line
    event_date: Optional[date] = None  # <-- Add this line
    welcome_message: str = Field(default="")
    storage_path: str
    password: Optional[str] = None
    deleted_at: Optional[datetime] = None

    files_metadata: List["FileMetadata"] = Relationship(back_populates="event")
    files: List["File"] = Relationship(back_populates="event")

class FileMetadata(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    file_name: str
    file_type: str
    guest_id: Optional[int] = Field(default=None, foreign_key="guest.id")
    event_id: int = Field(foreign_key="event.id")
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow)
    file_size: int
    deleted_at: Optional[datetime] = None

    event: "Event" = Relationship(back_populates="files_metadata")

class File(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="event.id")
    filename: str
    file_type: str
    uploaded_by: Optional[str] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None

    event: "Event" = Relationship(back_populates="files")

class Guest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: Optional[str] = None
    event_id: int = Field(foreign_key="event.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    first_name: str
    event_date: date
    email: str = Field(index=True, unique=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    

class EventType(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    event_type: str
