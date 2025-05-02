from __future__ import annotations
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy.orm import Mapped, relationship

class FileMetadata(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="event.id")
    guest_id: Optional[int] = Field(default=None, foreign_key="guest.id")
    file_name: str
    file_size: int
    created_date: datetime = Field(default_factory=datetime.utcnow)

    # relationships (no positional arg)
    event: Mapped[Event] = relationship(back_populates="file_metadata")
    guest: Optional["Guest"] = relationship(back_populates="files_metadata")