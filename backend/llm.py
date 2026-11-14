"""LLM access through OpenRouter (OpenAI-compatible API).

Errors are RAISED as LLMError - they are never returned as fake answers.
"""
import os
from functools import lru_cache
from pathlib import Path

from backend.errors import LLMError

API_KEY_ENV = "OPENROUTER_API_KEY"
DEFAULT_MODEL = "google/gemini-2.5-flash"

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:  # python-dotenv is optional
    pass


def get_model_name() -> str:
    return os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL)


@lru_cache(maxsize=1)
def _client():
    api_key = os.getenv(API_KEY_ENV)
    if not api_key:
        raise LLMError(
            f"{API_KEY_ENV} is not set. Copy .env.example to .env and add your key."
        )
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise LLMError("The 'openai' package is missing. Run: pip install openai") from exc
    return OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1", timeout=90)


def ask_llm(prompt: str, temperature: float = 0.2, max_tokens: int = 4096) -> str:
    client = _client()
    try:
        response = client.chat.completions.create(
            model=get_model_name(),
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except Exception as exc:
        raise LLMError(f"AI request failed: {exc}") from exc

    try:
        answer = response.choices[0].message.content
    except (AttributeError, IndexError, TypeError):
        answer = None
    if not answer or not answer.strip():
        raise LLMError("The AI returned an empty response. Please try again.")
    return answer.strip()
