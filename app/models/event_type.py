from __future__ import annotations
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class EventType(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=50, unique=True)

    # Relationship (no positional arg)
    events: List["Event"] = Relationship(back_populates="event_type")