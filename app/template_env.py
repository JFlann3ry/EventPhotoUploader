from starlette.templating import Jinja2Templates
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory="app/templates")

def ordinal(n):
    n = int(n)
    if 10 <= n % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f"{n}{suffix}"

def format_date(date_value):
    return date_value.strftime('%A ') + ordinal(date_value.day) + date_value.strftime(' %B %Y')

templates.env.filters['ordinal'] = ordinal
templates.env.filters['format_date'] = format_date