# Import necessary modules and libraries
from fastapi import APIRouter, HTTPException, UploadFile, File, Request, Form, Depends  # FastAPI utilities
from fastapi.templating import Jinja2Templates  # For rendering templates
from sqlmodel import Session, select  # ORM for database queries
from app.models import Event, FileMetadata, Guest  # Database models
from app.db.session import engine, get_session  # Database engine for creating sessions
from app.utils.token import validate_token  # Token validation utility
from pathlib import Path  # File path handling
import aiofiles, os, subprocess, shutil, json  # File and subprocess utilities
from datetime import datetime  # Date and time handling
from PIL import Image, ExifTags  # For extracting image metadata
from app.template_env import templates  # Jinja2 template environment

# Initialize the router for upload-related endpoints
upload_router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# ─── Helper Functions ───────────────────────────────────────────────────────

def extract_photo_time(path: str) -> datetime | None:
    """
    Extract the capture time from an image's EXIF metadata.
    """
    try:
        img = Image.open(path)
        exif = img._getexif() or {}
        tag_map = {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}
        dt = tag_map.get("DateTimeOriginal") or tag_map.get("DateTime")
        return datetime.strptime(dt, "%Y:%m:%d %H:%M:%S") if dt else None
    except:
        return None

def extract_video_time(path: str) -> datetime | None:
    """
    Extract the creation time from a video's metadata using ffprobe.
    """
    if shutil.which("ffprobe") is None:
        return None
    try:
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_entries", "format_tags=creation_time", path
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            return None
        info = json.loads(proc.stdout or "{}")
        ts = info.get("format", {}).get("tags", {}).get("creation_time")
        if not ts:
            return None
        ts = ts.rstrip("Z")
        return datetime.fromisoformat(ts)
    except Exception:
        return None

def transcode_to_mp4(input_path: str, output_path: str) -> bool:
    """
    Transcode a video file to MP4 format using ffmpeg.
    """
    cmd = [
        "ffmpeg", "-i", input_path,
        "-c:v", "libx264", "-c:a", "aac", "-strict", "experimental",
        "-movflags", "+faststart",
        "-y",  # Overwrite output
        output_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.returncode == 0

# ─── Upload Endpoints ───────────────────────────────────────────────────────

@upload_router.get("/{event_code}/{event_password}")
async def guest_upload_form(request: Request, event_code: str, event_password: str):
    """
    Render the guest upload form for a specific event.
    """
    with Session(engine) as session:
        # Validate the event code and password
        event = session.exec(
            select(Event).where(
                Event.event_code == event_code,
                Event.event_password == event_password
            )
        ).first()
        if not event:
            raise HTTPException(status_code=404, detail="Invalid event code or password")
    return templates.TemplateResponse(
        "upload_form.html",
        {
            "request": request,
            "event": event,
            "welcome_message": event.welcome_message or "",
        },
    )

@upload_router.post("/{event_code}/{event_password}")
async def guest_upload(
    request: Request,
    event_code: str,
    event_password: str,
    guest_email: str = Form(...),
    file_upload: list[UploadFile] = File(...),
    guest_device: str = Form(None)
):
    """
    Handle file uploads from guests for a specific event.
    - Validates the event and guest information.
    - Saves uploaded files and metadata to the database.
    """
    from app.core.config import STORAGE_ROOT

    with Session(engine) as session:
        # Validate the event
        event = session.exec(
            select(Event).where(
                Event.event_code == event_code,
                Event.event_password == event_password
            )
        ).first()
        if not event:
            raise HTTPException(status_code=404, detail="Invalid event code or password")

        # Find or create a guest entry
        guest = session.exec(
            select(Guest).where(
                Guest.guest_email == guest_email,
                Guest.event_id == event.id
            )
        ).first()
        if not guest:
            guest = Guest(guest_email=guest_email, event_id=event.id)
            session.add(guest)
            session.commit()
            session.refresh(guest)

        # Ensure storage directories exist
        event_folder = Path(STORAGE_ROOT) / event.storage_path
        event_folder.mkdir(parents=True, exist_ok=True)
        guest_folder = event_folder / str(guest.id)
        guest_folder.mkdir(parents=True, exist_ok=True)

        # Process uploaded files
        for upload in file_upload:
            dest = guest_folder / upload.filename
            async with aiofiles.open(dest, "wb") as buf:
                await buf.write(await upload.read())

            full_path = str(dest)
            capture_time = None
            file_name_to_store = upload.filename
            file_type_to_store = upload.content_type

            # Extract metadata based on file type
            if upload.content_type.startswith("image/"):
                capture_time = extract_photo_time(full_path)
            elif upload.content_type.startswith("video/"):
                capture_time = extract_video_time(full_path)

            # Save file metadata to the database
            size = os.path.getsize(full_path)
            meta = FileMetadata(
                file_name=file_name_to_store,
                file_type=file_type_to_store,
                guest_id=guest.id,
                event_id=event.id,
                file_size=size,
                guest_device=guest_device,
                capture_time=capture_time
            )
            session.add(meta)
            session.commit()

    return templates.TemplateResponse(
        "upload_form.html",
        {"request": request, "event": event, "success": True}
    )

@upload_router.get("/upload/{code}/{password}")
async def upload_page(
    request: Request,
    code: str,
    password: str,
    session: Session = Depends(get_session),
):
    """
    Render the upload page for an event, including a welcome message.
    """
    evt = session.exec(
        select(Event).where(
            Event.event_code == code,
            Event.event_password == password
        )
    ).first()
    if not evt:
        raise HTTPException(404, "Invalid event code or password")

    return templates.TemplateResponse(
        "upload.html",
        {
            "request": request,
            "event": evt,
            "welcome_message": evt.welcome_message or "",
        },
    )