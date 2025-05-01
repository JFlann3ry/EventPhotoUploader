from __future__ import annotations
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class Billing(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    event_id: int = Field(foreign_key="event.id")
    pricing_id: int = Field(foreign_key="pricing.id")
    billing_date: datetime
    amount: float
    created_date: datetime = Field(default_factory=datetime.utcnow)

    # Relationships (no positional arg)
    user: "User" = Relationship(back_populates="billings")
    event: "Event" = Relationship(back_populates="billings")
    pricing: "Pricing" = Relationship(back_populates="billings")