"""Per-user file storage. No Streamlit imports here, so it is easy to test."""
import json
import logging
import os
import re
import shutil
import tempfile
import threading
from datetime import datetime
from pathlib import Path

from backend.themes import DEFAULT_THEME, THEME_PRESETS

BASE_DIR = Path(__file__).resolve().parent.parent

USERNAME_RE = re.compile(r"^[a-z0-9_]{3,30}$")
MAX_HISTORY = 200
logger = logging.getLogger(__name__)

DEFAULT_STATS = {
    "questions": 0,
    "quizzes": 0,
    "flashcards": 0,
    "notes": 0,
    "study_plans": 0,
    "voice_assignments": 0,
    "summaries": 0,
    "best_score": 0,          # best quiz score as a PERCENTAGE (0-100)
    "best_voice_score": 0,    # 0-10
    "voice_total_score": 0.0,
}

# One process-wide lock protects every read-modify-write of JSON files.
lock = threading.RLock()


def data_dir() -> Path:
    """Root folder for all runtime data (users.json + user_data/)."""
    return Path(os.getenv("ECOEDITH_DATA_DIR", BASE_DIR / "data"))


# ---------------------------------------------------------------- helpers
def normalize_username(username) -> str:
    return (username or "").strip().lower()


def is_valid_username(username) -> bool:
    return bool(USERNAME_RE.fullmatch(username or ""))


def atomic_write_json(path, data):
    """Write JSON to a temp file, then atomically replace the target."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def read_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def user_dir(username) -> Path:
    """Safe per-user directory. Rejects anything that is not a valid username
    (this is what blocks path traversal such as '../../x')."""
    username = normalize_username(username)
    if not is_valid_username(username):
        raise ValueError("Invalid username.")
    root = (data_dir() / "user_data").resolve()
    path = (root / username).resolve()
    if root not in path.parents:
        raise ValueError("Invalid username.")
    path.mkdir(parents=True, exist_ok=True)
    return path


def _file(username, name) -> Path:
    return user_dir(username) / name


# ------------------------------------------------------------------ stats
def get_user_stats(username) -> dict:
    stored = read_json(_file(username, "stats.json"), {})
    stats = dict(DEFAULT_STATS)
    stats.update({k: v for k, v in stored.items() if k in DEFAULT_STATS})
    return stats


def save_user_stats(username, stats):
    atomic_write_json(_file(username, "stats.json"), stats)


def reset_user_stats(username):
    save_user_stats(username, dict(DEFAULT_STATS))


# -------------------------------------------------------------- preferences
def get_user_theme(username) -> str:
    preferences = read_json(_file(username, "preferences.json"), {})
    if not isinstance(preferences, dict):
        logger.warning("Invalid saved preferences for user %s; using the default theme.", username)
        return DEFAULT_THEME
    theme = preferences.get("theme", DEFAULT_THEME)
    if theme not in THEME_PRESETS:
        logger.warning("Unsupported saved theme for user %s; using the default.", username)
        return DEFAULT_THEME
    return theme


def save_user_theme(username, theme: str):
    if theme not in THEME_PRESETS:
        raise ValueError("Unsupported UI theme.")
    with lock:
        preferences = read_json(_file(username, "preferences.json"), {})
        if not isinstance(preferences, dict):
            logger.warning("Replacing invalid saved preferences for user %s.", username)
            preferences = {}
        preferences["theme"] = theme
        atomic_write_json(_file(username, "preferences.json"), preferences)


# ---------------------------------------------------------------- history
def get_user_history(username) -> list:
    return read_json(_file(username, "history.json"), [])


def save_user_history(username, history):
    atomic_write_json(_file(username, "history.json"), history)


def add_to_history(username, question, answer):
    with lock:
        history = get_user_history(username)
        history.insert(0, {
            "time": datetime.now().strftime("%d-%m-%Y %I:%M %p"),
            "question": question,
            "answer": answer,
        })
        save_user_history(username, history[:MAX_HISTORY])


def clear_user_history(username):
    save_user_history(username, [])


# --------------------------------------------------------- document files
def get_user_full_text(username) -> str:
    path = _file(username, "full_text.txt")
    return path.read_text(encoding="utf-8") if path.exists() else ""


def save_user_full_text(username, content):
    _file(username, "full_text.txt").write_text(content, encoding="utf-8")


def get_user_uploads_dir(username) -> Path:
    path = user_dir(username) / "uploads"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_doc_meta(username):
    return read_json(_file(username, "doc_meta.json"), None)


def save_doc_meta(username, meta: dict):
    atomic_write_json(_file(username, "doc_meta.json"), meta)


def clear_user_files(username):
    """Remove uploaded file, extracted text and metadata (NOT the vector DB;
    use backend.vectorstore.delete_document for the full cleanup)."""
    uploads = get_user_uploads_dir(username)
    shutil.rmtree(uploads, ignore_errors=True)
    for name in ("full_text.txt", "doc_meta.json"):
        p = _file(username, name)
        if p.exists():
            p.unlink()
