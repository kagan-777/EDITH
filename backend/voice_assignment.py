import os
import tempfile

_model = None


def _load_model():
    global _model
    if _model is None:
        try:
            import whisper
        except ImportError as exc:
            raise RuntimeError(
                "openai-whisper is required for speech-to-text. "
                "Install: pip install openai-whisper (and install ffmpeg)."
            ) from exc
        _model = whisper.load_model("base")
    return _model


def speech_to_text(audio_bytes):
    """Return the transcript. RAISES on failure (the old code returned
    'Error: ...' text which then got graded as if it were an answer)."""
    if not audio_bytes:
        raise ValueError("No audio recorded.")
    path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            f.write(audio_bytes)
            path = f.name
        result = _load_model().transcribe(path, fp16=False)
        text = result.get("text", "").strip()
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Speech-to-text failed (is ffmpeg installed?): {exc}") from exc
    finally:
        if path and os.path.exists(path):
            os.remove(path)
    if not text:
        raise ValueError("Could not hear any speech. Please record again.")
    return text
