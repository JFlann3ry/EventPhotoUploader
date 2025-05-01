from __future__ import annotations
from typing import Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship

class UserSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    event_id: int = Field(foreign_key="event.id")
    session_token: str
    created_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_date: datetime

    # Relationships (no positional arg)
    user: "User" = Relationship(back_populates="user_sessions")
    event: "Event" = Relationship(back_populates="user_sessions")