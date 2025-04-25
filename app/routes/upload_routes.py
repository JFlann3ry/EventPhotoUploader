from fastapi import APIRouter, HTTPException, UploadFile, File, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlmodel import Session
from pathlib import Path
import uuid
import aiofiles
from datetime import datetime
from typing import List

from ..models import Event, FileMetadata, Guest
from ..database import engine
from ..utils import validate_token

upload_router = APIRouter()

templates = Jinja2Templates(directory="templates")

@upload_router.get("/{event_id}")
async def guest_upload_form(request: Request, event_id: int):
    with Session(engine) as session:
        event = session.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
    return templates.TemplateResponse("upload_form.html", {"request": request, "event": event})

@upload_router.post("/{event_id}")
async def guest_upload(
    request: Request,
    event_id: int,
    guest_name: str = Form(...),
    file_upload: List[UploadFile] = File(...),
):
    from app.config import STORAGE_ROOT  # Ensure you use the correct storage root

    with Session(engine) as session:
        event = session.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        # Find or create guest
        guest = session.query(Guest).filter(Guest.name == guest_name, Guest.event_id == event_id).first()
        if not guest:
            guest = Guest(name=guest_name, event_id=event_id)
            session.add(guest)
            session.commit()
            session.refresh(guest)

        # Create guest folder inside the event folder
        guest_folder = Path(event.storage_path) / str(guest.id)
        guest_folder.mkdir(parents=True, exist_ok=True)

        # Save each uploaded file
        for upload in file_upload:
            file_location = guest_folder / upload.filename
            async with aiofiles.open(file_location, "wb") as buffer:
                content = await upload.read()
                await buffer.write(content)
            print(f"Saved file to: {file_location}")

    return templates.TemplateResponse(
        "upload_form.html",
        {"request": request, "event": event, "success": True}
    )