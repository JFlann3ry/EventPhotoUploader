from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import select
import bcrypt, time, jwt
from datetime import datetime
from app.models import User
from app.database import SessionLocal

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