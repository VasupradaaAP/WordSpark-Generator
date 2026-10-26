# Streamlit UI for the Words-to-Story app.
# Run from the project root with:  streamlit run frontend/app.py

import re

import requests
import streamlit as st

# Where the FastAPI backend is running.
BACKEND = "http://localhost:8000"


def highlight_words(text: str, words) -> str:
    """Wrap each selected word in **bold** (case-insensitive, whole words only)."""
    for w in sorted(words, key=len, reverse=True):  # longest first avoids partial overlap
        pattern = r"(\b" + re.escape(w) + r"\b)"
        text = re.sub(pattern, r"**\1**", text, flags=re.IGNORECASE)
    return text


st.set_page_config(page_title="Words to Story", page_icon="📖")
st.title("Words to Story")
st.caption("Select at least 10 words, pick a genre, and generate a story.")

# --- Fetch the 30 words from the backend -----------------------------------
try:
    resp = requests.get(f"{BACKEND}/words", timeout=10)
    resp.raise_for_status()
    words = resp.json()
except Exception as e:
    st.error(f"Could not connect to the backend at {BACKEND}. Is it running? ({e})")
    st.stop()

# --- Word picker with a live counter ----------------------------------------
selected = st.multiselect(
    "Choose your words",
    options=words,
    placeholder="Pick at least 10...",
)
st.write(f"Selected: {len(selected)} / {len(words)}")

# --- Genre ------------------------------------------------------------------
genre = st.radio("Genre", options=["Comedy", "Horror"])

# --- Generate (disabled until 10+ words, with a spinner) --------------------
can_generate = len(selected) >= 10
if st.button("Generate Story", type="primary", disabled=not can_generate):
    with st.spinner("Writing your story..."):
        try:
            r = requests.post(
                f"{BACKEND}/generate",
                json={"words": selected, "genre": genre.lower()},
                timeout=120,
            )
            if r.status_code == 200:
                data = r.json()
                # Remember the result and the words it was built from.
                st.session_state["story"] = data["story"]
                st.session_state["word_count"] = data["word_count"]
                st.session_state["story_words"] = selected
            else:
                st.error(r.json().get("detail", "Something went wrong."))
        except Exception as e:
            st.error(f"Request failed: {e}")

# --- Show the latest generated story ----------------------------------------
if "story" in st.session_state:
    st.subheader("Your story")
    st.markdown(highlight_words(st.session_state["story"], st.session_state.get("story_words", [])))
    st.caption(f"Word count: {st.session_state['word_count']}")

# --- Recent stories from the database ---------------------------------------
st.subheader("Recent stories")
try:
    rs = requests.get(f"{BACKEND}/stories", timeout=10)
    rs.raise_for_status()
    stories = rs.json()
    if not stories:
        st.write("No stories yet.")
    for s in stories:
        preview = s["selected_words"]
        if len(preview) > 40:
            preview = preview[:40] + "..."
        with st.expander(f"{s['genre'].capitalize()} — {preview}"):
            st.write(s["story"])
except Exception:
    st.caption("Could not load recent stories.")
