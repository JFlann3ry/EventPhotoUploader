from fastapi import APIRouter, HTTPException  # FastAPI utilities
from sqlmodel import Session, select  # ORM for database queries
from app.models import Event  # Database model for events
from app.db.session import engine  # Database engine for creating sessions

# Initialize the router for gallery-related endpoints
gallery_router = APIRouter()

@gallery_router.get("/photos/{event_id}")
async def get_photos(event_id: int):
    """
    Retrieve photos for a specific event by its ID.
    - Checks if the event exists in the database.
    - Returns a placeholder message for now (actual photo retrieval logic can be added later).
    """
    # Open a database session
    with Session(engine) as session:
        # Query the database for the event with the given ID
        event = session.exec(select(Event).where(Event.id == event_id)).first()
        if not event:
            # Raise an HTTP exception if the event is not found
            raise HTTPException(status_code=404, detail="Event not found")
    
    # Return a placeholder message (replace with actual photo retrieval logic)
    return {"message": f"Photos for event {event_id}"}