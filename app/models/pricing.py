from __future__ import annotations
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class Pricing(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tier: str = Field(max_length=50)
    price: float

    # Relationships (no positional arg)
    events: List["Event"] = Relationship(back_populates="pricing")
    billings: List["Billing"] = Relationship(back_populates="pricing")