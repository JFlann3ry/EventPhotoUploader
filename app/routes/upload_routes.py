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
import os
from app.config import STORAGE_ROOT

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
    guest_email: str = Form(...),
    file_upload: List[UploadFile] = File(...),
    guest_device: str = Form(None)  # Add this line with a default value
):
    from app.config import STORAGE_ROOT  # Ensure you use the correct storage root

    with Session(engine) as session:
        event = session.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        # Find or create guest
        guest = session.query(Guest).filter(Guest.guest_email == guest_email, Guest.event_id == event_id).first()
        if not guest:
            guest = Guest(guest_email=guest_email, event_id=event_id)
            session.add(guest)
            session.commit()
            session.refresh(guest)

        # Create event folder if it doesn't exist
        event_folder_path = Path(STORAGE_ROOT) / event.storage_path
        event_folder_path.mkdir(parents=True, exist_ok=True)

        # Create guest folder inside the event folder
        guest_folder = event_folder_path / str(guest.id)
        guest_folder.mkdir(parents=True, exist_ok=True)

        # Save each uploaded file
        for upload in file_upload:
            file_location = guest_folder / upload.filename
            async with aiofiles.open(file_location, "wb") as buffer:
                content = await upload.read()
                await buffer.write(content)
            print(f"Saved file to: {file_location}")

            # Get file size
            file_size = os.path.getsize(file_location)

            # Store file metadata in the database
            try:
                file_metadata = FileMetadata(
                    file_name=upload.filename,
                    file_type=upload.content_type,
                    guest_id=guest.id,
                    event_id=event.id,
                    file_size=file_size,
                    guest_device=guest_device  # Add this line
                )
                session.add(file_metadata)
                session.commit()  # Commit inside the loop
            except Exception as e:
                print(f"Error saving file metadata: {e}")
                session.rollback()  # Rollback in case of error
                raise HTTPException(status_code=500, detail="Failed to save file metadata")

    return templates.TemplateResponse(
        "upload_form.html",
        {"request": request, "event": event, "success": True}
    )