from itsdangerous import TimestampSigner, BadSignature
from fastapi import HTTPException, Request
from dotenv import load_dotenv
import os
import smtplib
from email.mime.text import MIMEText
from app.config import EMAIL_FROM, EMAIL_PASSWORD

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
    
from itsdangerous import URLSafeTimedSerializer
from app.config import SECRET_KEY, BASE_URL

serializer = URLSafeTimedSerializer(SECRET_KEY)

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

def send_verification_email(email: str, token: str):
    """Send a verification email to the user."""
    verification_url = f"{BASE_URL}/auth/verify-email?token={token}"
    subject = "Verify Your Email Address"
    body = f"""
    Hi,

    Please verify your email address by clicking the link below:

    {verification_url}

    If you did not sign up for this account, please ignore this email.

    Thanks,
    Event Snap Team
    """
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = email

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASSWORD)  # Replace with your app password
        server.sendmail(EMAIL_FROM, email, msg.as_string())