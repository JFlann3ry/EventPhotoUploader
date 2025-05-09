from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

from app.api.v1.auth import auth_router
from app.api.v1.event import event_router
from app.api.v1.gallery import gallery_router
from app.api.v1.page import page_router
from app.api.v1.upload import upload_router
from app.api.v1.event import router as event_router

from .db.session import init_db
from app.dummy_data import insert_dummy_event_types
from app.export_events import export_events_to_pdf
from app.core.config import STORAGE_ROOT, FACEBOOK_URL, INSTAGRAM_URL, TIKTOK_URL, WEBSITE_NAME, WEBSITE_DESCRIPTION

from app.template_env import templates

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

def insert_pricing_tiers():
    from app.models import Pricing
    from sqlmodel import Session, select
    from app.db.session import engine

    pricing_tiers = [
        {
            "tier": "Free",
            "price": 0.0,
            "event_limit": 1,
            "storage_limit_mb": 30,
            "can_download": False,
            "storage_duration": 30,
            "allow_video": False,
        },
        {
            "tier": "Basic",
            "price": 10.0,
            "event_limit": 1,
            "storage_limit_mb": -1,  # Use -1 for unlimited storage
            "can_download": True,
            "storage_duration": 180,
            "allow_video": False,
        },
        {
            "tier": "Pro",
            "price": 30.0,
            "event_limit": 5,
            "storage_limit_mb": -1,  # Use -1 for unlimited storage
            "can_download": True,
            "storage_duration": 365,
            "allow_video": False,
        },
        {
            "tier": "Premium",
            "price": 60.0,
            "event_limit": 5,
            "storage_limit_mb": -1,  # Use -1 for unlimited storage
            "can_download": True,
            "storage_duration": 365,
            "allow_video": True,
        },
    ]

    with Session(engine) as session:
        for tier in pricing_tiers:
            exists = session.exec(
                select(Pricing).where(Pricing.tier == tier["tier"])
            ).first()
            if not exists:
                session.add(Pricing(**tier))
        session.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    insert_dummy_event_types()
    export_events_to_pdf()
    insert_pricing_tiers()

    from app.models import User, Pricing
    from sqlmodel import Session, select
    from app.db.session import engine
    import bcrypt, os

    # Load test account details from .env
    test_accounts = [
        {
            "email": os.getenv("TEST_FREE_USER_EMAIL", "free@test.com"),
            "password": os.getenv("TEST_FREE_USER_PASSWORD", "Free123!?"),
            "pricing_tier": "Free"
        },
        {
            "email": os.getenv("TEST_PRO_USER_EMAIL", "pro@test.com"),
            "password": os.getenv("TEST_PRO_USER_PASSWORD", "Pro123!?"),
            "pricing_tier": "Pro"
        },
        {
            "email": os.getenv("TEST_PREMIUM_USER_EMAIL", "premium@test.com"),
            "password": os.getenv("TEST_PREMIUM_USER_PASSWORD", "Premium123!?"),
            "pricing_tier": "Premium"
        }
    ]

    with Session(engine) as session:
        for account in test_accounts:
            exists = session.exec(
                select(User).where(User.email == account["email"])
            ).first()
            if not exists:
                pricing = session.exec(
                    select(Pricing).where(Pricing.tier == account["pricing_tier"])
                ).first()
                if pricing:
                    hashed = bcrypt.hashpw(account["password"].encode("utf8"), bcrypt.gensalt()).decode("utf8")
                    test_user = User(
                        first_name="Test",
                        last_name=f"{account['pricing_tier']} User",
                        email=account["email"],
                        hashed_password=hashed,
                        verified=True,
                        pricing_id=pricing.id
                    )
                    session.add(test_user)
        session.commit()
    yield

app = FastAPI(lifespan=lifespan)

app.mount("/media", StaticFiles(directory=STORAGE_ROOT), name="media")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(event_router,   prefix="/api")
app.include_router(gallery_router, prefix="/api")
app.include_router(upload_router,  prefix="/upload")
app.include_router(auth_router,    prefix="/auth")
app.include_router(page_router)
# Removed duplicate registration of event_router with /auth prefix

@app.get("/")
async def home(request: Request):
    from app.api.v1.page import get_logged_in_user
    user = get_logged_in_user(request)
    return templates.TemplateResponse("home.html", {"request": request, "user": user})
