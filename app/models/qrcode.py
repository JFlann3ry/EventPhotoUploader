from __future__ import annotations
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy.orm import Mapped, relationship

class QRCode(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int     = Field(foreign_key="event.id", unique=True)
    qr_code_path: str
    created_date: datetime = Field(default_factory=datetime.utcnow)

    event_id: Optional[int] = Field(default=None, foreign_key="event.id")
    event: Optional["Event"] = relationship(back_populates="qrcode")