from itsdangerous import TimestampSigner, BadSignature, URLSafeTimedSerializer
from fastapi import HTTPException, Request
from dotenv import load_dotenv
from datetime import datetime, timedelta
import os
import jwt  # Install with `pip install PyJWT`
import bcrypt  # Ensure bcrypt is installed: pip install bcrypt
from app.core.config import SECRET_KEY, BASE_URL, EMAIL_FROM, EMAIL_PASSWORD, ALGORITHM

# Load environment variables from .env file
load_dotenv()

signer = TimestampSigner(SECRET_KEY)
serializer = URLSafeTimedSerializer(SECRET_KEY)

def create_access_token(data: dict, expires_delta: timedelta = timedelta(hours=1)) -> str:
    """
    Create a JWT access token.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt

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

def generate_verification_token(email: str) -> str:
    """Generate a secure token for email verification."""
    return serializer.dumps(email, salt="email-verification")

def verify_verification_token(token: str, max_age: int = 3600) -> str:
    """Verify the email verification token."""
    try:
        email = serializer.loads(token, salt="email-verification", max_age=max_age)
        return email
    except Exception:
        return None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    """
    return bcrypt.checkpw(plain_password.encode("utf8"), hashed_password.encode("utf8"))