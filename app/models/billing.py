from __future__ import annotations
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy.orm import Mapped, relationship

class Billing(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    event_id: int = Field(foreign_key="event.id")
    pricing_id: int = Field(foreign_key="pricing.id")
    billing_date: datetime
    amount: float
    created_date: datetime = Field(default_factory=datetime.utcnow)

    # relationships (no positional arg)
    user: Mapped[User] = relationship(back_populates="billings")
    event: Mapped[Event] = relationship(back_populates="billings")
    pricing: Mapped[Pricing] = relationship(back_populates="billings")