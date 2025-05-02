from __future__ import annotations
from typing import Optional, List
from sqlmodel import SQLModel, Field
from sqlalchemy.orm import Mapped, relationship

class EventType(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=50, unique=True)

    # relationship (no positional arg)
    events: List["Event"] = relationship(back_populates="event_type")