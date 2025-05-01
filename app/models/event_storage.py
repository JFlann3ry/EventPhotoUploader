from __future__ import annotations
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class EventStorage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="event.id")
    path: str
    created_date: datetime = Field(default_factory=datetime.utcnow)

    # Relationship (no positional arg)
    event: "Event" = Relationship(back_populates="event_storage")