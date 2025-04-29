from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, FileResponse
from app.template_env import templates
from sqlmodel import select
import bcrypt, time, jwt
from datetime import datetime, date
from app.models import User, Event, FileMetadata, EventType
from app.database import SessionLocal
from fastapi import Form
import qrcode
from io import BytesIO
from fastapi.responses import StreamingResponse
import os
from app.export_events import export_events_to_pdf
import zipfile
import io
import traceback
from sqlalchemy.exc import SQLAlchemyError
from pathlib import Path
from app.config import STORAGE_ROOT  # Import STORAGE_ROOT
import re

auth_router = APIRouter()

# Secret configuration (in a production setting store these securely)
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
TOKEN_EXPIRE_SECONDS = 3600

def is_valid_password(password: str) -> bool:
    # At least 6 characters, 1 number, 1 special character, 1 uppercase letter
    if len(password) < 6:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    if not re.search(r"[^A-Za-z0-9]", password):
        return False
    return True

@auth_router.get("/login")
async def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@auth_router.post("/login")
async def login_post(
    request: Request, 
    email: str = Form(...), 
    password: str = Form(...)
):
    with SessionLocal() as session:
        statement = select(User).where(User.email == email)
        results = session.exec(statement)
        user = results.first()
        if not user or not bcrypt.checkpw(password.encode("utf8"), user.hashed_password.encode("utf8")):
            raise HTTPException(status_code=400, detail="Invalid email or password.")
        # Generate session token using JWT
        payload = {
            "user_id": user.id,
            "exp": time.time() + TOKEN_EXPIRE_SECONDS
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        response = RedirectResponse(url="/auth/profile", status_code=303)
        response.set_cookie("session_token", token)
        return response

@auth_router.get("/profile")
async def profile(request: Request):
    token = request.cookies.get("session_token")
    if not token:
        return RedirectResponse(url="/auth/login", status_code=303)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
    except Exception:
        return RedirectResponse(url="/auth/login", status_code=303)
    with SessionLocal() as session:
        statement = select(User).where(User.id == user_id)
        results = session.exec(statement)
        user = results.first()
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)
    context = {"request": request, "user": user}
    return templates.TemplateResponse("profile.html", context)

@auth_router.get("/logout")
async def logout():
    response = RedirectResponse(url="/auth/login", status_code=303)
    response.delete_cookie("session_token")
    return response

@auth_router.post("/sign-up")
async def register_user(
    first_name: str = Form(...),
    last_name: str = Form(...), 
    event_date: str = Form(...),  # expecting YYYY-MM-DD
    email: str = Form(...),
    password: str = Form(...)
):
    if not is_valid_password(password):
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters long, contain at least one uppercase letter, one number, and one special character."
        )
    with SessionLocal() as session:
        # Check for existing user by email
        statement = select(User).where(User.email == email)
        results = session.exec(statement)
        existing_user = results.first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already exists.")
            
        # Parse event_date string to date object
        try:
            parsed_date = datetime.strptime(event_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid event date format. Use YYYY-MM-DD.")
        
        # Hash the password
        hashed = bcrypt.hashpw(password.encode("utf8"), bcrypt.gensalt())
        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            hashed_password=hashed.decode("utf8")
        )
        session.add(user)
        session.commit()
        session.refresh(user)  # Get the new user's ID

        # Create an Event for the new user
        event = Event(
            user_id=user.id,
            name="My Event Name",
            date=parsed_date,
            welcome_message="Welcome to our event! Please upload your favorite photos and memories here.",
            storage_path="",  # <-- TEMPORARY, will update after commit
            event_code=0,
            event_password="",
            pricing_id=1
        )
        session.add(event)
        session.commit()
        session.refresh(event)
        event.storage_path = str(event.id)
        session.add(event)
        session.commit()

        return RedirectResponse(url="/auth/profile", status_code=303)

@auth_router.get("/gallery")
async def user_gallery(request: Request, event_id: int = None):
    token = request.cookies.get("session_token")
    if not token:
        return RedirectResponse(url="/auth/login", status_code=303)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
    except Exception:
        return RedirectResponse(url="/auth/login", status_code=303)
    with SessionLocal() as session:
        user = session.exec(select(User).filter(User.id == user_id)).first()
        if not user:
            return RedirectResponse(url="/auth/login", status_code=303)
        events = session.exec(select(Event).filter(Event.user_id == user_id)).all()
        # Determine which event to show
        selected_event = None
        if event_id:
            selected_event = next((e for e in events if e.id == event_id), None)
        else:
            selected_event = events[0] if events else None
        files = []
        seen_files = set()
        if selected_event:
            event_folder = selected_event.storage_path
            full_event_path = os.path.join(STORAGE_ROOT, event_folder)
            if os.path.exists(full_event_path):
                for guest_id in os.listdir(full_event_path):
                    guest_folder = os.path.join(full_event_path, guest_id)
                    if os.path.isdir(guest_folder):
                        for filename in os.listdir(guest_folder):
                            relative_path = os.path.relpath(guest_folder, STORAGE_ROOT)
                            filepath = os.path.join("/media", relative_path, filename)
                            if filepath in seen_files:
                                continue
                            seen_files.add(filepath)
                            files.append({
                                "filename": filename,
                                "filepath": filepath
                            })
    context = {
        "request": request,
        "user": user,
        "files": files,
        "events": events,
        "selected_event": selected_event
    }
    return templates.TemplateResponse("gallery.html", context)

@auth_router.get("/download/{file_id}")
async def download_file(file_id: int):
    with SessionLocal() as session:
        file = session.exec(FileMetadata).filter(FileMetadata.id == file_id).first()
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        # Build the file path (adjust as needed)
        event = session.exec(Event).filter(Event.id == file.event_id).first()
        file_path = Path(event.storage_path) / file.file_name
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found on disk")
        return FileResponse(path=str(file_path), filename=file.file_name, media_type="application/octet-stream")

@auth_router.get("/event-details/{event_id}")
async def event_details(request: Request, event_id: int):
    token = request.cookies.get("session_token")
    if not token:
        return RedirectResponse(url="/auth/login", status_code=303)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
    except Exception:
        return RedirectResponse(url="/auth/login", status_code=303)
    with SessionLocal() as session:
        # Use select() to create a SQL expression
        user = session.exec(select(User).filter(User.id == user_id)).first()
        event = session.exec(select(Event).filter(Event.id == event_id, Event.user_id == user_id)).first()
        event_types = session.exec(select(EventType)).all()
        # If event does not exist, show the same form but with empty/default values
        if not event:
            context = {"request": request, "user": user, "event": None, "event_types": event_types, "event_id": event_id}
            return templates.TemplateResponse("event_details.html", context)
    context = {"request": request, "user": user, "event": event, "event_types": event_types,  "event_id": event_id}
    return templates.TemplateResponse("event_details.html", context)

@auth_router.post("/event-details/{event_id}")
async def update_event_details(
    request: Request,
    event_id: int,
    name: str = Form(...),
    event_date: str = Form(...),
    event_type_id: int = Form(...),
    welcome_message: str = Form(...),
):
    with SessionLocal() as session:
        user_id = 4  # Replace with your actual user ID retrieval logic
        event_folder = os.path.join(STORAGE_ROOT, str(user_id))
        folder_created = False
        if not os.path.exists(event_folder):
            os.makedirs(event_folder, exist_ok=True)
            folder_created = True
        # Parse event_date
        print("DEBUG: Received event_date:", event_date)
        parsed_date = None
        if event_date:
            try:
                parsed_date = datetime.strptime(event_date, "%Y-%m-%d").date()
            except ValueError:
                print("DEBUG: Failed to parse event_date")
                parsed_date = None
        if not parsed_date:
            # Re-render the form with an error message
            event_types = session.query(EventType).all()
            context = {
                "request": request,
                "user": session.query(User).filter(User.id == user_id).first(),
                "event": session.query(Event).filter(Event.id == event_id, Event.user_id == user_id).first(),
                "event_types": event_types,
                "error": "Event date is required and must be valid.",
                "event_id": event_id
            }
            return templates.TemplateResponse("event_details.html", context)

        # Check if the parsed date is in the past
        if parsed_date < date.today():
            event_types = session.query(EventType).all()
            context = {
                "request": request,
                "user": session.query(User).filter(User.id == user_id).first(),
                "event": session.query(Event).filter(Event.id == event_id, Event.user_id == user_id).first(),
                "event_types": event_types,
                "error": "Event date cannot be in the past.",
                "event_id": event_id
            }
            return templates.TemplateResponse("event_details.html", context)

        event = session.query(Event).filter(Event.id == event_id, Event.user_id == user_id).first()
        if event:
            event.name = name
            event.date = parsed_date
            event.event_type_id = event_type_id
            event.welcome_message = welcome_message
            # Do not overwrite storage_path unless you are intentionally moving files.
            # If you must, use:
            event.storage_path = str(event.id)
        else:
            event = Event(
                user_id=user_id,
                name=name,
                date=parsed_date,
                event_type_id=event_type_id,
                welcome_message=welcome_message,
                storage_path="",  # <-- TEMPORARY, will update after commit
                event_code=0,
                event_password="",
                pricing_id=1
            )
            session.add(event)
            session.commit()
            session.refresh(event)
            event.storage_path = str(event.id)
            session.add(event)
            session.commit()

    return RedirectResponse(url="/auth/events", status_code=303)

@auth_router.get("/events")
async def list_events(request: Request):
    token = request.cookies.get("session_token")
    if not token:
        return RedirectResponse(url="/auth/login", status_code=303)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
    except Exception:
        return RedirectResponse(url="/auth/login", status_code=303)
    with SessionLocal() as session:
        events = session.exec(select(Event).where(Event.user_id == user_id)).all()
    return templates.TemplateResponse("event_list.html", {"request": request, "events": events})

@auth_router.get("/create-event")
async def create_event_get(request: Request):
    token = request.cookies.get("session_token")
    if not token:
        return RedirectResponse(url="/auth/login", status_code=303)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
    except Exception:
        return RedirectResponse(url="/auth/login", status_code=303)
    with SessionLocal() as session:
        event_types = session.exec(select(EventType)).all()
    return templates.TemplateResponse("create_event.html", {"request": request, "event_types": event_types})

@auth_router.post("/create-event")
async def create_event_post(
    request: Request,
    name: str = Form(...),
    event_date: str = Form(...),
    event_type_id: int = Form(...),
    welcome_message: str = Form(...)
):
    token = request.cookies.get("session_token")
    if not token:
        return RedirectResponse(url="/auth/login", status_code=303)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
    except Exception:
        return RedirectResponse(url="/auth/login", status_code=303)
    with SessionLocal() as session:
        try:
            parsed_date = datetime.strptime(event_date, "%Y-%m-%d").date()
        except ValueError:
            event_types = session.exec(select(EventType)).all()
            return templates.TemplateResponse(
                "create_event.html",
                {
                    "request": request,
                    "event_types": event_types,
                    "error": "Invalid event date format. Use YYYY-MM-DD."
                }
            )
        event = Event(
            user_id=user_id,
            name=name,
            date=parsed_date,
            event_type_id=event_type_id,
            welcome_message=welcome_message,
            storage_path="",  # Will update after commit
            event_code=0,
            event_password="",
            pricing_id=1
        )
        session.add(event)
        session.commit()
        session.refresh(event)
        event.storage_path = str(event.id)
        session.add(event)
        session.commit()
    return RedirectResponse(url="/auth/events", status_code=303)

