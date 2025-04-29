from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime  # Import datetime

from .routes.upload_routes import upload_router
from .routes.auth_routes import auth_router
from .routes.event_routes import router as event_router
from .routes.page_routes import router as page_router
from .database import init_db
from app.dummy_data import insert_dummy_event_types
from app.export_events import export_events_to_pdf
from app.config import STORAGE_ROOT, FACEBOOK_URL, INSTAGRAM_URL, TIKTOK_URL, WEBSITE_NAME  # Import WEBSITE_NAME
from .routes.gallery_routes import gallery_router    # add this import

from app.template_env import templates
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    insert_dummy_event_types()
    export_events_to_pdf()
    yield

app = FastAPI(lifespan=lifespan)

# Mount uploaded media from a separate directory
app.mount("/media", StaticFiles(directory=STORAGE_ROOT), name="media")
# Mount the general static files (CSS, JS, images)
app.mount("/static", StaticFiles(directory="static"), name="static")

# include your API routers
app.include_router(event_router,   prefix="/api")
app.include_router(gallery_router, prefix="/api")  # ← register your gallery endpoints
app.include_router(upload_router,  prefix="/upload")
app.include_router(auth_router,    prefix="/auth")
app.include_router(page_router)

@app.get("/")
async def home(request: Request):
    # Import and use the same get_logged_in_user as in page_routes.py
    from app.routes.page_routes import get_logged_in_user
    user = get_logged_in_user(request)
    return templates.TemplateResponse("home.html", {"request": request, "user": user})

@app.middleware("http")
async def add_global_context(request: Request, call_next):
    response = await call_next(request)
    templates.env.globals.update({
        "FACEBOOK_URL": FACEBOOK_URL,
        "INSTAGRAM_URL": INSTAGRAM_URL,
        "TIKTOK_URL": TIKTOK_URL,
        "current_year": datetime.now().year,  # Pass the current year
        "WEBSITE_NAME": WEBSITE_NAME,  # Pass the website name
    })
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
