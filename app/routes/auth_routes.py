from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import select
import bcrypt, time, jwt
from datetime import datetime
from app.models import User, Event, FileMetadata, EventType
from app.database import SessionLocal
from fastapi import Form
import qrcode
from io import BytesIO
from fastapi.responses import StreamingResponse
from app.config import STORAGE_ROOT
import os
from app.export_events import export_events_to_pdf
import zipfile
import io

auth_router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Secret configuration (in a production setting store these securely)
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
TOKEN_EXPIRE_SECONDS = 3600

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
    event_date: str = Form(...),  # expecting YYYY-MM-DD
    email: str = Form(...),
    password: str = Form(...)
):
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
            event_date=parsed_date,
            email=email,
            hashed_password=hashed.decode("utf8")
        )
        session.add(user)
        session.commit()
        # Optionally, set a session cookie here if you want the user to be logged in immediately
        return RedirectResponse(url="/auth/profile", status_code=303)

@auth_router.get("/gallery")
async def user_gallery(request: Request):
    token = request.cookies.get("session_token")
    if not token:
        return RedirectResponse(url="/auth/login", status_code=303)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
    except Exception:
        return RedirectResponse(url="/auth/login", status_code=303)
    with SessionLocal() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return RedirectResponse(url="/auth/login", status_code=303)
        event = session.query(Event).filter(Event.user_id == user_id).first()
        files = []
        if event:
            event_folder = event.storage_path
            if os.path.exists(event_folder):
                for guest_id in os.listdir(event_folder):
                    guest_folder = os.path.join(event_folder, guest_id)
                    if os.path.isdir(guest_folder):
                        for filename in os.listdir(guest_folder):
                            files.append({
                                "filename": filename,
                                "filepath": f"/static/events/{event.id}/{guest_id}/{filename}"
                            })
    context = {"request": request, "user": user, "files": files}
    return templates.TemplateResponse("gallery.html", context)

@auth_router.get("/download/{file_id}")
async def download_file(file_id: int):
    with SessionLocal() as session:
        file = session.query(FileMetadata).filter(FileMetadata.id == file_id).first()
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        # Build the file path (adjust as needed)
        event = session.query(Event).filter(Event.id == file.event_id).first()
        file_path = Path(event.storage_path) / file.filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found on disk")
        return FileResponse(path=str(file_path), filename=file.filename, media_type="application/octet-stream")

@auth_router.get("/event-details")
async def event_details(request: Request):
    token = request.cookies.get("session_token")
    if not token:
        return RedirectResponse(url="/auth/login", status_code=303)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
    except Exception:
        return RedirectResponse(url="/auth/login", status_code=303)
    with SessionLocal() as session:
        user = session.query(User).filter(User.id == user_id).first()
        event = session.query(Event).filter(Event.user_id == user_id).first()
        event_types = session.query(EventType).all()
        # If event does not exist, show the same form but with empty/default values
        if not event:
            context = {"request": request, "user": user, "event": None, "event_types": event_types}
            return templates.TemplateResponse("event_details.html", context)
    context = {"request": request, "user": user, "event": event, "event_types": event_types}
    return templates.TemplateResponse("event_details.html", context)

@auth_router.post("/event-details")
async def update_event_details(
    request: Request,
    name: str = Form(...),
    event_date: str = Form(...),
    event_type_id: int = Form(...),
    welcome_message: str = Form(...),
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
        event = session.query(Event).filter(Event.user_id == user_id).first()
        event_folder = os.path.join(STORAGE_ROOT, str(user_id))
        folder_created = False
        if not os.path.exists(event_folder):
            os.makedirs(event_folder, exist_ok=True)
            folder_created = True
        # Parse event_date
        parsed_date = None
        if event_date:
            try:
                parsed_date = datetime.strptime(event_date, "%Y-%m-%d").date()
            except ValueError:
                parsed_date = None
        if event:
            event.name = name
            event.event_date = parsed_date
            event.event_type_id = event_type_id
            event.welcome_message = welcome_message
            event.storage_path = event_folder
        else:
            event = Event(
                user_id=user_id,
                name=name,
                event_date=parsed_date,
                event_type_id=event_type_id,
                welcome_message=welcome_message,
                storage_path=event_folder
            )
            session.add(event)
        session.commit()
        if folder_created:
            export_events_to_pdf()
    return RedirectResponse(url="/auth/event-details", status_code=303)

@auth_router.get("/event-qr")
async def event_qr(request: Request):
    token = request.cookies.get("session_token")
    if not token:
        return RedirectResponse(url="/auth/login", status_code=303)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
    except Exception:
        return RedirectResponse(url="/auth/login", status_code=303)
    with SessionLocal() as session:
        event = session.query(Event).filter(Event.user_id == user_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        upload_url = f"http://100.98.194.29:8000/upload/{event.id}"
        qr = qrcode.make(upload_url)
        buf = BytesIO()
        qr.save(buf, format="PNG")
        buf.seek(0)
        return StreamingResponse(buf, media_type="image/png")

@auth_router.get("/download-all")
async def download_all_photos(request: Request):
    token = request.cookies.get("session_token")
    if not token:
        return RedirectResponse(url="/auth/login", status_code=303)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
    except Exception:
        return RedirectResponse(url="/auth/login", status_code=303)
    with SessionLocal() as session:
        event = session.query(Event).filter(Event.user_id == user_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        event_folder = event.storage_path
        # Collect all file paths
        file_paths = []
        if os.path.exists(event_folder):
            for guest_id in os.listdir(event_folder):
                guest_folder = os.path.join(event_folder, guest_id)
                if os.path.isdir(guest_folder):
                    for filename in os.listdir(guest_folder):
                        file_paths.append((guest_id, os.path.join(guest_folder, filename)))
        # Create ZIP in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            for guest_id, file_path in file_paths:
                arcname = f"{guest_id}/{os.path.basename(file_path)}"
                zip_file.write(file_path, arcname=arcname)
        zip_buffer.seek(0)
        return StreamingResponse(
            zip_buffer,
            media_type="application/x-zip-compressed",
            headers={"Content-Disposition": "attachment; filename=event_photos.zip"}
        )