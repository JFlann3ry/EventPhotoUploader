from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session
from pydantic import BaseModel
import os
from .database import create_db_and_tables, engine
from .models import Event
import uuid

# Initialize FastAPI instance
app = FastAPI()

# Serve static files (like HTML form)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Pydantic model for event creation
class EventCreateRequest(BaseModel):
    name: str
    slug: str

# Route to serve the HTML upload form
@app.get("/", response_class=HTMLResponse)
async def get_upload_form():
    with open("static/upload_form.html", "r") as f:
        return HTMLResponse(content=f.read())

# Route to handle file upload by guest ID within an event folder
@app.post("/upload/{event_slug}/{guest_id}")
async def upload_file(event_slug: str, guest_id: int, file: UploadFile = File(...)):
    # Define base storage path for events
    base_storage_path = "/media/devmon/Elements/EventPhotoUploader/events/"

    # Create event folder path
    event_path = os.path.join(base_storage_path, event_slug)
    if not os.path.exists(event_path):
        raise HTTPException(status_code=404, detail="Event not found")

    # Create guest-specific folder inside the event folder
    guest_folder = os.path.join(event_path, f"guest-{guest_id}")
    if not os.path.exists(guest_folder):
        os.makedirs(guest_folder)

    # Generate a unique filename to avoid conflicts
    unique_filename = f"{uuid.uuid4().hex}_{file.filename}"

    # Define the file location
    file_location = os.path.join(guest_folder, unique_filename)

    # Save the uploaded file
    with open(file_location, "wb") as f:
        f.write(await file.read())

    return {"filename": unique_filename, "location": file_location}

# Route to create an event
@app.post("/events/")
def create_event(event: EventCreateRequest):
    base_storage_path = "/media/devmon/Elements/EventPhotoUploader/events/"
    event_path = os.path.join(base_storage_path, event.slug)

    # Ensure base storage path exists
    if not os.path.exists(base_storage_path):
        os.makedirs(base_storage_path)

    # Check if event folder already exists
    if os.path.exists(event_path):
        raise HTTPException(status_code=400, detail="Event folder already exists")

    # Create the event folder
    os.makedirs(event_path)

    # Create and add event to the database
    event_db = Event(name=event.name, slug=event.slug, storage_path=event_path)

    with Session(engine) as session:
        session.add(event_db)
        session.commit()
        session.refresh(event_db)

    return {"message": "Event created", "event": event_db}

# Run the app with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
