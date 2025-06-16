from sqlmodel import Session, select
from app.models import Event, FileMetadata
from app.db.session import engine

with Session(engine) as session:
    event_id = 1  # Replace with the event_id you are testing
    event = session.exec(select(Event).where(Event.id == event_id)).first()
    if not event:
        print(f"No event found with ID {event_id}")
    else:
        print(f"Event: {event.name}")
        files = session.exec(
            select(FileMetadata).where(FileMetadata.event_id == event_id)
        ).all()
        if not files:
            print(f"No files found for event ID {event_id}")
        else:
            for f in files:
                print(f"File: {f.file_name}, Uploaded: {f.created_date}")