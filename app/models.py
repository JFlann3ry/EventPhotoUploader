from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime, date, timezone

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    first_name: str = Field(max_length=25)
    last_name: str = Field(max_length=25)
    email: str = Field(max_length=50, index=True, unique=True)
    created_date: datetime = Field(default_factory=datetime.utcnow)
    hashed_password: str
    verified: bool = Field(default=False)
    marked_for_deletion: bool = Field(default=False)  # <-- Add this line

    events: List["Event"] = Relationship(back_populates="user")
    billings: List["Billing"] = Relationship(back_populates="user")

class Event(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_type_id: Optional[int] = Field(default=None, foreign_key="eventtype.id")
    user_id: int = Field(foreign_key="user.id")
    name: Optional[str] = Field(default=None, max_length=100)
    date: datetime
    welcome_message: Optional[str] = Field(default=None, max_length=250)
    storage_path: str
    event_code: str = Field(max_length=4)  # Ensure it's a 4-character string
    event_password: str = Field(max_length=4)  # Ensure it's a 4-character string
    pricing_id: int = Field(foreign_key="pricing.id")

    user: User = Relationship(back_populates="events")
    guests: List["Guest"] = Relationship(back_populates="event")
    billings: List["Billing"] = Relationship(back_populates="event")
    event_storage: Optional["EventStorage"] = Relationship(back_populates="event")
    file_metadata: List["FileMetadata"] = Relationship(back_populates="event")
    guest_sessions: List["GuestSession"] = Relationship(back_populates="event")
    # Specify foreign_keys for clarity (optional but good practice)
    qrcode: Optional["QRCode"] = Relationship(back_populates="event", sa_relationship_kwargs={"uselist": False, "foreign_keys": "[QRCode.event_id]"})
    event_type: Optional["EventType"] = Relationship(back_populates="events")
    pricing: "Pricing" = Relationship(back_populates="events")

class Guest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="event.id")
    guest_email: str

    event: Event = Relationship(back_populates="guests")
    files_metadata: List["FileMetadata"] = Relationship(back_populates="guest")
    guest_sessions: List["GuestSession"] = Relationship(back_populates="guest")

class Pricing(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    pricing_name: int

    events: List["Event"] = Relationship(back_populates="pricing")
    billings: List["Billing"] = Relationship(back_populates="pricing")

class Billing(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    entry_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: int = Field(foreign_key="user.id")
    event_id: int = Field(foreign_key="event.id")
    pricing_id: int = Field(foreign_key="pricing.id")
    billing_total: float
    tax: int
    paid_date: Optional[datetime] = None
    currency: str = Field(default="GBP")

    user: User = Relationship(back_populates="billings")
    event: Event = Relationship(back_populates="billings")
    pricing: "Pricing" = Relationship(back_populates="billings")

class EventStorage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="event.id")
    total_used_space: int = Field(default=0)

    event: Event = Relationship(back_populates="event_storage")

class QRCode(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="event.id")
    qr_url: str
    scanned_count: int = Field(default=0)

    event: Event = Relationship(back_populates="qrcode", sa_relationship_kwargs={"foreign_keys": "[QRCode.event_id]"})

class EventType(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_type_name: str

    events: List[Event] = Relationship(back_populates="event_type")

class FileMetadata(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    file_name: str
    file_type: str
    guest_id: int = Field(foreign_key="guest.id")
    event_id: int = Field(foreign_key="event.id")
    upload_datetime: datetime = Field(default_factory=datetime.now) # Changed this line
    capture_time: datetime | None = Field(default=None, index=True)
    file_size: int
    guest_device: Optional[str] = Field(default=None)  # Add this line

    event: Event = Relationship(back_populates="file_metadata")
    guest: Optional[Guest] = Relationship(back_populates="files_metadata")

class GuestSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    guest_id: int = Field(foreign_key="guest.id")
    event_id: int = Field(foreign_key="event.id")
    session_token: str
    created_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_date: datetime

    guest: Guest = Relationship(back_populates="guest_sessions")
    event: Event = Relationship(back_populates="guest_sessions")
