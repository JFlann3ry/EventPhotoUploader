from fastapi import APIRouter, Query, HTTPException
from sqlmodel import Session, select
from app.models import FileMetadata, Event
from app.database import engine

gallery_router = APIRouter()

@gallery_router.get("/photos/{event_id}")  # <-- REMOVE /api prefix here
async def get_photos(event_id: int, batch: int = Query(0), size: int = Query(20)):
    print(f"Fetching photos for event_id: {event_id}, batch: {batch}, size: {size}")
    with Session(engine) as session:
        # validate event
        event = session.exec(select(Event).where(Event.id == event_id)).first()
        if not event:
            # Add a specific log message if the event itself isn't found
            print(f"Event with ID {event_id} not found in database.")
            raise HTTPException(404, "Event not found.")

        # page through FileMetadata
        files = session.exec(
            select(FileMetadata)
            .where(FileMetadata.event_id == event_id)
            .offset(batch * size)
            .limit(size)
        ).all()
        print(f"Files retrieved: {len(files)}")
        if not files:
            # Return empty list if no files found for this batch, not 404
            print(f"No files found for event {event_id} in batch {batch}.")
            return []

        results = []
        for f in files:
            # Construct the URL relative to the /media mount point
            url = f"/media/{event.storage_path}/{f.guest_id}/{f.file_name}"
            is_video = f.file_name.lower().endswith((
                ".mp4", ".mov", ".avi", ".webm", ".mkv"
            ))
            results.append({
                "url": url,
                "caption": f.file_name,
                "type": "video" if is_video else "image"
            })
        # Add a log to see what's being returned
        print(f"Returning {len(results)} items for batch {batch}.")
        return results