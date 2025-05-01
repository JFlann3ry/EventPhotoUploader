from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime

from app.api.v1.auth import auth_router
from app.api.v1.event import event_router
from app.api.v1.gallery import gallery_router
from app.api.v1.page import page_router
from app.api.v1.upload import upload_router

from .db.session import init_db
from app.dummy_data import insert_dummy_event_types
from app.export_events import export_events_to_pdf
from app.core.config import STORAGE_ROOT, FACEBOOK_URL, INSTAGRAM_URL, TIKTOK_URL, WEBSITE_NAME, WEBSITE_DESCRIPTION

from app.template_env import templates  # ← your Jinja2Templates instance

# ─── Register your site globals here ───────────────────────────────────────────
templates.env.globals.update({
    "WEBSITE_NAME":        WEBSITE_NAME,
    "WEBSITE_DESCRIPTION": WEBSITE_DESCRIPTION,
    "FACEBOOK_URL":        FACEBOOK_URL,
    "INSTAGRAM_URL":       INSTAGRAM_URL,
    "TIKTOK_URL":          TIKTOK_URL,
    "current_year":        datetime.now().year,
})
# ────────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    insert_dummy_event_types()
    export_events_to_pdf()

    # ─── Create a test user if missing ───────────────────────────────────────────
    from sqlmodel import Session, select
    from app.db.session import engine
    from app.models import User
    import bcrypt, os

    TEST_EMAIL    = os.getenv("TEST_USER_EMAIL", "test1@test.com")
    TEST_PASSWORD = os.getenv("TEST_USER_PASSWORD", "T3qu1la!?!")

    with Session(engine) as session:
        exists = session.exec(
            select(User).where(User.email == TEST_EMAIL)
        ).first()
        if not exists:
            hashed = bcrypt.hashpw(TEST_PASSWORD.encode("utf8"), bcrypt.gensalt()).decode("utf8")
            test_user = User(
                first_name="Test",
                last_name="User",
                email=TEST_EMAIL,
                hashed_password=hashed,
                verified=True
            )
            session.add(test_user)
            session.commit()
    # ───────────────────────────────────────────────────────────────────────────────
    yield

app = FastAPI(lifespan=lifespan)

app.mount("/media", StaticFiles(directory=STORAGE_ROOT), name="media")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(event_router,   prefix="/api")
app.include_router(gallery_router, prefix="/api")
app.include_router(upload_router,  prefix="/upload")
app.include_router(auth_router,    prefix="/auth")
app.include_router(page_router)

@app.get("/")
async def home(request: Request):
    from app.api.v1.page import get_logged_in_user
    user = get_logged_in_user(request)
    return templates.TemplateResponse("home.html", {"request": request, "user": user})

# you can now remove the add_global_context middleware if you want
