from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from app.models import User, Event
from app.database import SessionLocal
from sqlmodel import select
import jwt
import smtplib
from email.mime.text import MIMEText
from app.config import EMAIL_FROM, EMAIL_PASSWORD, WEBSITE_NAME
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="templates")

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

def get_logged_in_user(request: Request):
    token = request.cookies.get("session_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        with SessionLocal() as session:
            user = session.query(User).filter(User.id == user_id).first()
            return user
    except Exception:
        return None

@router.get("/how-it-works")
async def how_it_works(request: Request):
    user = get_logged_in_user(request)
    return templates.TemplateResponse(
        "how_it_works.html",
        {
            "request": request,
            "user": user,
            "WEBSITE_NAME": WEBSITE_NAME,
            "current_year": datetime.now().year,
        }
    )

@router.get("/pricing")
async def pricing(request: Request):
    user = get_logged_in_user(request)
    return templates.TemplateResponse("pricing.html", {"request": request, "user": user})

@router.get("/guest-login")
async def guest_login(request: Request):
    user = get_logged_in_user(request)
    return templates.TemplateResponse("guest_login.html", {"request": request, "user": user})

@router.post("/guest-login")
async def guest_login_post(
    request: Request,
    guest_code: str = Form(...),
    password: str = Form(...)
):
    with SessionLocal() as session:
        event = session.exec(
            select(Event).where(Event.event_code == guest_code, Event.event_password == password)
        ).first()
        if event:
            # Redirect to the upload page for this event
            return RedirectResponse(
                url=f"/upload/{event.event_code}/{event.event_password}", status_code=303
            )
        else:
            user = get_logged_in_user(request)
            return templates.TemplateResponse(
                "guest_login.html",
                {"request": request, "user": user, "error": "Invalid event code or password."}
            )

@router.get("/sign-up")
async def sign_up(request: Request):
    user = get_logged_in_user(request)
    return templates.TemplateResponse("sign_up.html", {"request": request, "user": user})

@router.get("/about")
async def about(request: Request):
    user = get_logged_in_user(request)
    return templates.TemplateResponse("about.html", {"request": request, "user": user})

@router.get("/help-center")
async def help_center(request: Request):
    user = get_logged_in_user(request)
    return templates.TemplateResponse("help_center.html", {"request": request, "user": user})

@router.get("/contact-us")
async def contact_us_get(request: Request):
    user = get_logged_in_user(request)
    return templates.TemplateResponse("contact_us.html", {"request": request, "user": user})

@router.post("/contact-us")
async def contact_us_post(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    topic: str = Form(...),
    message: str = Form(...)
):
    # Send email to site owner
    owner_subject = f"Contact Us: {topic} from {full_name}"
    owner_body = f"""
    Name: {full_name}
    Email: {email}
    Topic: {topic}
    Message:
    {message}
    """
    msg = MIMEText(owner_body)
    msg["Subject"] = owner_subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_FROM

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.sendmail(EMAIL_FROM, EMAIL_FROM, msg.as_string())

    # Send thank you email to user
    thank_subject = "Thank you for contacting Event Snap"
    thank_body = f"""Hi {full_name},

Thank you for getting in touch with us regarding "{topic}".
We have received your message and will get back to you as soon as possible.

Best regards,
Event Snap Team
"""
    thank_msg = MIMEText(thank_body)
    thank_msg["Subject"] = thank_subject
    thank_msg["From"] = EMAIL_FROM
    thank_msg["To"] = email

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.sendmail(EMAIL_FROM, email, thank_msg.as_string())

    user = get_logged_in_user(request)
    return templates.TemplateResponse(
        "contact_us.html",
        {"request": request, "user": user, "success": "Thank you for contacting us! We have received your message."}
    )

@router.get("/terms-and-conditions")
async def terms_and_conditions(request: Request):
    user = get_logged_in_user(request)
    return templates.TemplateResponse(
        "terms_and_conditions.html",
        {
            "request": request,
            "user": user,
            "WEBSITE_NAME": WEBSITE_NAME,
            "current_year": datetime.now().year,
            "EMAIL_FROM": EMAIL_FROM
        }
    )