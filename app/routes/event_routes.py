from fastapi import APIRouter, HTTPException, Form
from sqlmodel import Session
from pathlib import Path
from datetime import datetime

from ..models import Event
from ..database import engine

event_router = APIRouter()

STORAGE_ROOT = Path("/media/devmon/Elements/EventPhotoUploader/events")

@event_router.post("/")
def create_event(event: Event, password: str = Form(...)):
    """
    Create a new event and its corresponding folder.
    """
    event_path = STORAGE_ROOT / event.slug

    if event_path.exists():
        raise HTTPException(status_code=400, detail="Event folder already exists")

    event_path.mkdir(parents=True, exist_ok=True)

    event_db = Event(
        name=event.name,
        slug=event.slug,
        storage_path=str(event_path),
        password=password  # Store the password in the database
    )

    with Session(engine) as session:
        session.add(event_db)
        session.commit()
        session.refresh(event_db)

    return {"message": "Event created", "event": event_db}