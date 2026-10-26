# SQLAlchemy engine and session factory for PostgreSQL.
# DATABASE_URL must already be in the environment (main.py loads .env first).

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# The connection string, e.g. postgresql://user:password@localhost:5432/wordstory
DATABASE_URL = os.getenv("DATABASE_URL")

# One engine shared by the whole app.
engine = create_engine(DATABASE_URL)

# A factory that produces a fresh DB session per request.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class all ORM models inherit from.
Base = declarative_base()


def get_db():
    """FastAPI dependency: yield a session, and close it when done."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
