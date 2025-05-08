from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime
from sqlmodel import Session, select
from app.models import Event  # Corrected import
from app.db.session import engine

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

@router.post("/events")
async def create_event(event: EventCreate):
    event_id = str(uuid4())
    events[event_id] = {
        "id": event_id,
        "name": event.name,
        "description": event.description,
        "event_code": event.event_code,
        "password": event.password,  # In production, hash this password
        "created_at": datetime.utcnow(),
        "updated_at": None,
    }
    return events[event_id]

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

event_router = APIRouter()

@event_router.get("/events")
async def get_events():
    with Session(engine) as session:
        events = session.exec(select(Event)).all()
    return {"events": events}