from itsdangerous import TimestampSigner, BadSignature
from fastapi import HTTPException, Request
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Retrieve the secret key from environment variables
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY is not set in the environment variables")

signer = TimestampSigner(SECRET_KEY)

def validate_token(request: Request, event_slug: str, guest_id: int):
    """
    Validate the session token.
    """
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(status_code=403, detail="Not authenticated")

    try:
        payload = signer.unsign(token, max_age=60 * 60).decode()
        token_event_slug, token_user_id = payload.split(":")
        if token_event_slug != event_slug or int(token_user_id) != guest_id:
            raise HTTPException(status_code=403, detail="Invalid session for this event.")
    except (BadSignature, ValueError):
        raise HTTPException(status_code=403, detail="Invalid session token")