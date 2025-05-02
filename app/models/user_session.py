from __future__ import annotations
from typing import Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from sqlalchemy.orm import Mapped, relationship

class UserSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    event_id: int = Field(foreign_key="event.id")
    session_token: str
    created_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_date: datetime

    # relationships (no positional arg)
    user: Mapped[User] = relationship(back_populates="user_sessions")
    event: Mapped[Event] = relationship(back_populates="user_sessions")