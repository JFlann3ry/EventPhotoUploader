from __future__ import annotations
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class GuestSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    guest_id: int = Field(foreign_key="guest.id")
    event_id: int = Field(foreign_key="event.id")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None

    # Relationships (no positional arg)
    guest: "Guest" = Relationship(back_populates="guest_sessions")
    event: "Event" = Relationship(back_populates="guest_sessions")