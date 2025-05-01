from sqlmodel import Session, select
from app.models import EventType
from app.db.session import engine

DEFAULT_EVENT_TYPES = [
    "Wedding",
    "Birthday",
    "Corporate",
    "Anniversary",
    "Graduation",
    "Other"
]

def insert_dummy_event_types():
    with Session(engine) as session:
        for event_type in DEFAULT_EVENT_TYPES:
            exists = session.exec(
                select(EventType).where(EventType.name == event_type)
            ).first()
            if not exists:
                session.add(EventType(name=event_type))
        session.commit()