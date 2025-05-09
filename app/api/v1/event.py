from fastapi import APIRouter, HTTPException, Depends, Request, Form
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime
from sqlmodel import Session, select
from app.models import Event, User, Pricing  # Corrected import
from app.db.session import engine, get_session
from app.api.v1.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# In-memory storage for demonstration purposes
events = {}

# Pydantic models
class EventCreate(BaseModel):
    name: str
    description: str = None
    event_code: str
    password: str

class EventUpdate(BaseModel):
    name: str = None
    description: str = None

def check_event_limit(user: User, session: Session):
    pricing = session.exec(select(Pricing).where(Pricing.id == user.pricing_id)).first()
    if not pricing:
        raise HTTPException(status_code=400, detail="Pricing tier not found")

    event_count = session.exec(select(Event).where(Event.user_id == user.id)).count()
    if event_count >= pricing.event_limit:
        raise HTTPException(status_code=403, detail="Event limit reached")

@router.post("/events")
async def create_event(
    name: str = Form(...),
    description: str = Form(None),
    event_code: str = Form(...),
    password: str = Form(...),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    check_event_limit(user, session)

    new_event = Event(
        user_id=user.id,
        name=name,
        description=description,
        date=datetime.utcnow(),
        storage_path="path/to/storage",  # Replace with actual storage logic
        event_code=event_code,
        event_password=password,
    )
    session.add(new_event)
    session.commit()
    session.refresh(new_event)
    return {"message": "Event created successfully", "event": new_event}

@router.get("/events/{event_id}")
async def get_event(event_id: str):
    if event_id not in events:
        raise HTTPException(status_code=404, detail="Event not found")
    return events[event_id]

@router.put("/events/{event_id}")
async def update_event(event_id: str, event_update: EventUpdate, request: Request):
    if event_id not in events:
        raise HTTPException(status_code=404, detail="Event not found")
    event = events[event_id]
    if event_update.name:
        event["name"] = event_update.name
    if event_update.description:
        event["description"] = event_update.description
    event["updated_at"] = datetime.utcnow()
    event_types = ["Conference", "Workshop", "Webinar"]  # Example event types
    return templates.TemplateResponse(
        "event_details.html",
        {
            "request": request,
            "event": event,
            "event_types": event_types,
            "success": "Event details updated successfully!",
            "field_errors": {}  # <-- This is correct
        }
    )

@router.delete("/events/{event_id}")
async def delete_event(event_id: str):
    if event_id not in events:
        raise HTTPException(status_code=404, detail="Event not found")
    del events[event_id]
    return {"message": "Event deleted successfully"}

@router.get("/events")
async def events_page(request: Request, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    # Fetch the user's events
    user_events = session.exec(select(Event).where(Event.user_id == user.id)).all()
    return templates.TemplateResponse("events.html", {"request": request, "events": user_events, "user": user})

@router.get("/events/create")
async def create_event_page(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse("create_event.html", {"request": request, "user": user})

event_router = APIRouter()

@event_router.get("/events")
async def get_events():
    with Session(engine) as session:
        events = session.exec(select(Event)).all()
    return {"events": events}