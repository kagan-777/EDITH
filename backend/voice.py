import io
import re

MAX_CHARS = 2500


def clean_for_speech(text):
    text = re.split(r"\n-{3,}\s*\n", text or "")[0]          # drop the "Sources" footer
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"[*_#>`|~]", "", text)                      # markdown symbols
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)       # [text](url) -> text
    text = re.sub(r"[^\w\s.,;:!?()'\"%/+=-]", " ", text)       # emoji etc.
    return re.sub(r"\s+", " ", text).strip()[:MAX_CHARS]


def text_to_speech(text):
    """Return MP3 bytes (no temp files left behind) or None for empty text."""
    speech = clean_for_speech(text)
    if not speech:
        return None
    try:
        from gtts import gTTS
    except ImportError as exc:
        raise RuntimeError("gTTS is required for audio. Install: pip install gtts") from exc
    try:
        buffer = io.BytesIO()
        gTTS(text=speech, lang="en").write_to_fp(buffer)
        return buffer.getvalue()
    except Exception as exc:
        raise RuntimeError(f"Text-to-speech failed (needs internet): {exc}") from exc
