from fastapi import APIRouter, HTTPException, Request, Form, status, Depends
from fastapi.responses import RedirectResponse, StreamingResponse
from sqlmodel import select, Session
from typing import Optional
from datetime import datetime, timedelta, timezone
from io import BytesIO
import random
import string
import re
import time
import qrcode
import jwt
import bcrypt

from app.models import User, Event, UserSession, Pricing
from app.db.session import SessionLocal, get_session
from app.utils.token import (
    generate_verification_token,
    verify_verification_token,
)
from app.utils.email_utils import send_verification_email
from app.profanity_filter import PROFANITY_LIST
from app.core.config import SECRET_KEY, ALGORITHM, TOKEN_EXPIRE_SECONDS
from app.template_env import templates

auth_router = APIRouter()


def get_logged_in_user(request: Request) -> Optional[User]:
    token = request.cookies.get("session_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
    except jwt.PyJWTError:
        return None

    with SessionLocal() as session:
        us = session.exec(
            select(UserSession).where(UserSession.session_token == token)
        ).first()
        if not us:
            return None
        # ensure expires_at is TZ‐aware
        exp = us.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp < datetime.now(timezone.utc):
            return None
        user = session.exec(select(User).where(User.id == user_id)).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return user


def is_valid_password(password: str) -> bool:
    if len(password) < 6:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"\W", password):
        return False
    return True


def generate_unique_code(session, length: int = 4) -> str:
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        if code in PROFANITY_LIST:
            continue
        exists = session.exec(select(Event).where(Event.event_code == code)).first()
        if not exists:
            return code


@auth_router.get("/login")
async def login_get(request: Request):
    user = get_logged_in_user(request)
    return templates.TemplateResponse("login.html", {"request": request, "user": user})


@auth_router.post("/login")
async def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    with SessionLocal() as session:
        user = session.exec(select(User).where(User.email == email)).first()
        if not user or not bcrypt.checkpw(password.encode(), user.hashed_password.encode()):
            return templates.TemplateResponse(
                "login.html", {"request": request, "error": "Invalid email or password."}
            )
        if not user.verified:
            return templates.TemplateResponse(
                "login.html", {"request": request, "error": "Please verify your email."}
            )

        payload = {"user_id": user.id, "exp": time.time() + TOKEN_EXPIRE_SECONDS}
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

        us = UserSession(
            user_id=user.id,
            session_token=token,
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=TOKEN_EXPIRE_SECONDS),
            user_agent=request.headers.get("user-agent", ""),
            ip_address=request.client.host if request.client else "",
        )
        session.add(us)
        session.commit()

        response = RedirectResponse(url="/auth/profile", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(
            "session_token", token, httponly=True, samesite="lax", max_age=TOKEN_EXPIRE_SECONDS
        )
        return response


@auth_router.get("/logout")
async def logout(request: Request):
    token = request.cookies.get("session_token")
    with SessionLocal() as session:
        if token:
            sessions = session.exec(
                select(UserSession).where(UserSession.session_token == token)
            ).all()
            for us in sessions:
                session.delete(us)
            session.commit()
    response = RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("session_token")
    return response


@auth_router.post("/sign-up")
async def register_user(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    next: Optional[str] = None,
):
    with SessionLocal() as session:
        existing = session.exec(select(User).where(User.email == email)).first()
        if existing:
            return templates.TemplateResponse(
                "sign_up.html",
                {"request": request, "error": "An account with this email already exists."},
            )
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            hashed_password=hashed,
            verified=False,
        )
        session.add(user)
        session.commit()

        token = generate_verification_token(email)
        send_verification_email(email, token)

    return RedirectResponse(url=next or "/pricing", status_code=status.HTTP_303_SEE_OTHER)


@auth_router.get("/profile")
async def profile(
    request: Request,
    session: Session = Depends(get_session),
):
    user = get_logged_in_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=status.SEE_OTHER)

    # load pricing tier
    pricing = session.exec(
        select(Pricing).where(Pricing.id == user.pricing_id)
    ).first()

    # load user’s events
    events = session.exec(
        select(Event).where(Event.user_id == user.id).order_by(Event.date)
    ).all()

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user": user,
            "pricing": pricing,
            "events": events,
        },
    )


@auth_router.get("/verify-email")
async def verify_email(token: str, request: Request):
    email = verify_verification_token(token)
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token.")
    with SessionLocal() as session:
        user = session.exec(select(User).where(User.email == email)).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        user.verified = True
        session.add(user)
        session.commit()
    return templates.TemplateResponse("thank_you_verification.html", {"request": request})


@auth_router.get("/event-qr")
async def event_qr(event_id: int):
    with SessionLocal() as session:
        event = session.exec(select(Event).where(Event.id == event_id)).first()
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        qr_data = f"/upload/{event.event_code}/{event.event_password}"
        img = qrcode.make(qr_data)
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return StreamingResponse(buf, media_type="image/png")


@auth_router.get("/delete-account")
async def delete_account_get(
    request: Request,
    user: User = Depends(get_logged_in_user),
):
    if not user:
        return RedirectResponse("/auth/login")
    return templates.TemplateResponse(
        "delete_account.html",
        {"request": request, "user": user},
    )


@auth_router.post("/delete-account")
async def delete_account_post(
    request: Request,
    session: Session = Depends(get_session),
    user: User = Depends(get_logged_in_user),
):
    if not user:
        return RedirectResponse("/auth/login")
    # delete all user sessions
    sessions = session.exec(
        select(UserSession).where(UserSession.user_id == user.id)
    ).all()
    for us in sessions:
        session.delete(us)

    # delete all user events
    events = session.exec(
        select(Event).where(Event.user_id == user.id)
    ).all()
    for ev in events:
        session.delete(ev)

    # finally delete the user
    session.delete(user)
    session.commit()
    resp = RedirectResponse("/", status_code=303)
    resp.delete_cookie("session_token")
    return resp