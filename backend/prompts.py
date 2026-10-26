# Prompt templates for the comedy and horror genres, plus shared safety rules.

MAX_WORDS = 200  # The story must be at most this many words.

# Rules appended to every prompt, regardless of genre.
SAFETY_RULES = """
Safety rules (always follow):
- Keep it non-graphic: suspense and eerie atmosphere only. No gore, no graphic
  violence, and no self-harm.
- No hateful, sexual, or real-person content.
- Output only the story. no title, no labels, no extra commentary.
"""


def build_prompt(words, genre: str, shorten: bool = False, examples: list[str] = None) -> str:
    """Build the user prompt for the LLM.

    words:   list of the selected words.
    genre:   "comedy" or "horror".
    shorten: True when re-asking for a shorter version after the first reply
             was over the word limit.
    examples: optional list of previously saved stories (retrieved from the
              database). When provided, they are included in the prompt as
              style examples for the model to follow. When empty/None, the
              prompt is exactly the same as before (no behavior change).
    """
    words_text = ", ".join(words)

    if genre == "comedy":
        tone = "Write a light, silly, and funny story."
    else:
        tone = "Write a spooky and suspenseful story."

    prompt = f"""{tone}

Requirements:
- Write exactly one story of at most {MAX_WORDS} words, with a clear
  beginning, middle, and end.
- Use EVERY one of the following words in the story: {words_text}.
"""

    # If we have previously saved stories, show them as style examples.
    if examples:
        prompt += "\nPreviously written stories (examples of the style to follow):\n"
        for i, ex in enumerate(examples, start=1):
            prompt += f"Example {i}:\n{ex}\n\n"
        prompt += "Now write the new story in the same style.\n"

    prompt += SAFETY_RULES

    if shorten:
        prompt += (
            f"\n\nIMPORTANT: Your previous answer was too long. Rewrite the story "
            f"in UNDER {MAX_WORDS} words while still using every required word."
        )
    return prompt
