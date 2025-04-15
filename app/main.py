from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session
import os
from .database import create_db_and_tables, engine
from .models import Event

# Initialize FastAPI instance
app = FastAPI()

# Serve static files (like HTML form)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Route to serve the HTML upload form
@app.get("/", response_class=HTMLResponse)
async def get_upload_form():
    with open("static/upload_form.html", "r") as f:
        return HTMLResponse(content=f.read())

# Route to handle file upload
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # Define the path where files will be stored
    base_storage_path = "/media/devmon/Elements/EventPhotoUploader/photos/"

    # Ensure the directory exists
    if not os.path.exists(base_storage_path):
        os.makedirs(base_storage_path)

    # Define the full path where the file will be saved
    file_location = os.path.join(base_storage_path, file.filename)

    # Save the file
    with open(file_location, "wb") as f:
        f.write(await file.read())

    return {"filename": file.filename, "content_type": file.content_type, "location": file_location}

# Route to create an event
@app.post("/events/")
def create_event(name: str, slug: str):
    base_storage_path = "/media/devmon/Elements/EventPhotoUploader/photos/"
    event_path = os.path.join(base_storage_path, slug)

    # Ensure base storage path exists
    if not os.path.exists(base_storage_path):
        os.makedirs(base_storage_path)

    # Check if event folder already exists
    if os.path.exists(event_path):
        raise HTTPException(status_code=400, detail="Event folder already exists")

    # Create the event folder
    os.makedirs(event_path)

    # Create and add event to the database
    event = Event(name=name, slug=slug, storage_path=event_path)

    with Session(engine) as session:
        session.add(event)
        session.commit()
        session.refresh(event)

    return {"message": "Event created", "event": event}

# Run the app with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
