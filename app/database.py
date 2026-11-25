
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./food_plant.db"
)

# SQLite configuration
connect_args = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args = {
        "check_same_thread": False
    }

# Create database engine
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args
)

# Create database session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create base class for SQLAlchemy models
Base = declarative_base()


# Database dependency for FastAPI
def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()
