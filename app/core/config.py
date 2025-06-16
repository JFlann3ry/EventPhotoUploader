import os  # For environment variable handling
from dotenv import load_dotenv  # For loading environment variables from a .env file
from datetime import datetime, timedelta  # For date and time utilities

# Load environment variables from .env file
load_dotenv()

# ─── General Configuration ─────────────────────────────────────────────────

# Website settings
WEBSITE_NAME = os.getenv("WEBSITE_NAME", "Event Snap")  # Default website name
WEBSITE_DESCRIPTION = os.getenv(
    "WEBSITE_DESCRIPTION", "Upload your event photos easily!"
)  # Default website description

# Storage settings
STORAGE_ROOT = "/media/devmon/Elements/EventPhotoUploader/Events"  # Root directory for storing event files

# Database settings
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database.db")  # Database connection URL

# ─── Social Media Links ────────────────────────────────────────────────────

# URLs for social media platforms
FACEBOOK_URL = "https://www.facebook.com/"
INSTAGRAM_URL = "https://www.instagram.com/"
TIKTOK_URL = "https://www.tiktok.com/"

# ─── Email Configuration ───────────────────────────────────────────────────

# Email settings for sending notifications
EMAIL_FROM = "testingeventsnap@gmail.com"  # Sender email address
EMAIL_PASSWORD = "auoa rdig arpx jjsj"  # App-specific password for the email account

# ─── Security Configuration ────────────────────────────────────────────────

# Security settings for token generation and validation
SECRET_KEY = os.getenv(
    "SECRET_KEY", "This_is-More-Secure_than_nothing-i-Gu3SS!"
)  # Secret key for signing tokens
ALGORITHM = "HS256"  # Algorithm used for token encoding
TOKEN_EXPIRE_SECONDS = 3600  # Token expiration time in seconds (1 hour)

# ─── Application Base URL ──────────────────────────────────────────────────

# Base URL for the application
BASE_URL = "http://100.98.194.29:8000"

# ─── Test User Credentials ─────────────────────────────────────────────────

# Test user credentials for different roles
TEST_USER_EMAIL = "test1@test.com"
TEST_USER_PASSWORD = "T3qu1la!?!"

TEST_FREE_USER_EMAIL = "free@test.com"
TEST_FREE_USER_PASSWORD = "Free123!?"

TEST_PRO_USER_EMAIL = "pro@test.com"
TEST_PRO_USER_PASSWORD = "Pro123!?"

TEST_PREMIUM_USER_EMAIL = "premium@test.com"
TEST_PREMIUM_USER_PASSWORD = "Premium123!?"