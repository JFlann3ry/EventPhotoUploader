from fastapi import APIRouter, HTTPException, UploadFile, File, Request, Form
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from app.models import Event, FileMetadata, Guest  # Corrected import
from app.db.session import engine
from app.utils.token import validate_token
from pathlib import Path
import aiofiles, os, subprocess, shutil, json
from datetime import datetime
from PIL import Image, ExifTags
from app.template_env import templates

upload_router = APIRouter()

# ─── Helpers ─────────────────────────────────────────────────────────────
def extract_photo_time(path: str) -> datetime | None:
    try:
        img = Image.open(path)
        exif = img._getexif() or {}
        tag_map = {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}
        dt = tag_map.get("DateTimeOriginal") or tag_map.get("DateTime")
        return datetime.strptime(dt, "%Y:%m:%d %H:%M:%S") if dt else None
    except:
        return None

def extract_video_time(path: str) -> datetime | None:
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
    cmd = [
        "ffmpeg", "-i", input_path,
        "-c:v", "libx264", "-c:a", "aac", "-strict", "experimental",
        "-movflags", "+faststart",
        "-y",  # Overwrite output
        output_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.returncode == 0
# ────────────────────────────────────────────────────────────────────────

@upload_router.get("/{event_code}/{event_password}")
async def guest_upload_form(request: Request, event_code: str, event_password: str):
    with Session(engine) as session:
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
        {"request": request, "event": event}
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
    from app.core.config import STORAGE_ROOT

    with Session(engine) as session:
        # validate event
        event = session.exec(
            select(Event).where(
                Event.event_code == event_code,
                Event.event_password == event_password
            )
        ).first()
        if not event:
            raise HTTPException(status_code=404, detail="Invalid event code or password")

        # find or create guest
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

        # ensure storage directories exist
        event_folder = Path(STORAGE_ROOT) / event.storage_path
        event_folder.mkdir(parents=True, exist_ok=True)
        guest_folder = event_folder / str(guest.id)
        guest_folder.mkdir(parents=True, exist_ok=True)

        # process uploads
        for upload in file_upload:
            dest = guest_folder / upload.filename
            async with aiofiles.open(dest, "wb") as buf:
                await buf.write(await upload.read())

            full_path = str(dest)
            ct = None
            file_name_to_store = upload.filename
            file_type_to_store = upload.content_type

            if upload.content_type.startswith("image/"):
                ct = extract_photo_time(full_path)
            elif upload.content_type.startswith("video/"):
                ct = extract_video_time(full_path)
                # No transcoding, just store as-is

            size = os.path.getsize(full_path)
            meta = FileMetadata(
                file_name=file_name_to_store,
                file_type=file_type_to_store,
                guest_id=guest.id,
                event_id=event.id,
                file_size=size,
                guest_device=guest_device,
                capture_time=ct
            )
            session.add(meta)
            session.commit()

    return templates.TemplateResponse(
        "upload_form.html",
        {"request": request, "event": event, "success": True}
    )