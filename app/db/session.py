from sqlmodel import Session, create_engine
from app.core.config import DATABASE_URL
from typing import Generator

# ─── Database Engine ────────────────────────────────────────────────────────

engine = create_engine(DATABASE_URL, echo=True)

# ─── Database Initialization ───────────────────────────────────────────────

def init_db():
    """
    Initialize the database by creating all tables defined in the models.
    """
    from app.models import User  # Import models to ensure they are registered
    from sqlmodel import SQLModel  # Base class for SQLModel models
    SQLModel.metadata.create_all(engine)  # Create tables based on model metadata

# ─── Session Management ────────────────────────────────────────────────────

def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a SQLModel Session."""
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()

# ─── Legacy SessionLocal for manual use ─────────────────────────────────────
def SessionLocal() -> Session:
    """
    Backward‐compat factory so code using `with SessionLocal() as session:` still works.
    """
    return Session(engine)