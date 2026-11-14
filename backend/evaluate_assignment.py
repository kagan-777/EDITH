import re

from backend.llm import ask_llm

_SCORE_PATTERNS = [
    r"score\W{0,8}(\d+(?:\.\d+)?)\s*(?:/|out of)\s*10",   # handles **Score:** 8/10
    r"score\W{0,8}(\d+(?:\.\d+)?)",
]


def parse_score(text):
    """Return a score 0-10, or None if it cannot be found (never a fake 0)."""
    for pattern in _SCORE_PATTERNS:
        m = re.search(pattern, text or "", re.IGNORECASE)
        if m:
            return max(0.0, min(10.0, float(m.group(1))))
    return None


def evaluate_assignment(question, answer):
    prompt = f"""You are an expert university professor.

Evaluate the student's answer.

Question:
{question}

Student answer (speech transcript):
{answer}

Return in exactly this format:

Score: X/10

Feedback:
(2-3 lines)

Correct Points:
- point 1
- point 2

Missing Points:
- point 1
- point 2

Suggestions:
- point 1
- point 2"""
    text = ask_llm(prompt)
    return parse_score(text), text
