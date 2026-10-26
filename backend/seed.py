# Insert the 30 fixed words on first startup. Skips the work if already seeded.

from sqlalchemy.orm import Session

from .models import Word

# The 30 words the app offers (fixed list - users pick from these only).
WORDS = [
    "moon", "key", "forest", "robot", "mirror",
    "candle", "storm", "cat", "door", "shadow",
    "banana", "castle", "whisper", "clock", "umbrella",
    "ghost", "pizza", "bridge", "dragon", "radio",
    "tunnel", "spoon", "thunder", "doll", "balloon",
    "lantern", "wizard", "attic", "sock", "river",
]


def seed_words(db: Session) -> None:
    """Add the 30 words if the words table is empty; do nothing otherwise."""
    if db.query(Word).count() > 0:
        return  # Already seeded.
    for w in WORDS:
        db.add(Word(word=w))
    db.commit()
