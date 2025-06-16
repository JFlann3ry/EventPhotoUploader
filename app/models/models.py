from typing import Optional, List  # For optional and list type hints
from datetime import datetime, timezone  # For date and time handling
from sqlmodel import SQLModel, Field, Relationship  # SQLModel utilities for ORM

# ─── User Model ─────────────────────────────────────────────────────────────

class User(SQLModel, table=True):
    """
    Represents a user in the system.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    first_name: str
    last_name: str
    email: str
    hashed_password: str
    verified: bool = False  # Indicates if the user's email is verified
    marked_for_deletion: bool = False  # Indicates if the user is marked for deletion
    pricing_id: Optional[int] = Field(default=1, foreign_key="pricing.id")  # Default to Free Plan

    # Relationships
    pricing: Optional["Pricing"] = Relationship(back_populates="users")
    events: List["Event"] = Relationship(back_populates="user")
    billings: List["Billing"] = Relationship(back_populates="user")
    sessions: List["UserSession"] = Relationship(back_populates="user")

# ─── Pricing Model ─────────────────────────────────────────────────────────

class Pricing(SQLModel, table=True):
    """
    Represents a pricing plan for users.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    tier: str  # Name of the pricing tier (e.g., Free, Pro, Premium)
    price: float  # Price of the plan
    event_limit: int  # Maximum number of events allowed
    storage_limit_mb: int  # Storage limit in megabytes
    can_download: bool  # Indicates if downloads are allowed
    storage_duration: int  # Storage duration in days
    allow_video: bool  # Indicates if video uploads are allowed
    features: Optional[str] = None  # Additional features as a string

    # Relationships
    events: List["Event"] = Relationship(back_populates="pricing")
    billings: List["Billing"] = Relationship(back_populates="pricing")
    users: List["User"] = Relationship(back_populates="pricing")

# ─── Event Type Model ──────────────────────────────────────────────────────

class EventType(SQLModel, table=True):
    """
    Represents a type of event (e.g., Wedding, Birthday).
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str  # Name of the event type
    banner_url: Optional[str] = Field(default=None, description="Optional header image URL")
    theme_color: Optional[str] = Field(default="#007bff", description="Primary accent color")
    instructions: Optional[str] = Field(default=None, description="HTML/text shown above upload form")
    require_guest_name: bool = Field(default=False, description="Collect guest names?")
    watermark_text: Optional[str] = Field(default=None, description="Text to overlay on previews")

    # Relationships
    events: List["Event"] = Relationship(back_populates="event_type")

# ─── Event Model ───────────────────────────────────────────────────────────

class Event(SQLModel, table=True):
    """
    Represents an event created by a user.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    event_type_id: Optional[int] = Field(default=None, foreign_key="eventtype.id")
    user_id: int = Field(foreign_key="user.id")
    name: Optional[str] = Field(default=None, max_length=100)
    date: datetime  # Date of the event
    welcome_message: Optional[str] = Field(default=None, max_length=250)
    storage_path: str  # Path to the event's storage directory
    event_code: str = Field(max_length=4)  # Unique event code
    event_password: str = Field(max_length=4)  # Password for accessing the event
    pricing_id: Optional[int] = Field(default=None, foreign_key="pricing.id")
    # store just the filename; URL will be /static/uploads/<code>/customisation/<banner_filename>
    banner_filename: Optional[str] = Field(default=None, description="Uploaded banner image filename")

    # Relationships
    user: "User" = Relationship(back_populates="events")
    event_type: Optional["EventType"] = Relationship(back_populates="events")
    pricing: Optional["Pricing"] = Relationship(back_populates="events")
    files: List["FileMetadata"] = Relationship(back_populates="event")
    guests: List["Guest"] = Relationship(back_populates="event")
    billings: List["Billing"] = Relationship(back_populates="event")
    storages: List["EventStorage"] = Relationship(back_populates="event")
    qrcode: Optional["QRCode"] = Relationship(back_populates="event")
    guest_sessions: List["GuestSession"] = Relationship(back_populates="event")

# ─── Guest Model ───────────────────────────────────────────────────────────

class Guest(SQLModel, table=True):
    """
    Represents a guest attending an event.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="event.id")
    guest_email: str  # Email address of the guest

    # Relationships
    event: "Event" = Relationship(back_populates="guests")
    files: List["FileMetadata"] = Relationship(back_populates="guest")
    sessions: List["GuestSession"] = Relationship(back_populates="guest")

# ─── Billing Model ─────────────────────────────────────────────────────────

class Billing(SQLModel, table=True):
    """
    Represents a billing record for a user or event.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    event_id: int = Field(foreign_key="event.id")
    pricing_id: int = Field(foreign_key="pricing.id")
    billing_date: datetime  # Date of the billing
    amount: float  # Amount billed
    created_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    user: "User" = Relationship(back_populates="billings")
    event: "Event" = Relationship(back_populates="billings")
    pricing: "Pricing" = Relationship(back_populates="billings")

# ─── Event Storage Model ───────────────────────────────────────────────────

class EventStorage(SQLModel, table=True):
    """
    Represents storage information for an event.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="event.id")
    path: str  # Path to the storage
    created_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    event: "Event" = Relationship(back_populates="storages")

# ─── QR Code Model ─────────────────────────────────────────────────────────

class QRCode(SQLModel, table=True):
    """
    Represents a QR code associated with an event.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="event.id", unique=True)
    qr_code_path: str  # Path to the QR code image
    created_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    event: "Event" = Relationship(back_populates="qrcode")

# ─── User Session Model ────────────────────────────────────────────────────

class UserSession(SQLModel, table=True):
    """
    Represents a session for a logged-in user.
    """
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    session_token: str  # Token for the session
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime  # Expiration time of the session
    user_agent: str = ""  # User agent of the client
    ip_address: str = ""  # IP address of the client

    # Relationships
    user: "User" = Relationship(back_populates="sessions")

# ─── File Metadata Model ───────────────────────────────────────────────────

class FileMetadata(SQLModel, table=True):
    """
    Represents metadata for a file uploaded to an event.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="event.id")
    guest_id: Optional[int] = Field(default=None, foreign_key="guest.id")
    file_name: str  # Name of the file
    file_size: int  # Size of the file in bytes
    created_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    event: "Event" = Relationship(back_populates="files")
    guest: Optional["Guest"] = Relationship(back_populates="files")

# ─── Guest Session Model ───────────────────────────────────────────────────

class GuestSession(SQLModel, table=True):
    """
    Represents a session for a guest attending an event.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    guest_id: int = Field(foreign_key="guest.id")
    event_id: int = Field(foreign_key="event.id")
    started_at: datetime  # Start time of the session
    ended_at: Optional[datetime] = None  # End time of the session (optional)

    # Relationships
    guest: "Guest" = Relationship(back_populates="sessions")
    event: "Event" = Relationship(back_populates="guest_sessions")