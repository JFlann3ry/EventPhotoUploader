from __future__ import annotations
from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    first_name: str
    last_name: str
    email: str
    created_date: datetime = Field(default_factory=datetime.utcnow)
    hashed_password: str
    verified: bool = Field(default=False)
    marked_for_deletion: bool = Field(default=False)

    # Relationships (no positional arg)
    events: List["Event"] = Relationship(back_populates="user")
    billings: List["Billing"] = Relationship(back_populates="user")
    user_sessions: List["UserSession"] = Relationship(back_populates="user")