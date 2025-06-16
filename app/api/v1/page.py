# Import necessary modules and libraries
from fastapi import APIRouter, Request, Form, HTTPException  # FastAPI utilities
from app.template_env import templates  # Jinja2 template environment
from fastapi.responses import RedirectResponse  # For HTTP redirects
from app.models import User, Event  # Database models
from app.db.session import SessionLocal, engine  # Database session utilities
from sqlmodel import select, Session  # ORM for database queries
import jwt  # For decoding JWT tokens
import smtplib  # For sending emails
from email.mime.text import MIMEText  # For constructing email messages
from app.core.config import EMAIL_FROM, EMAIL_PASSWORD, WEBSITE_NAME, SECRET_KEY, ALGORITHM  # Config variables
from datetime import datetime  # For date and time handling
from app.models.models import Pricing  # Pricing model

# Initialize routers for page-related and authentication-related endpoints
page_router = APIRouter()
auth_router = APIRouter()

# ─── Helper Functions ───────────────────────────────────────────────────────

def get_logged_in_user(request: Request):
    """
    Retrieve the currently logged-in user based on the session token in cookies.
    """
    token = request.cookies.get("session_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
    except Exception:
        return None
    with SessionLocal() as session:
        user = session.exec(select(User).where(User.id == user_id)).first()
    return user

# ─── Page Endpoints ─────────────────────────────────────────────────────────

@page_router.get("/how-it-works")
async def how_it_works(request: Request):
    """
    Render the "How It Works" page.
    """
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

@page_router.get("/pricing")
async def pricing_page(request: Request):
    """
    Render the pricing page with available plans.
    """
    user = get_logged_in_user(request)
    with SessionLocal() as session:
        pricing = session.exec(select(Pricing)).all()
    return templates.TemplateResponse("pricing.html", {"request": request, "pricing": pricing, "user": user})

@page_router.get("/guest-login")
async def guest_login(request: Request):
    """
    Render the guest login page.
    """
    user = get_logged_in_user(request)
    return templates.TemplateResponse("guest_login.html", {"request": request, "user": user})

@page_router.post("/guest-login")
async def guest_login_post(
    request: Request,
    guest_code: str = Form(...),
    password: str = Form(...),
):
    """
    Handle guest login by validating event code and password.
    """
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

@page_router.get("/sign-up")
async def sign_up(request: Request):
    """
    Render the sign-up page.
    """
    user = get_logged_in_user(request)
    return templates.TemplateResponse("sign_up.html", {"request": request, "user": user})

@page_router.get("/about")
async def about(request: Request):
    """
    Render the "About Us" page.
    """
    user = get_logged_in_user(request)
    return templates.TemplateResponse("about.html", {"request": request, "user": user})

@page_router.get("/help-center")
async def help_center(request: Request):
    """
    Render the Help Center page.
    """
    user = get_logged_in_user(request)
    return templates.TemplateResponse("help_center.html", {"request": request, "user": user})

@page_router.get("/contact-us")
async def contact_us_get(request: Request):
    """
    Render the Contact Us page.
    """
    user = get_logged_in_user(request)
    return templates.TemplateResponse("contact_us.html", {"request": request, "user": user})

@page_router.post("/contact-us")
async def contact_us_post(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    topic: str = Form(...),
    message: str = Form(...),
):
    """
    Handle Contact Us form submission.
    - Sends an email to the site owner.
    - Sends a thank-you email to the user.
    """
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

    # Send thank-you email to user
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

@page_router.get("/terms-and-conditions")
async def terms_and_conditions(request: Request):
    """
    Render the Terms and Conditions page.
    """
    user = get_logged_in_user(request)
    return templates.TemplateResponse(
        "terms_and_conditions.html",
        {
            "request": request,
            "user": user,
            "WEBSITE_NAME": WEBSITE_NAME,
            "current_year": datetime.now().year,
            "EMAIL_FROM": EMAIL_FROM,
        }
    )

@auth_router.get("/profile")
async def profile(request: Request):
    """
    Render the user's profile page.
    """
    user = get_logged_in_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)
    context = {"request": request, "user": user}
    return templates.TemplateResponse("profile.html", context)