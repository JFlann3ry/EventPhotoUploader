from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/how-it-works")
async def how_it_works(request: Request):
    return templates.TemplateResponse("how_it_works.html", {"request": request})

@router.get("/pricing")
async def pricing(request: Request):
    return templates.TemplateResponse("pricing.html", {"request": request})

@router.get("/guest-login")
async def guest_login(request: Request):
    return templates.TemplateResponse("guest_login.html", {"request": request})

@router.get("/sign-up")
async def sign_up(request: Request):
    return templates.TemplateResponse("sign_up.html", {"request": request})

@router.get("/about")
async def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

@router.get("/help-center")
async def help_center(request: Request):
    return templates.TemplateResponse("help_center.html", {"request": request})