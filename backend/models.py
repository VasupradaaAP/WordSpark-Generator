# SQLAlchemy table definitions for the `words` and `stories` tables.

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text

from .database import Base


def _utcnow():
    """Timezone-aware 'now' (avoids the deprecated datetime.utcnow)."""
    return datetime.now(timezone.utc)


class Word(Base):
    __tablename__ = "words"

    id = Column(Integer, primary_key=True, index=True)
    word = Column(String, unique=True, nullable=False)


class Story(Base):
    __tablename__ = "stories"

    id = Column(Integer, primary_key=True, index=True)
    genre = Column(String, nullable=False)               # "comedy" or "horror"
    selected_words = Column(Text, nullable=False)        # comma-separated words
    story = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
