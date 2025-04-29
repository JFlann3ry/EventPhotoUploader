import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

WEBSITE_NAME = os.getenv("WEBSITE_NAME", "Event Snap")
WEBSITE_DESCRIPTION = os.getenv("WEBSITE_DESCRIPTION", "Upload your event photos easily!")
STORAGE_ROOT = "/media/devmon/Elements/EventPhotoUploader/Events"
BASE_URL = os.getenv("BASE_URL", "http://100.98.194.29:8000")  # Default to localhost if not set

#Social Meadia URLs
FACEBOOK_URL = "https://www.facebook.com/"
INSTAGRAM_URL = "https://www.instagram.com/"
TIKTOK_URL = "https://www.tiktok.com/"

#Email Configuration
EMAIL_FROM = "testingeventsnap@gmail.com"
EMAIL_PASSWORD = "auoa rdig arpx jjsj"

SECRET_KEY = os.getenv("SECRET_KEY", "This_is-More-Secure_than_nothing-i-Gu3SS!")  # Replace "default-secret-key" with a secure value