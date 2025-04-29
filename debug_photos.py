from sqlmodel import Session, select
from app.models import Photo, Event
from app.database import engine

with Session(engine) as session:
    event_id = 1  # Replace with the event_id you are testing
    event = session.exec(select(Event).where(Event.id == event_id)).first()
    if not event:
        print(f"No event found with ID {event_id}")
    else:
        print(f"Event: {event.name}")
        photos = session.exec(select(Photo).where(Photo.event_id == event_id)).all()
        if not photos:
            print(f"No photos found for event ID {event_id}")
        else:
            for photo in photos:
                print(f"Photo: {photo.filepath}, Caption: {photo.caption}")