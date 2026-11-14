import base64
import hashlib
import hmac
import logging
import mimetypes
import os
import re
import tempfile
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath

from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from psycopg import errors as pg_errors
from psycopg.types.json import Jsonb

from api.db import DatabaseNotConfigured, connection
from backend.auth import (
    EMAIL_RE,
    LOCK_SECONDS,
    MAX_FAILED_ATTEMPTS,
    MIN_PASSWORD_LEN,
    hash_password,
    is_valid_username,
    normalize_username,
    verify_password,
)
from backend.context import sources_line
from backend.errors import LLMError
from backend.llm import ask_llm
from backend.loader import SUPPORTED, load_document
from backend.splitter import split_documents
from backend.vectorstore import _bm25_search

logger = logging.getLogger(__name__)

app = FastAPI(title="EcoEdith API", version="1.0.0")

MAX_UPLOAD_BYTES = 25 * 1024 * 1024
MAX_EXTRACTED_CHARACTERS = 2_000_000
SESSION_SECONDS = 7 * 24 * 60 * 60
SESSION_COOKIE = "edith_session"
TOKEN_RE = re.compile(r"\w+", re.UNICODE)
STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "do", "for",
    "from", "how", "i", "in", "is", "it", "of", "on", "or", "that", "the",
    "this", "to", "was", "what", "when", "where", "which", "who", "why",
    "with", "you",
}
GREETINGS = {"hi", "hii", "hello", "hey", "hi there", "hello there"}


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    email: str = Field(max_length=254)
    password: str = Field(min_length=MIN_PASSWORD_LEN, max_length=128)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=30)
    password: str = Field(min_length=1, max_length=128)


class ProcessDocumentRequest(BaseModel):
    pathname: str = Field(min_length=1, max_length=950)
    filename: str = Field(min_length=1, max_length=255)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)


def _auth_secret():
    secret = os.getenv("AUTH_SECRET", "")
    if len(secret) < 32:
        raise HTTPException(
            status_code=503,
            detail="Set AUTH_SECRET to a random value of at least 32 characters.",
        )
    return secret.encode("utf-8")


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _make_session_token(username: str) -> str:
    payload = _encode(f"{username}:{int(time.time()) + SESSION_SECONDS}".encode())
    signature = hmac.new(_auth_secret(), payload.encode("ascii"), hashlib.sha256).digest()
    return f"{payload}.{_encode(signature)}"


def _username_from_token(token: str | None) -> str | None:
    if not token:
        return None
    try:
        payload, signature = token.split(".", 1)
        expected = _encode(
            hmac.new(_auth_secret(), payload.encode("ascii"), hashlib.sha256).digest()
        )
        if not hmac.compare_digest(signature, expected):
            return None
        username, expiry = _decode(payload).decode("utf-8").rsplit(":", 1)
        if int(expiry) < int(time.time()) or not is_valid_username(username):
            return None
        return username
    except (ValueError, UnicodeDecodeError):
        return None


def require_user(request: Request) -> str:
    username = _username_from_token(request.cookies.get(SESSION_COOKIE))
    if not username:
        raise HTTPException(status_code=401, detail="Please sign in again.")
    return username


def _set_session_cookie(response: JSONResponse, username: str) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        _make_session_token(username),
        max_age=SESSION_SECONDS,
        httponly=True,
        secure=bool(os.getenv("VERCEL")),
        samesite="lax",
        path="/",
    )


def _blob_client():
    from vercel.blob import sync as blob

    return blob


@app.exception_handler(DatabaseNotConfigured)
async def database_not_configured(_request: Request, exc: DatabaseNotConfigured):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/auth/register", status_code=201)
def register(body: RegisterRequest):
    _auth_secret()
    username = normalize_username(body.username)
    email = body.email.strip().lower()
    if not is_valid_username(username):
        raise HTTPException(
            status_code=422,
            detail="Username must be 3-30 characters: letters, numbers or underscore only.",
        )
    if not EMAIL_RE.match(email):
        raise HTTPException(status_code=422, detail="Enter a valid email address.")

    try:
        with connection() as conn, conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO edith_users (username, email, password_hash)
                VALUES (%s, %s, %s)
                """,
                (username, email, hash_password(body.password)),
            )
    except pg_errors.UniqueViolation as exc:
        raise HTTPException(
            status_code=409, detail="That username or email is already registered."
        ) from exc

    response = JSONResponse(
        status_code=201,
        content={"user": {"username": username, "email": email}},
    )
    _set_session_cookie(response, username)
    return response


@app.post("/api/auth/login")
def login(body: LoginRequest):
    _auth_secret()
    username = normalize_username(body.username)
    error_status = None
    error_message = None
    user = None

    with connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT username, email, password_hash, failed_attempts, locked_until
            FROM edith_users
            WHERE username = %s
            FOR UPDATE
            """,
            (username,),
        )
        user = cursor.fetchone()
        now = datetime.now(timezone.utc)

        if user is None:
            error_status = 401
            error_message = "Invalid username or password."
        elif user["locked_until"] and user["locked_until"] > now:
            error_status = 429
            minutes = int((user["locked_until"] - now).total_seconds() // 60) + 1
            error_message = f"Too many failed attempts. Try again in {minutes} minute(s)."
        elif not verify_password(body.password, user["password_hash"]):
            attempts = user["failed_attempts"] + 1
            locked_until = None
            if attempts >= MAX_FAILED_ATTEMPTS:
                locked_until = now + timedelta(seconds=LOCK_SECONDS)
                attempts = 0
            cursor.execute(
                """
                UPDATE edith_users
                SET failed_attempts = %s, locked_until = %s
                WHERE username = %s
                """,
                (attempts, locked_until, username),
            )
            error_status = 401
            error_message = "Invalid username or password."
        else:
            cursor.execute(
                """
                UPDATE edith_users
                SET failed_attempts = 0, locked_until = NULL, last_login = %s
                WHERE username = %s
                """,
                (now, username),
            )

    if error_message:
        raise HTTPException(status_code=error_status, detail=error_message)

    response = JSONResponse(
        content={"user": {"username": user["username"], "email": user["email"]}}
    )
    _set_session_cookie(response, user["username"])
    return response


@app.get("/api/me")
def me(username: str = Depends(require_user)):
    with connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            "SELECT username, email FROM edith_users WHERE username = %s",
            (username,),
        )
        user = cursor.fetchone()
    if user is None:
        raise HTTPException(status_code=401, detail="Please sign in again.")
    return {"user": user}


@app.post("/api/auth/logout")
def logout():
    response = JSONResponse(content={"ok": True})
    response.delete_cookie(
        SESSION_COOKIE,
        httponly=True,
        secure=bool(os.getenv("VERCEL")),
        samesite="lax",
        path="/",
    )
    return response


@app.get("/api/document")
def get_document(username: str = Depends(require_user)):
    with connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT name, chunk_count, character_count, uploaded_at
            FROM edith_documents WHERE username = %s
            """,
            (username,),
        )
        document = cursor.fetchone()
    if document is None:
        return {"document": None}
    document["uploaded_at"] = document["uploaded_at"].isoformat()
    return {"document": document}


@app.post("/api/document/process")
def process_document(
    body: ProcessDocumentRequest,
    username: str = Depends(require_user),
):
    prefix = f"edith/{username}/"
    if not body.pathname.startswith(prefix) or ".." in body.pathname.split("/"):
        raise HTTPException(status_code=403, detail="That uploaded file is not yours.")

    filename = body.filename.strip()
    if PurePosixPath(filename).name != filename:
        raise HTTPException(status_code=400, detail="Invalid file name.")
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED:
        raise HTTPException(status_code=400, detail="Upload a PDF, DOCX or TXT file.")

    blob = _blob_client()
    try:
        metadata = blob.head_blob(body.pathname)
        if metadata.size > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="File is larger than 25 MB.")
        stored_file = blob.get_blob(body.pathname, access="private")
    except blob.BlobError as exc:
        raise HTTPException(status_code=502, detail="Could not read the uploaded file.") from exc

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / filename
            temp_path.write_bytes(stored_file.body)
            documents = load_document(str(temp_path))
            chunks = split_documents(documents)
    except ValueError as exc:
        try:
            blob.delete_blob(body.pathname)
        except blob.BlobError:
            logger.exception("Could not remove a rejected private upload.")
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    records = [
        {
            "text": chunk.page_content,
            "page": int(chunk.metadata.get("page", 0) or 0),
            "unit": chunk.metadata.get("unit", "Page"),
            "source": chunk.metadata.get("source", filename),
        }
        for chunk in chunks
    ]
    character_count = sum(len(chunk["text"]) for chunk in records)
    if not records:
        try:
            blob.delete_blob(body.pathname)
        except blob.BlobError:
            logger.exception("Could not remove an upload with no readable chunks.")
        raise HTTPException(status_code=400, detail="The file contains no readable text.")
    if character_count > MAX_EXTRACTED_CHARACTERS:
        try:
            blob.delete_blob(body.pathname)
        except blob.BlobError:
            logger.exception("Could not remove an upload that exceeds the indexing limit.")
        raise HTTPException(
            status_code=413,
            detail="The extracted document is too large to index (maximum 2 million characters).",
        )

    old_blob_path = None
    try:
        with connection() as conn, conn.cursor() as cursor:
            cursor.execute(
                "SELECT blob_path FROM edith_documents WHERE username = %s FOR UPDATE",
                (username,),
            )
            previous = cursor.fetchone()
            old_blob_path = previous["blob_path"] if previous else None
            cursor.execute(
                """
                INSERT INTO edith_documents
                    (username, name, blob_path, chunks, chunk_count, character_count)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (username) DO UPDATE SET
                    name = EXCLUDED.name,
                    blob_path = EXCLUDED.blob_path,
                    chunks = EXCLUDED.chunks,
                    chunk_count = EXCLUDED.chunk_count,
                    character_count = EXCLUDED.character_count,
                    uploaded_at = now()
                """,
                (
                    username,
                    filename,
                    body.pathname,
                    Jsonb(records),
                    len(records),
                    character_count,
                ),
            )
            cursor.execute(
                "DELETE FROM edith_chat_messages WHERE username = %s",
                (username,),
            )
    except Exception:
        try:
            blob.delete_blob(body.pathname)
        except blob.BlobError:
            logger.exception("Could not remove an upload after document processing failed.")
        raise

    if old_blob_path and old_blob_path != body.pathname:
        try:
            blob.delete_blob(old_blob_path)
        except blob.BlobError:
            logger.exception("Could not remove the user's replaced private document.")

    return {
        "document": {
            "name": filename,
            "chunk_count": len(records),
            "character_count": character_count,
        }
    }


@app.get("/api/chat/history")
def chat_history(
    limit: int = Query(default=30, ge=1, le=100),
    username: str = Depends(require_user),
):
    with connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT role, content, created_at
            FROM edith_chat_messages
            WHERE username = %s
            ORDER BY id DESC
            LIMIT %s
            """,
            (username, limit),
        )
        rows = cursor.fetchall()
    rows.reverse()
    return {
        "messages": [
            {
                "role": row["role"],
                "content": row["content"],
                "created_at": row["created_at"].isoformat(),
            }
            for row in rows
        ]
    }


@app.post("/api/chat")
def chat(body: ChatRequest, username: str = Depends(require_user)):
    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="Enter a question.")

    with connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT role, content FROM edith_chat_messages
            WHERE username = %s ORDER BY id DESC LIMIT 8
            """,
            (username,),
        )
        history = cursor.fetchall()
        history.reverse()
        cursor.execute(
            "SELECT chunks FROM edith_documents WHERE username = %s",
            (username,),
        )
        document = cursor.fetchone()

    chunks = document["chunks"] if document else []
    normalized = re.sub(r"[^\w\s]", "", question.casefold()).strip()
    if normalized in GREETINGS:
        answer = "Hi! Ask me anything, or upload a document to study it together."
        sources = ""
    else:
        matches = _bm25_search(chunks, question, 5) if chunks else []
        context = "\n\n".join(
            f"[{chunk.get('unit', 'Page')} {chunk['page']}]\n{chunk['text']}"
            for chunk in matches
        ) or "(No relevant excerpt was found in the uploaded material.)"
        conversation = "\n".join(
            f"{message['role'].capitalize()}: {message['content']}"
            for message in history
        ) or "(No earlier messages.)"
        prompt = f"""You are EcoEdith, a helpful AI tutor.

Answer clearly and accurately. Combine relevant uploaded study material with
general knowledge to explain concepts and give useful examples.
- Treat excerpts as the source for claims about the uploaded document.
- Distinguish document information from additional general knowledge.
- If excerpts do not address the question, say so briefly and answer from general knowledge.
- Never invent quotations or page references.

Uploaded study material:
{context}

Conversation so far:
{conversation}

Student's current question:
{question}"""
        try:
            answer = ask_llm(prompt)
        except LLMError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        sources = sources_line(matches)
        if sources:
            answer += f"\n\nSources: {sources}"

    with connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO edith_chat_messages (username, role, content)
            VALUES (%s, 'user', %s), (%s, 'assistant', %s)
            """,
            (username, question, username, answer),
        )

    return {"answer": answer, "sources": sources}
