from __future__ import annotations
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class FileMetadata(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="event.id")
    guest_id: Optional[int] = Field(default=None, foreign_key="guest.id")
    file_name: str
    file_size: int
    created_date: datetime = Field(default_factory=datetime.utcnow)

    # Relationships (no positional arg)
    event: "Event" = Relationship(back_populates="file_metadata")
    guest: Optional["Guest"] = Relationship(back_populates="files_metadata")