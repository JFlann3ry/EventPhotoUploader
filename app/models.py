from sqlmodel import Field, SQLModel
from typing import Optional

class Event(SQLModel, table=True):
    # … existing columns …
    banner_url: Optional[str] = Field(default=None, description="Optional header image URL")
    theme_color: Optional[str] = Field(default="#007bff", description="Primary accent color")
    instructions: Optional[str] = Field(default=None, description="HTML/text shown above upload form")
    require_guest_name: bool = Field(default=False, description="Collect guest names?")
    watermark_text: Optional[str] = Field(default=None, description="Text to overlay on previews")