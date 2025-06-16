from sqlmodel import Session, select
from app.models import Pricing, EventType, User
from app.db.session import engine
import bcrypt
import os

def insert_pricing_tiers(session: Session):
    pricing_tiers = [
        {
            "tier": "Free",
            "price": 0.0,
            "event_limit": 1,
            "storage_limit_mb": 30,
            "can_download": False,
            "storage_duration": 30,
            "allow_video": False,
            "features": "1 Event, 30MB Storage, No Downloads, 30 Days Storage",
        },
        {
            "tier": "Basic",
            "price": 10.0,
            "event_limit": 1,
            "storage_limit_mb": -1,
            "can_download": True,
            "storage_duration": 180,
            "allow_video": False,
            "features": "1 Event, Unlimited Storage, Downloads Allowed, 6 Months Storage",
        },
        {
            "tier": "Pro",
            "price": 30.0,
            "event_limit": 5,
            "storage_limit_mb": -1,
            "can_download": True,
            "storage_duration": 365,
            "allow_video": False,
            "features": "5 Events, Unlimited Storage, Downloads Allowed, 12 Months Storage",
        },
        {
            "tier": "Premium",
            "price": 60.0,
            "event_limit": 5,
            "storage_limit_mb": -1,
            "can_download": True,
            "storage_duration": 365,
            "allow_video": True,
            "features": "5 Events, Unlimited Storage, Video Uploads, Downloads Allowed, 12 Months Storage",
        },
    ]

    for tier in pricing_tiers:
        exists = session.exec(select(Pricing).where(Pricing.tier == tier["tier"])).first()
        if not exists:
            session.add(Pricing(**tier))
    session.commit()

def insert_dummy_event_types(session: Session):
    event_types = ["Wedding", "Birthday", "Corporate", "Anniversary", "Graduation", "Other"]
    for event_type in event_types:
        exists = session.exec(select(EventType).where(EventType.name == event_type)).first()
        if not exists:
            session.add(EventType(name=event_type))
    session.commit()

def insert_test_users(session: Session):
    test_accounts = [
        {
            "email": os.getenv("TEST_FREE_USER_EMAIL", "free@test.com"),
            "password": os.getenv("TEST_FREE_USER_PASSWORD", "Free123!?"),
            "pricing_tier": "Free"
        },
        {
            "email": os.getenv("TEST_PRO_USER_EMAIL", "pro@test.com"),
            "password": os.getenv("TEST_PRO_USER_PASSWORD", "Pro123!?"),
            "pricing_tier": "Pro"
        },
        {
            "email": os.getenv("TEST_PREMIUM_USER_EMAIL", "premium@test.com"),
            "password": os.getenv("TEST_PREMIUM_USER_PASSWORD", "Premium123!?"),
            "pricing_tier": "Premium"
        }
    ]

    for account in test_accounts:
        exists = session.exec(select(User).where(User.email == account["email"])).first()
        if not exists:
            pricing = session.exec(select(Pricing).where(Pricing.tier == account["pricing_tier"])).first()
            if pricing:
                hashed = bcrypt.hashpw(account["password"].encode("utf8"), bcrypt.gensalt()).decode("utf8")
                test_user = User(
                    first_name="Test",
                    last_name=f"{account['pricing_tier']} User",
                    email=account["email"],
                    hashed_password=hashed,
                    verified=True,
                    pricing_id=pricing.id
                )
                session.add(test_user)
    session.commit()

def populate_dummy_data(session: Session):
    insert_pricing_tiers(session)
    insert_dummy_event_types(session)
    insert_test_users(session)
