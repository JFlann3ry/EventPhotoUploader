from fastapi import APIRouter, HTTPException, Depends, status, Request, Response, Form
from sqlmodel import Session, select
from typing import Optional  # Ensure this is included
from app.models import User, Event, FileMetadata, EventType, QRCode
from app.db.session import SessionLocal, engine
from app.utils.token import create_access_token, verify_password, generate_verification_token, verify_verification_token, validate_token
from app.utils.email_utils import send_verification_email
from app.core.config import SECRET_KEY, ALGORITHM, STORAGE_ROOT, BASE_URL, EMAIL_FROM
from datetime import datetime, timedelta, date
import jwt
from fastapi.responses import RedirectResponse, FileResponse, StreamingResponse
from app.template_env import templates
import bcrypt, time
import random
import string
import re
from app.profanity_filter import PROFANITY_LIST
import smtplib
from email.mime.text import MIMEText
import qrcode
from io import BytesIO
import os
from app.export_events import export_events_to_pdf
import zipfile
import io
import traceback
from sqlalchemy.exc import SQLAlchemyError
from pathlib import Path
from app.api.v1.page import get_logged_in_user
from app.models.models import UserSession

auth_router = APIRouter()

def get_logged_in_user(request: Request):
    token = request.cookies.get("session_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
    except Exception:
        return None
    with SessionLocal() as session:
        user_session = session.exec(select(UserSession).where(UserSession.session_token == token)).first()
        if not user_session or user_session.expires_at < datetime.utcnow():
            return None
        user = session.exec(select(User).where(User.id == user_id)).first()
    return user

@auth_router.get("/login")
async def login_get(request: Request):
    user = get_logged_in_user(request)
    return templates.TemplateResponse("login.html", {"request": request, "user": user})

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

def generate_unique_code(session, length=4):
    """Generate a unique alphanumeric code that avoids profanity."""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        # Check if the code is in the profanity list
        if code in PROFANITY_LIST:
            continue
        # Check if the code already exists in the database
        existing_event = session.exec(select(Event).where(Event.event_code == code)).first()
        if not existing_event:
            return code

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
            # Show a generic error
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "user": None, "error": "Invalid email or password."}
            )
        if user.marked_for_deletion:
            # Show a specific error with a contact link
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "user": None,
                    "error": (
                        "This account has been marked for deletion. "
                        "If this is a mistake, please <a href='/contact-us'>contact us</a>."
                    )
                }
            )
        if not user.verified:
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "user": None, "error": "Please verify your email before logging in."}
            )
        # Generate session token using JWT
        payload = {
            "user_id": user.id,
            "exp": time.time() + TOKEN_EXPIRE_SECONDS
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        
        # Log session in DB
        user_agent = request.headers.get("user-agent", "")
        ip_address = request.client.host if request.client else ""
        expires_at = datetime.utcnow() + timedelta(seconds=TOKEN_EXPIRE_SECONDS)
        user_session = UserSession(
            user_id=user.id,
            session_token=token,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address
        )
        session.add(user_session)
        session.commit()
        
        response = RedirectResponse(url="/auth/profile", status_code=303)
        response.set_cookie("session_token", token, httponly=True, samesite="lax", max_age=TOKEN_EXPIRE_SECONDS, path="/")
        return response

@auth_router.get("/profile")
async def profile(request: Request):
    user = get_logged_in_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)
    context = {"request": request, "user": user}
    return templates.TemplateResponse("profile.html", context)

@auth_router.get("/logout")
async def logout(request: Request):
    token = request.cookies.get("session_token")
    with SessionLocal() as session:
        if token:
            user_sessions = session.exec(
                select(UserSession).where(UserSession.session_token == token)
            ).all()
            for user_session in user_sessions:
                session.delete(user_session)
            session.commit()
    response = RedirectResponse(url="/auth/login", status_code=303)
    response.delete_cookie("session_token")
    return response

@auth_router.post("/sign-up")
async def register_user(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    next: Optional[str] = None  # Capture the redirect URL
):
    with SessionLocal() as session:
        # Check for existing user by email
        statement = select(User).where(User.email == email)
        results = session.exec(statement)
        existing_user = results.first()
        if existing_user:
            return templates.TemplateResponse(
                "sign_up.html",
                {"request": request, "error": "An account with this email already exists."}
            )

        # Hash the password
        hashed = bcrypt.hashpw(password.encode("utf8"), bcrypt.gensalt())
        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            hashed_password=hashed.decode("utf8"),
            verified=False,
            pricing_id=1  # Automatically assign Free Plan
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        # Generate verification token and send email
        token = generate_verification_token(email)
        send_verification_email(email, token)

    # Redirect to the next page or the pricing page by default
    redirect_url = next or "/pricing"
    return RedirectResponse(url=redirect_url, status_code=303)

@auth_router.get("/gallery")
async def user_gallery(request: Request, event_id: int = None):
    user = get_logged_in_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)
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

        # auto‐select if there's only one event
        selected_event = None
        if event_id:
            selected_event = next((e for e in events if e.id == event_id), None)
        elif len(events) == 1:
            selected_event = events[0]

        files = []
        if selected_event:
            event_folder = selected_event.storage_path
            full_event_path = os.path.join(STORAGE_ROOT, event_folder)
            seen_files = set()  # ← Add this line
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
    user = get_logged_in_user(request)
    with SessionLocal() as session:
        event = session.exec(select(Event).where(Event.id == event_id)).first()
        event_types = session.exec(select(EventType)).all()
    return templates.TemplateResponse(
        "event_details.html",
        {
            "request": request,
            "event": event,
            "event_types": event_types,
            "field_errors": {},
            "user": user
        }
    )

@auth_router.post("/event-details/{event_id}")
async def update_event_details(
    request: Request,
    event_id: int,
    name: str = Form(...),
    event_date: str = Form(...),
    event_type_id: int = Form(...),
    welcome_message: str = Form(...)
):
    user = get_logged_in_user(request)
    with SessionLocal() as session:
        event = session.exec(select(Event).where(Event.id == event_id)).first()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        event.name = name
        event.date = datetime.strptime(event_date, "%Y-%m-%d")
        event.event_type_id = event_type_id
        event.welcome_message = welcome_message
        session.add(event)
        session.commit()
        session.refresh(event)
    event_types = session.exec(select(EventType)).all()
    return templates.TemplateResponse(
        "event_details.html",
        {
            "request": request,
            "event": event,
            "event_types": event_types,
            "success": "Event details updated successfully!",
            "field_errors": {},
            "user": user
        }
    )

@auth_router.get("/events")
async def list_events(request: Request):
    user = get_logged_in_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)
    with SessionLocal() as session:
        events = session.exec(select(Event).where(Event.user_id == user.id)).all()
    return templates.TemplateResponse(
        "events.html",
        {"request": request, "events": events, "user": user}
    )

@auth_router.get("/create-event")
async def create_event_get(request: Request):
    user = get_logged_in_user(request)
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
    return templates.TemplateResponse("create_event.html", {"request": request, "event_types": event_types, "user": user})

@auth_router.post("/create-event")
async def create_event_post(
    request: Request,
    name: str = Form(...),
    event_date: str = Form(...),
    event_type_id: int = Form(...),
    welcome_message: str = Form(...)
):
    user = get_logged_in_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)
    with SessionLocal() as session:
        user = session.exec(select(User).where(User.id == user.id)).first()
        if user.pricing.tier == "Free":
            events = session.exec(select(Event).where(Event.user_id == user.id)).all()
            if len(events) >= 1:  # Free tier allows 1 event
                return templates.TemplateResponse(
                    "error.html",
                    {"request": request, "error": "Upgrade your plan to create more events."}
                )
        try:
            parsed_date = datetime.strptime(event_date, "%Y-%m-%d").date()
        except ValueError:
            event_types = session.exec(select(EventType)).all()
            return templates.TemplateResponse(
                "create_event.html",
                {
                    "request": request,
                    "event_types": event_types,
                    "error": "Invalid event date format. Use YYYY-MM-DD.",
                    "user": user
                }
            )
        event_code = generate_unique_code(session)
        event_password = generate_unique_code(session)
        event = Event(
            user_id=user.id,
            name=name,
            date=parsed_date,
            event_type_id=event_type_id,
            welcome_message=welcome_message,
            storage_path="",
            event_code=event_code,
            event_password=event_password,
            pricing_id=1
        )
        session.add(event)
        session.commit()
        session.refresh(event)
        event.storage_path = str(event.id)
        session.add(event)
        session.commit()
        event_folder_path = Path(STORAGE_ROOT) / event.storage_path
        event_folder_path.mkdir(parents=True, exist_ok=True)
    return RedirectResponse(url=f"/auth/event-details/{event.id}", status_code=303)

@auth_router.get("/scan-qr/{event_id}")
async def scan_qr_code(event_id: int):
    with SessionLocal() as session:
        # Retrieve the QR code entry for the event
        qr_code = session.query(QRCode).filter(QRCode.event_id == event_id).first()
        if not qr_code:
            raise HTTPException(status_code=404, detail="QR Code not found")
        
        # Increment the scanned count
        qr_code.scanned_count += 1
        session.add(qr_code)  # Ensure the object is marked as updated
        session.commit()  # Commit the changes to the database

        # Redirect to the full URL stored in the database
        return RedirectResponse(url=qr_code.qr_url)

@auth_router.get("/verify-email")
async def verify_email(token: str, request: Request):
    email = verify_verification_token(token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired token.")
    
    with SessionLocal() as session:
        user = session.exec(select(User).where(User.email == email)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")
        
        user.verified = True
        session.add(user)
        session.commit()

    return templates.TemplateResponse("thank_you_verification.html", {"request": request})

@auth_router.get("/delete-account")
async def delete_account_get(request: Request):
    user = get_logged_in_user(request)  # <-- Add this line
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)
    return templates.TemplateResponse("delete_account.html", {"request": request, "user": user})

@auth_router.post("/delete-account")
async def delete_account_post(request: Request, reason: str = Form(None)):
    user = get_logged_in_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)
    with SessionLocal() as session:
        # Delete all user sessions
        sessions = session.exec(
            select(UserSession).where(UserSession.user_id == user.id)
        ).all()
        for s in sessions:
            session.delete(s)
        # Optionally, log the reason somewhere (not shown)
        # Delete the user
        session.delete(user)
        session.commit()
    response = RedirectResponse(url="/auth/login", status_code=303)
    response.delete_cookie("session_token")
    return response

@auth_router.get("/event-qr")
async def event_qr(event_id: int):
    with SessionLocal() as session:
        event = session.exec(select(Event).where(Event.id == event_id)).first()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        # Generate the QR code data (URL for upload)
        qr_data = f"/upload/{event.event_code}/{event.event_password}"
        img = qrcode.make(qr_data)
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return StreamingResponse(buf, media_type="image/png")

@auth_router.post("/upgrade-plan")
async def upgrade_plan(request: Request, pricing_id: int = Form(...)):
    user = get_logged_in_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)
    with SessionLocal() as session:
        user = session.exec(select(User).where(User.id == user.id)).first()
        if user:
            user.pricing_id = pricing_id
            session.add(user)
            session.commit()
    return RedirectResponse(url="/pricing", status_code=303)

@auth_router.post("/auth/choose-plan")
async def choose_plan(request: Request, pricing_id: int = Form(...), redirect_url: str = Form(...)):
    user = get_logged_in_user(request)
    if not user:
        # If the user is not logged in, redirect to the sign-up page
        response = RedirectResponse(url=f"/auth/sign-up?next={redirect_url}", status_code=303)
        return response

    # If the user is logged in, redirect to the payment page (placeholder for now)
    response = RedirectResponse(url=f"/auth/payment?pricing_id={pricing_id}", status_code=303)
    return response

@auth_router.get("/auth/payment")
async def payment_page(request: Request, pricing_id: int):
    with SessionLocal() as session:
        pricing = session.exec(select(Pricing).where(Pricing.id == pricing_id)).first()
        if not pricing:
            raise HTTPException(status_code=404, detail="Pricing plan not found.")
    return templates.TemplateResponse("payment.html", {"request": request, "pricing": pricing})

@auth_router.post("/auth/process-payment")
async def process_payment(request: Request, pricing_id: int = Form(...)):
    user = get_logged_in_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)

    # Placeholder logic for payment processing
    with SessionLocal() as session:
        user = session.exec(select(User).where(User.id == user.id)).first()
        if user:
            user.pricing_id = pricing_id  # Upgrade the user's plan
            session.add(user)
            session.commit()

    return RedirectResponse(url="/auth/profile", status_code=303)

