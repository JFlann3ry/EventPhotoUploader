import smtplib
from email.mime.text import MIMEText
from app.core.config import EMAIL_FROM, EMAIL_PASSWORD, BASE_URL

def send_verification_email(email: str, token: str):
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
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.sendmail(EMAIL_FROM, email, msg.as_string())