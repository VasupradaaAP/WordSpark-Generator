# FastAPI app and routes for the Words-to-Story backend.
# Run from the project root with:  uvicorn backend.main:app --reload

from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from . import models, seed
from .ai_service import LLMError, create_story
from .database import SessionLocal, engine, get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup: create the tables and seed the 30 words (skips if seeded).
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed.seed_words(db)
    finally:
        db.close()
    yield


app = FastAPI(title="Words to Story API", lifespan=lifespan)


# How many saved stories to include as style examples in the prompt.
NUM_EXAMPLES = 3


def _recent_examples(db: Session, genre: str, limit: int = NUM_EXAMPLES) -> list[str]:
    """Fetch recent saved stories (same genre) to use as style examples.

    Best-effort: any error (DB hiccup, etc.) just returns [] so generation
    proceeds exactly as it did before examples existed.
    """
    try:
        rows = (
            db.query(models.Story.story)
            .filter(models.Story.genre == genre)
            .order_by(models.Story.created_at.desc(), models.Story.id.desc())
            .limit(limit)
            .all()
        )
        return [r[0] for r in rows]
    except Exception:
        return []


class GenerateRequest(BaseModel):
    words: list[str]   # the selected words (at least 10)
    genre: str         # "comedy" or "horror"


@app.get("/words")
def list_words(db: Session = Depends(get_db)):
    """Return all 30 words."""
    rows = db.query(models.Word).order_by(models.Word.id).all()
    return [w.word for w in rows]


@app.post("/generate")
def generate(req: GenerateRequest, db: Session = Depends(get_db)):
    """Validate the request, call the LLM, save the story, and return it."""
    # Genre must be comedy or horror.
    if req.genre not in ("comedy", "horror"):
        raise HTTPException(status_code=400, detail="Genre must be 'comedy' or 'horror'.")

    # Need at least 10 words.
    if len(req.words) < 10:
        raise HTTPException(status_code=400, detail="Please select at least 10 words.")

    # Every selected word must exist in the words table.
    valid = {w.word for w in db.query(models.Word).all()}
    invalid = [w for w in req.words if w not in valid]
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown word(s): {', '.join(invalid)}. Pick from the provided words.",
        )

    # Pull recent same-genre stories from the DB as style examples for the
    # model. Empty list = first story ever generated; prompt is unchanged.
    examples = _recent_examples(db, req.genre)

    # Call the model; surface a friendly error if it fails or is rate-limited.
    try:
        story = create_story(req.words, req.genre, examples=examples)
    except LLMError as e:
        raise HTTPException(status_code=502, detail=str(e))

    # Save the story to PostgreSQL.
    row = models.Story(
        genre=req.genre,
        selected_words=", ".join(req.words),
        story=story,
    )
    db.add(row)
    db.commit()

    return {"story": story, "word_count": len(story.split())}


@app.get("/stories")
def recent_stories(db: Session = Depends(get_db)):
    """Return the last 10 saved stories, newest first."""
    rows = (
        db.query(models.Story)
        .order_by(models.Story.created_at.desc(), models.Story.id.desc())
        .limit(10)
        .all()
    )
    return [
        {
            "id": r.id,
            "genre": r.genre,
            "selected_words": r.selected_words,
            "story": r.story,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
