from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

auth_router = APIRouter()

@auth_router.get("/logout")
async def logout():
    """
    Log the user out by clearing session cookies.
    """
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("session_token")
    response.delete_cookie("session_expiry")
    return response