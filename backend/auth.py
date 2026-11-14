"""Authentication: salted PBKDF2 hashes, validation, lockout, atomic writes."""
import hashlib
import hmac
import os
import re
import secrets
import shutil
import time
from datetime import datetime

from backend.user_db import (
    BASE_DIR, atomic_write_json, data_dir, is_valid_username,
    lock, normalize_username, read_json,
)

PBKDF2_ITERATIONS = 240_000
MIN_PASSWORD_LEN = 8
MAX_FAILED_ATTEMPTS = 5
LOCK_SECONDS = 300
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def users_file():
    return data_dir() / "users.json"


# ---------------------------------------------------------------- hashing
def hash_password(password: str, salt: bytes = None, iterations: int = PBKDF2_ITERATIONS) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    if stored.startswith("pbkdf2_sha256$"):
        try:
            _, iterations, salt_hex, hash_hex = stored.split("$")
            digest = hashlib.pbkdf2_hmac(
                "sha256", password.encode(), bytes.fromhex(salt_hex), int(iterations)
            )
            return hmac.compare_digest(digest.hex(), hash_hex)
        except ValueError:
            return False
    # Legacy unsalted SHA-256 (from the old version) - verified, then upgraded.
    legacy = hashlib.sha256(password.encode()).hexdigest()
    return hmac.compare_digest(legacy, stored)


# ------------------------------------------------------------- user store
def _migrate_legacy():
    """Import users.json / user_data/ created by the old version (project root)."""
    if "ECOEDITH_DATA_DIR" in os.environ or users_file().exists():
        return
    old_users = BASE_DIR / "users.json"
    if old_users.exists():
        data_dir().mkdir(parents=True, exist_ok=True)
        old = read_json(old_users, {})
        clean = {}
        for name, info in old.items():
            name = normalize_username(name)
            if is_valid_username(name) and isinstance(info, dict):
                clean[name] = info
        atomic_write_json(users_file(), clean)
        old_data = BASE_DIR / "user_data"
        new_data = data_dir() / "user_data"
        if old_data.exists() and not new_data.exists():
            shutil.copytree(old_data, new_data)


def load_users() -> dict:
    _migrate_legacy()
    return read_json(users_file(), {})


def save_users(users: dict):
    atomic_write_json(users_file(), users)


def user_exists(username) -> bool:
    return normalize_username(username) in load_users()


# ----------------------------------------------------------- registration
def register_user(username, password, email):
    username = normalize_username(username)
    email = (email or "").strip().lower()

    if not is_valid_username(username):
        return False, "Username must be 3-30 characters: letters, numbers or underscore only"
    if len(password or "") < MIN_PASSWORD_LEN:
        return False, f"Password must be at least {MIN_PASSWORD_LEN} characters"
    if not EMAIL_RE.match(email):
        return False, "Please enter a valid email address"

    with lock:
        users = load_users()
        if username in users:
            return False, "User already exists"
        if any(u.get("email", "").lower() == email for u in users.values()):
            return False, "That email is already registered"
        users[username] = {
            "password": hash_password(password),
            "email": email,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "failed_attempts": 0,
            "locked_until": 0,
        }
        save_users(users)
    return True, "User registered successfully"


# ------------------------------------------------------------------ login
def login_user(username, password):
    username = normalize_username(username)
    generic = "Invalid username or password"

    with lock:
        users = load_users()
        user = users.get(username)
        if user is None:
            return False, generic

        now = time.time()
        if user.get("locked_until", 0) > now:
            minutes = int((user["locked_until"] - now) // 60) + 1
            return False, f"Too many failed attempts. Try again in {minutes} minute(s)."

        if not verify_password(password or "", user["password"]):
            user["failed_attempts"] = user.get("failed_attempts", 0) + 1
            if user["failed_attempts"] >= MAX_FAILED_ATTEMPTS:
                user["locked_until"] = now + LOCK_SECONDS
                user["failed_attempts"] = 0
            save_users(users)
            return False, generic

        if not user["password"].startswith("pbkdf2_sha256$"):
            user["password"] = hash_password(password)   # upgrade legacy hash
        user["failed_attempts"] = 0
        user["locked_until"] = 0
        user["last_login"] = datetime.now().isoformat()
        save_users(users)
    return True, "Login successful"


def get_user_info(username):
    username = normalize_username(username)
    user = load_users().get(username)
    if user is None:
        return None
    return {
        "username": username,
        "email": user.get("email", ""),
        "created_at": user.get("created_at", ""),
        "last_login": user.get("last_login", ""),
    }


def change_password(username, old_password, new_password):
    username = normalize_username(username)
    if len(new_password or "") < MIN_PASSWORD_LEN:
        return False, f"New password must be at least {MIN_PASSWORD_LEN} characters"
    with lock:
        users = load_users()
        user = users.get(username)
        if user is None or not verify_password(old_password or "", user["password"]):
            return False, "Current password is incorrect"
        user["password"] = hash_password(new_password)
        save_users(users)
    return True, "Password changed successfully"
