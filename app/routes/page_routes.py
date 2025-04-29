from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.models import User
from app.database import SessionLocal
import jwt

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
    return templates.TemplateResponse("how_it_works.html", {"request": request, "user": user})

@router.get("/pricing")
async def pricing(request: Request):
    user = get_logged_in_user(request)
    return templates.TemplateResponse("pricing.html", {"request": request, "user": user})

@router.get("/guest-login")
async def guest_login(request: Request):
    user = get_logged_in_user(request)
    return templates.TemplateResponse("guest_login.html", {"request": request, "user": user})

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
async def contact_us(request: Request):
    user = get_logged_in_user(request)
    return templates.TemplateResponse("contact_us.html", {"request": request, "user": user})

@router.get("/terms-and-conditions")
async def terms_and_conditions(request: Request):
    user = get_logged_in_user(request)
    return templates.TemplateResponse("terms_and_conditions.html", {"request": request, "user": user})

@router.get("/privacy-policy")
async def privacy_policy(request: Request):
    user = get_logged_in_user(request)
    return templates.TemplateResponse("privacy_policy.html", {"request": request, "user": user})