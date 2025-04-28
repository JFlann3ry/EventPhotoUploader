from sqlalchemy.orm import Session
from app.models import Event, FileMetadata
from app.database import SessionLocal, create_db_and_tables

# Create the database and tables if they don't exist
create_db_and_tables()

# Create a session
db = SessionLocal()

try:
    # Create an event
    event = Event(name="Wedding Ceremony", slug="wedding-ceremony", storage_path="/storage/photos")
    db.add(event)
    db.commit()  # Commit the transaction for event
    db.refresh(event)

    # Create some files associated with the event
    file1 = FileMetadata(filename="photo1.jpg", event_id=event.id, file_type="photo")
    file2 = FileMetadata(filename="photo2.jpg", event_id=event.id, file_type="photo")

    db.add(file1)
    db.add(file2)
    db.commit()  # Commit the transaction for files

    # Query the event and check the associated files
    queried_event = db.query(Event).filter(Event.id == event.id).first()
    print(f"Event: {queried_event.name}")
    for file in queried_event.files:
        print(f"File: {file.filename}, Type: {file.file_type}")

except Exception as e:
    print(f"An error occurred: {e}")
finally:
    # Commit the session before closing
    db.commit()  # Make sure the changes are committed before closing
    db.close()   # Close the session

