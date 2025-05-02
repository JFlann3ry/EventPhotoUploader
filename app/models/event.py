from __future__ import annotations
from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy.orm import Mapped, relationship

class Event(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_type_id: Optional[int] = Field(default=None, foreign_key="eventtype.id")
    user_id: int = Field(foreign_key="user.id")
    name: Optional[str] = Field(default=None, max_length=100)
    date: datetime
    welcome_message: Optional[str] = Field(default=None, max_length=250)
    storage_path: str
    event_code: str = Field(max_length=4)
    event_password: str = Field(max_length=4)
    pricing_id: int = Field(foreign_key="pricing.id")

    # relationships (no positional arg)
    user: Mapped[User] = relationship(back_populates="events")
    guests: List["Guest"] = relationship(back_populates="event")
    billings: List["Billing"] = relationship(back_populates="event")
    event_storage: Optional["EventStorage"] = relationship(back_populates="event")
    file_metadata: List["FileMetadata"] = relationship(back_populates="event")
    guest_sessions: List["GuestSession"] = relationship(back_populates="event")
    qrcode: Optional[QRCode] = relationship(back_populates="event")
    event_type: Optional["EventType"] = relationship(back_populates="events")
    pricing: Mapped[Pricing] = relationship(back_populates="events")