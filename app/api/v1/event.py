from fastapi import APIRouter, HTTPException, Depends, Request, Form, File, UploadFile
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone, date
from sqlmodel import Session, select
import random, string
import os
from fastapi.responses import StreamingResponse
from io import BytesIO
import qrcode

from app.models import Event, User, Pricing, EventType
from app.core.config import STORAGE_ROOT
from app.db.session import engine, get_session
from app.api.v1.auth import get_logged_in_user as get_current_user

# ─── Pydantic Schemas ────────────────────────────────────────────────────────
class EventUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def generate_code(length: int = 4) -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# ─── CREATE PAGE (static) ──────────────────────────────────────────────────
@router.get("/events/create")
def create_event_page(
    request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    event_types = session.exec(select(EventType)).all()
    return templates.TemplateResponse(
        "create_event.html",
        {"request": request, "user": user, "event_types": event_types},
    )

# ─── LIST EVENTS ───────────────────────────────────────────────────────────
@router.get("/events")
def list_user_events(
    request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    events = session.exec(select(Event).where(Event.user_id == user.id)).all()
    return templates.TemplateResponse(
        "events.html", {"request": request, "events": events, "user": user}
    )

# ─── GET ONE (dynamic) ─────────────────────────────────────────────────────
@router.get("/events/{event_id}")
def get_event(
    request: Request,
    event_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    evt = session.exec(select(Event).where(Event.id == event_id)).first()
    if not evt:
        raise HTTPException(404, "Event not found")

    # you'll need event_types for the edit dropdown / display logic
    event_types = session.exec(select(EventType)).all()

    return templates.TemplateResponse(
        "event_details.html",
        {
            "request":     request,
            "event":       evt,
            "user":        user,
            "event_types": event_types,
            # avoid Jinja undefined errors
            "field_errors": {},
            "error":        None,
            "success":      None,
        },
    )

# ─── EVENT QR CODE ─────────────────────────────────────────────────────────
@router.get("/events/{event_id}/qr")
def event_qr(event_id: int, session: Session = Depends(get_session)):
    evt = session.exec(select(Event).where(Event.id == event_id)).first()
    if not evt:
        raise HTTPException(404, "Event not found")
    data = f"/upload/{evt.event_code}/{evt.event_password}"
    img = qrcode.make(data)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")


@router.put("/events/{event_id}")
def update_event(
    event_id: int,
    update: EventUpdate,
    session: Session = Depends(get_session),
):
    evt = session.exec(select(Event).where(Event.id == event_id)).first()
    if not evt:
        raise HTTPException(404, "Event not found")

    if update.name:
        evt.name = update.name
    if update.description:
        evt.description = update.description
    evt.updated_at = datetime.now(timezone.utc)

    session.add(evt)
    session.commit()
    session.refresh(evt)
    return {"message": "Event updated", "event": evt}


@router.delete("/events/{event_id}")
def delete_event(event_id: int, session: Session = Depends(get_session)):
    evt = session.exec(select(Event).where(Event.id == event_id)).first()
    if not evt:
        raise HTTPException(404, "Event not found")
    session.delete(evt)
    session.commit()
    return {"message": "Event deleted"}


@router.post("/events")
def create_event(
    request: Request,
    name: str = Form(...),
    description: str = Form(None),
    date: date = Form(...),
    event_type_id: int = Form(...),
    welcome_message: str = Form(None),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    # enforce limits …
    # check_event_limit(user, session)

    code = generate_code()
    password = generate_code(4)
    # prepare a storage directory for this event (must be non-null)
    event_storage_dir = os.path.join(STORAGE_ROOT, code)
    os.makedirs(event_storage_dir, exist_ok=True)

    new_event = Event(
        user_id=user.id,
        name=name,
        description=description,
        date=datetime.combine(date, datetime.min.time()).replace(tzinfo=timezone.utc),
        event_type_id=event_type_id,
        welcome_message=welcome_message,
        event_code=code,
        event_password=password,
        storage_path=event_storage_dir,
    )
    session.add(new_event)
    session.commit()
    session.refresh(new_event)

    return templates.TemplateResponse(
        "event_created.html",
        {
            "request": request,
            "user": user,
            "event": new_event,
            "event_code": code,
            "event_password": password,
        },
    )


@router.post("/events/{event_id}")
async def update_event_form(
    request: Request,
    event_id: int,
    name: str = Form(...),
    date: date = Form(...),
    event_type_id: int = Form(...),
    welcome_message: str = Form(None),
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    # fetch & validate…
    evt = session.exec(select(Event).where(Event.id == event_id)).first()
    if not evt:
        raise HTTPException(404, "Event not found")

    # apply the simple fields
    evt.name = name
    evt.date = datetime.combine(date, datetime.min.time()).replace(tzinfo=timezone.utc)
    evt.event_type_id = event_type_id
    evt.welcome_message = welcome_message

    # now manually pull the File
    form = await request.form()
    banner_file = form.get("banner_file")
    # only if it's really an UploadFile and has a filename
    if hasattr(banner_file, "filename") and banner_file.filename:
        from pathlib import Path
        import aiofiles

        upload_dir = Path(evt.storage_path) / "customisation"
        upload_dir.mkdir(parents=True, exist_ok=True)
        ext = Path(banner_file.filename).suffix
        banner_name = f"banner{ext}"
        dest = upload_dir / banner_name
        async with aiofiles.open(dest, "wb") as out:
            await out.write(await banner_file.read())
        evt.banner_filename = banner_name

    # commit & render…
    session.add(evt)
    session.commit()
    session.refresh(evt)

    # re-fetch types for template
    event_types = session.exec(select(EventType)).all()

    return templates.TemplateResponse(
        "event_details.html",
        {
            "request":     request,
            "event":       evt,
            "user":        user,
            "event_types": event_types,
            "field_errors": {},
            "error":        None,
            "success":      True,
        },
    )