from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
from sqlmodel import Session, select
from app.models import Event
from app.database import engine
from app.config import STORAGE_ROOT

EXPORT_FILENAME = "events_export.pdf"

def export_events_to_pdf():
    with Session(engine) as session:
        events = session.exec(select(Event)).all()
        export_path = os.path.join(STORAGE_ROOT, EXPORT_FILENAME)
        c = canvas.Canvas(export_path, pagesize=letter)
        width, height = letter
        y = height - 40
        c.setFont("Helvetica", 12)
        c.drawString(40, y, "Event List")
        y -= 30
        for e in events:
            line = f"ID: {e.id}, User: {e.user_id}, Type: {e.event_type_id}, Welcome: {e.welcome_message}"
            c.drawString(40, y, line)
            y -= 20
            if y < 40:
                c.showPage()
                y = height - 40
        c.save()