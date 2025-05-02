from __future__ import annotations
from typing import Optional, List
from sqlmodel import SQLModel, Field
from sqlalchemy.orm import Mapped, relationship

class Pricing(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tier: str = Field(max_length=50)
    price: float

    # relationships (no positional arg)
    events: List["Event"] = relationship(back_populates="pricing")
    billings: List["Billing"] = relationship(back_populates="pricing")