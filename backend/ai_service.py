# LLM call + enforcement of the 200-word limit.
# Uses the OpenAI-compatible client against whichever base URL .env points at
# (OpenRouter by default, Hugging Face as a drop-in alternative).

import os
import re

from openai import OpenAI, RateLimitError

from . import prompts
from .prompts import MAX_WORDS


class LLMError(Exception):
    """Raised when the model cannot produce a usable story."""
    pass


def _make_client() -> OpenAI:
    return OpenAI(
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL"),
    )


def _call_llm(prompt: str) -> str:
    """Send one prompt to the model. Retries once, then raises a friendly LLMError."""
    client = _make_client()
    model = os.getenv("LLM_MODEL")
    last_err = None

    for _ in range(2):  # initial attempt + one retry
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
            )
            content = (resp.choices[0].message.content or "").strip()
            if not content:
                last_err = Exception("empty response")
                continue
            return content
        except RateLimitError as e:
            last_err = e
        except Exception as e:
            last_err = e

    # Every attempt failed - return a clear, friendly message.
    msg = str(last_err)
    if isinstance(last_err, RateLimitError) or "rate" in msg.lower():
        raise LLMError(
            "The free model is rate-limited right now. Please wait a moment "
            "and try again."
        )
    raise LLMError(
        "The story model is not responding. Please check your .env settings "
        f"and try again. ({msg})"
    )


def _word_count(text: str) -> int:
    """Simple whitespace word count."""
    return len(text.split())


def _trim(text: str, limit: int) -> str:
    """Keep full sentences until adding the next one would exceed the limit."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    out = []
    total = 0
    for s in sentences:
        if total + len(s.split()) > limit:
            break
        out.append(s)
        total += len(s.split())
    return " ".join(out).strip()


def create_story(words, genre: str, examples: list[str] = None) -> str:
    """Build the prompt, call the model, enforce the word limit, return the story.

    examples: optional previously saved stories (from the DB) included in the
              prompt as style examples. None/empty = prompt unchanged.
    """
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        raise LLMError("LLM_API_KEY is empty. Fill in your .env file first.")

    prompt = prompts.build_prompt(words, genre, examples=examples)
    story = _call_llm(prompt)

    # If the first story is too long, ask once for a shorter version.
    if _word_count(story) > MAX_WORDS:
        story = _call_llm(prompts.build_prompt(words, genre, shorten=True, examples=examples))

    # If it's still too long, trim at the last full sentence under the limit.
    if _word_count(story) > MAX_WORDS:
        story = _trim(story, MAX_WORDS)

    return story
