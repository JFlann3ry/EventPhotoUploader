# ─── External imports ────────────────────────────────────────────────────────
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ─── Routers ────────────────────────────────────────────────────────────────
from app.api.v1.auth import auth_router
from app.api.v1.event import router as event_router
from app.api.v1.gallery import gallery_router
from app.api.v1.page import page_router
from app.api.v1.upload import upload_router

# ─── Database ───────────────────────────────────────────────────────────────
from app.db.session import init_db
from sqlmodel import Session
from app.db.session import engine
from app.dummy_data import populate_dummy_data

# ─── Configuration ─────────────────────────────────────────────────────────
from app.core.config import (
    STORAGE_ROOT,
    FACEBOOK_URL,
    INSTAGRAM_URL,
    TIKTOK_URL,
    WEBSITE_NAME,
    WEBSITE_DESCRIPTION,
)

# ─── Templates ─────────────────────────────────────────────────────────────
from app.template_env import templates

# ─── Global template variables ──────────────────────────────────────────────
templates.env.globals.update({
    "WEBSITE_NAME":        WEBSITE_NAME,
    "WEBSITE_DESCRIPTION": WEBSITE_DESCRIPTION,
    "FACEBOOK_URL":        FACEBOOK_URL,
    "INSTAGRAM_URL":       INSTAGRAM_URL,
    "TIKTOK_URL":          TIKTOK_URL,
    "current_year":        datetime.now().year,
})

# ─── Application lifespan (startup/shutdown) ───────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    with Session(engine) as session:
        populate_dummy_data(session)
    yield

# ─── Create FastAPI app ─────────────────────────────────────────────────────
app = FastAPI(lifespan=lifespan)

# ─── Static & media mounts ─────────────────────────────────────────────────
app.mount("/media", StaticFiles(directory=STORAGE_ROOT), name="media")
app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static",
)
# serve /<storage_root> → /uploads
app.mount("/uploads",
          StaticFiles(directory=STORAGE_ROOT, html=False),
          name="uploads")

# ─── Include routers ───────────────────────────────────────────────────────
app.include_router(auth_router,    prefix="/auth")
app.include_router(event_router,   prefix="/auth")
app.include_router(gallery_router, prefix="/api")
app.include_router(upload_router,  prefix="/upload")
app.include_router(page_router)

# ─── Home page ────────────────────────────────────────────────────────────
@app.get("/")
async def home(request: Request):
    from app.api.v1.page import get_logged_in_user
    user = get_logged_in_user(request)
    return templates.TemplateResponse("home.html", {"request": request, "user": user})

