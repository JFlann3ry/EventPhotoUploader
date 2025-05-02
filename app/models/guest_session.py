from __future__ import annotations
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy.orm import Mapped, relationship

class GuestSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    guest_id: int = Field(foreign_key="guest.id")
    event_id: int = Field(foreign_key="event.id")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None

    # relationships (no positional arg)
    guest: Mapped[Guest] = relationship(back_populates="guest_sessions")
    event: Mapped[Event] = relationship(back_populates="guest_sessions")