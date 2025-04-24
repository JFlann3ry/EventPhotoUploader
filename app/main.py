from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from .routes.upload_routes import upload_router
from .routes.auth_routes import auth_router
from .routes.event_routes import router as event_router
from .routes.page_routes import router as page_router
from .database import init_db
from contextlib import asynccontextmanager

# Initialize FastAPI app with lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

# Mount static files for frontend assets
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure templates
templates = Jinja2Templates(directory="templates")

# Configure storage root
STORAGE_ROOT = Path("/media/devmon/Elements/EventPhotoUploader/events")

# Include routers
app.include_router(event_router, prefix="/api")
app.include_router(upload_router, prefix="/upload")
app.include_router(auth_router, prefix="/auth")
app.include_router(page_router)

@app.get("/")
async def home(request: Request):
    """
    Serve the home page.
    """
    return templates.TemplateResponse("home.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
