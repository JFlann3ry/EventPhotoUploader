from __future__ import annotations
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class Guest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="event.id")
    guest_email: str

    # Relationships (no positional arg)
    event: "Event" = Relationship(back_populates="guests")
    files_metadata: List["FileMetadata"] = Relationship(back_populates="guest")
    guest_sessions: List["GuestSession"] = Relationship(back_populates="guest")