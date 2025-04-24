from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from .routes.event_routes import event_router
from .routes.upload_routes import upload_router
from .routes.auth_routes import auth_router

# Initialize FastAPI app
app = FastAPI()

# Mount static files for frontend assets
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure templates
templates = Jinja2Templates(directory="templates")

# Configure storage root
STORAGE_ROOT = Path("/media/devmon/Elements/EventPhotoUploader/events")

# Include routers
app.include_router(event_router, prefix="/events")
app.include_router(upload_router, prefix="/upload")
app.include_router(auth_router, prefix="/auth")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
