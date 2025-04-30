from fastapi import APIRouter, Query, HTTPException
from sqlmodel import Session, select
from app.models import FileMetadata, Event
from app.database import engine
from sqlalchemy import nulls_last

gallery_router = APIRouter()

@gallery_router.get("/photos/{event_id}")
def get_photos(event_id: int, batch: int = Query(0), size: int = Query(20)):
    with Session(engine) as session:
        event = session.exec(select(Event).where(Event.id == event_id)).first()
        if not event:
            raise HTTPException(404, "Event not found.")

        stmt = (
          select(FileMetadata)
          .where(FileMetadata.event_id == event_id)
          .order_by(nulls_last(FileMetadata.capture_time))  # real-time first
          .order_by(FileMetadata.upload_datetime)           # then upload order
          .offset(batch*size)
          .limit(size)
        )
        files = session.exec(stmt).all()

        if not files:
            return []

        results = []
        for f in files:
            url = f"/media/{event.storage_path}/{f.guest_id}/{f.file_name}"
            is_video = f.file_name.lower().endswith((".mp4", ".mov", ".avi", ".webm", ".mkv"))
            results.append({
                "url": url,
                "caption": f.file_name,
                "type": "video" if is_video else "image"
            })

        return results