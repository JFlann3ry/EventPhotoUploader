from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, create_engine
from pydantic import BaseModel
import os
import uuid
import time
from datetime import datetime
import aiofiles  # For async file I/O

from .database import create_db_and_tables, engine
from .models import Event, FileMetadata
from .event_credentials import EVENT_CREDENTIALS

from itsdangerous import TimestampSigner, BadSignature

# Config
SECRET_KEY = "REPLACE_WITH_SOMETHING_RANDOM_AND_SECRET"
signer = TimestampSigner(SECRET_KEY)

# App init
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Models
class EventCreateRequest(BaseModel):
    name: str
    slug: str

# Routes
@app.get("/", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, event_code: str = Form(...), password: str = Form(...)):
    if event_code in EVENT_CREDENTIALS and EVENT_CREDENTIALS[event_code] == password:
        print(f"Event code '{event_code}' authenticated successfully.")  # Debugging
        token = signer.sign(event_code.encode()).decode()
        response = RedirectResponse(url=f"/upload_form/{event_code}", status_code=303)
        response.set_cookie(key="session_token", value=token, httponly=True)

        # Also set a client-side cookie to warn before expiration
        expiry_timestamp = int(time.time() + 60 * 60) * 1000  # JS uses ms
        response.set_cookie(key="session_expiry", value=str(expiry_timestamp))

        return response
    print(f"Invalid login attempt for event code: '{event_code}'")  # Debugging
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid event code or password"})

@app.get("/upload_form/{event_slug}", response_class=HTMLResponse)
async def get_upload_form(request: Request, event_slug: str):
    token = request.cookies.get("session_token")
    if not token:
        return RedirectResponse(url="/")

    try:
        event_code = signer.unsign(token, max_age=60 * 60).decode()
        if event_code != event_slug:
            raise HTTPException(status_code=403, detail="Invalid session for this event.")
    except BadSignature:
        return RedirectResponse(url="/")

    with Session(engine) as session:
        event = session.query(Event).filter(Event.slug == event_slug).first()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    return templates.TemplateResponse("upload_form.html", {
        "request": request,
        "event_slug": event_slug,
        "event_name": event.name
    })

@app.post("/upload/{event_slug}/{guest_id}")
async def upload_file(request: Request, event_slug: str, guest_id: int, file: UploadFile = File(...)):
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(status_code=403, detail="Not authenticated")

    try:
        event_code = signer.unsign(token, max_age=60 * 60).decode()
        if event_code != event_slug:
            raise HTTPException(status_code=403, detail="Invalid session for this event.")
    except BadSignature:
        raise HTTPException(status_code=403, detail="Invalid session token")

    base_storage_path = "/media/devmon/Elements/EventPhotoUploader/events/"
    event_path = os.path.join(base_storage_path, event_slug)

    if not os.path.exists(event_path):
        raise HTTPException(status_code=404, detail="Event not found")

    guest_folder = os.path.join(event_path, f"guest-{guest_id}")
    if not os.path.exists(guest_folder):
        os.makedirs(guest_folder)

    unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_location = os.path.join(guest_folder, unique_filename)

    # Save the file to disk using aiofiles for async file I/O
    async with aiofiles.open(file_location, 'wb') as f:
        content = await file.read()
        await f.write(content)

    # Debugging: Log file saving location and metadata
    print(f"File saved at: {file_location}")
    print(f"File details: {file.filename}, {file.content_type}, {os.path.getsize(file_location)} bytes")

    # Now, insert metadata into the filemetadata table
    with Session(engine) as session:
        # Get event info to store in metadata
        event = session.query(Event).filter(Event.slug == event_slug).first()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        # Debugging: Log event info
        print(f"Event found: {event.name}, {event.id}")

        # Create a FileMetadata entry
        file_metadata = FileMetadata(
            file_name=unique_filename,
            file_type=file.content_type,
            guest_id=guest_id,
            event_id=event.id,
            upload_timestamp=datetime.utcnow(),
            file_size=os.path.getsize(file_location)
        )

        print(f"Inserting file metadata: {file_metadata}")  # Log the metadata to be inserted
        session.add(file_metadata)
        try:
            session.commit()  # Commit the session
            print("File metadata inserted successfully.")
        except Exception as e:
            print(f"Error committing session: {e}")
            session.rollback()  # Rollback in case of an error

    return {"filename": unique_filename, "location": file_location}

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("session_token")
    response.delete_cookie("session_expiry")
    return response

@app.post("/events/") 
def create_event(event: EventCreateRequest):
    base_storage_path = "/media/devmon/Elements/EventPhotoUploader/events/"
    event_path = os.path.join(base_storage_path, event.slug)

    if not os.path.exists(base_storage_path):
        os.makedirs(base_storage_path)

    if os.path.exists(event_path):
        raise HTTPException(status_code=400, detail="Event folder already exists")

    os.makedirs(event_path)

    event_db = Event(name=event.name, slug=event.slug, storage_path=event_path)

    with Session(engine) as session:
        session.add(event_db)
        session.commit()
        session.refresh(event_db)

    return {"message": "Event created", "event": event_db}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
