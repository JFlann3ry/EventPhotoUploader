from sqlmodel import select  # Import select
from app.models.models import Pricing
from app.db.session import SessionLocal

def seed_pricing():
    pricing_tiers = [
        {"tier": "Free", "price": 0.0, "features": "Create account,1 event/month,10 photos/event,Basic gallery,Email support"},
        {"tier": "Basic", "price": 30.0, "features": "5 events/month,100 photos/event,Custom galleries,High-res downloads,Priority support,QR tracking,6-month storage"},
        {"tier": "Ultimate", "price": 60.0, "features": "Unlimited events,500 photos/event,Event analytics,Custom branding,Password-protected links,12-month storage"},
        {"tier": "Everything", "price": 99.0, "features": "Unlimited photos,Lifetime storage,Guest management,Third-party integrations,Custom domains,VIP support"}
    ]

    with SessionLocal() as session:
        for tier in pricing_tiers:
            if not session.exec(select(Pricing).where(Pricing.tier == tier["tier"])).first():
                session.add(Pricing(**tier))
        session.commit()

if __name__ == "__main__":
    seed_pricing()