from fastapi import APIRouter
from sqlmodel import Session, select
from app.models import Event  # Corrected import
from app.db.session import engine

gallery_router = APIRouter()

@gallery_router.get("/photos/{event_id}")
async def get_photos(event_id: int):
    with Session(engine) as session:
        event = session.exec(select(Event).where(Event.id == event_id)).first()
        if not event:
            return {"message": "Event not found"}
    return {"message": f"Photos for event {event_id}"}