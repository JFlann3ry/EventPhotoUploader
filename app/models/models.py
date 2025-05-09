from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    first_name: str
    last_name: str
    email: str
    hashed_password: str
    verified: bool = False
    marked_for_deletion: bool = False
    pricing_id: Optional[int] = Field(default=1, foreign_key="pricing.id")  # Default to Free Plan

    pricing: Optional["Pricing"] = Relationship(back_populates="users")
    events: List["Event"] = Relationship(back_populates="user")
    billings: List["Billing"] = Relationship(back_populates="user")
    sessions: List["UserSession"] = Relationship(back_populates="user")


class Pricing(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tier: str  # e.g., "Free", "Basic", "Ultimate", "Everything"
    price: float  # e.g., 0.0, 30.0, 60.0, 99.0
    features: str  # JSON or comma-separated list of features

    events: List["Event"] = Relationship(back_populates="pricing")
    billings: List["Billing"] = Relationship(back_populates="pricing")
    users: List["User"] = Relationship(back_populates="pricing")


class EventType(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str 

    events: List["Event"] = Relationship(back_populates="event_type")


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
    pricing_id: Optional[int] = Field(default=None, foreign_key="pricing.id")

    user: "User" = Relationship(back_populates="events")
    event_type: Optional["EventType"] = Relationship(back_populates="events")
    pricing: Optional["Pricing"] = Relationship(back_populates="events")
    files: List["FileMetadata"] = Relationship(back_populates="event")
    guests: List["Guest"] = Relationship(back_populates="event")
    billings: List["Billing"] = Relationship(back_populates="event")
    storages: List["EventStorage"] = Relationship(back_populates="event")
    qrcode: Optional["QRCode"] = Relationship(back_populates="event")
    guest_sessions: List["GuestSession"] = Relationship(back_populates="event")


class Guest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="event.id")
    guest_email: str

    event: "Event" = Relationship(back_populates="guests")
    files: List["FileMetadata"] = Relationship(back_populates="guest")
    sessions: List["GuestSession"] = Relationship(back_populates="guest")


class Billing(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    event_id: int = Field(foreign_key="event.id")
    pricing_id: int = Field(foreign_key="pricing.id")
    billing_date: datetime
    amount: float
    created_date: datetime = Field(default_factory=datetime.utcnow)

    user: "User" = Relationship(back_populates="billings")
    event: "Event" = Relationship(back_populates="billings")
    pricing: "Pricing" = Relationship(back_populates="billings")


class EventStorage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="event.id")
    path: str
    created_date: datetime = Field(default_factory=datetime.utcnow)

    event: "Event" = Relationship(back_populates="storages")


class QRCode(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="event.id", unique=True)
    qr_code_path: str
    created_date: datetime = Field(default_factory=datetime.utcnow)

    event: "Event" = Relationship(back_populates="qrcode")


class UserSession(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    session_token: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    user_agent: str = ""
    ip_address: str = ""
    
    user: "User" = Relationship(back_populates="sessions")


class FileMetadata(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="event.id")
    guest_id: Optional[int] = Field(default=None, foreign_key="guest.id")
    file_name: str
    file_size: int
    created_date: datetime = Field(default_factory=datetime.utcnow)

    event: "Event" = Relationship(back_populates="files")
    guest: Optional["Guest"] = Relationship(back_populates="files")


class GuestSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    guest_id: int = Field(foreign_key="guest.id")
    event_id: int = Field(foreign_key="event.id")
    started_at: datetime
    ended_at: Optional[datetime] = None

    guest: "Guest" = Relationship(back_populates="sessions")
    event: "Event" = Relationship(back_populates="guest_sessions")