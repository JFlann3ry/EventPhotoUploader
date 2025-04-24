from fastapi import APIRouter, HTTPException, UploadFile, File, Request
from sqlmodel import Session
from pathlib import Path
import uuid
import aiofiles
from datetime import datetime

from ..models import Event, FileMetadata
from ..database import engine
from ..utils import validate_token

upload_router = APIRouter()

STORAGE_ROOT = Path("/media/devmon/Elements/EventPhotoUploader/events")

@upload_router.post("/{event_slug}/{guest_id}")
async def upload_file(event_slug: str, guest_id: int, file: UploadFile = File(...), request: Request = None):
    """
    Handle file uploads for a specific event and guest.
    """
    # Validate session token
    validate_token(request, event_slug, guest_id)

    # Query the database for the event
    with Session(engine) as session:
        event = session.query(Event).filter(Event.slug == event_slug).first()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Ensure the event folder exists
    event_path = STORAGE_ROOT / event_slug
    if not event_path.exists():
        raise HTTPException(status_code=404, detail="Event not found")

    # Create a folder for the guest if it doesn't exist
    guest_folder = event_path / f"guest-{guest_id}"
    guest_folder.mkdir(parents=True, exist_ok=True)

    # Generate a unique filename and save the file
    unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_location = guest_folder / unique_filename

    async with aiofiles.open(file_location, 'wb') as f:
        content = await file.read()
        await f.write(content)

    # Insert metadata into the database
    with Session(engine) as session:
        file_metadata = FileMetadata(
            file_name=unique_filename,
            file_type=file.content_type,
            guest_id=guest_id,
            event_id=event.id,
            upload_timestamp=datetime.utcnow(),
            file_size=file_location.stat().st_size
        )
        session.add(file_metadata)
        session.commit()

    return {"filename": unique_filename, "location": str(file_location)}