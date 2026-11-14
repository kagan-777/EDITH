from backend.context import build_context
from backend.errors import LLMError
from backend.jsonutil import extract_json
from backend.llm import ask_llm


def _answer_index(answer, options):
    """Accept 0-based int, 'A'-'D' letters, '2' strings or the option text."""
    if isinstance(answer, bool):
        return None
    if isinstance(answer, int):
        return answer if 0 <= answer < len(options) else None
    if isinstance(answer, str):
        s = answer.strip()
        if s.isdigit():
            i = int(s)
            return i if 0 <= i < len(options) else None
        if len(s) == 1 and s.upper() in "ABCD":
            i = "ABCD".index(s.upper())
            return i if i < len(options) else None
        for i, opt in enumerate(options):
            if opt.strip().lower() == s.lower():
                return i
    return None


def clean_questions(raw):
    """Keep only well-formed questions (the old code crashed on bad ones)."""
    questions = []
    for q in raw if isinstance(raw, list) else []:
        if not isinstance(q, dict):
            continue
        question = str(q.get("question", "")).strip()
        options = [str(o).strip() for o in q.get("options", []) if str(o).strip()] \
            if isinstance(q.get("options"), list) else []
        if not question or len(options) < 2 or len(set(options)) != len(options):
            continue
        idx = _answer_index(q.get("answer"), options)
        if idx is None:
            continue
        page = q.get("page")
        questions.append({
            "question": question,
            "options": options,
            "answer": idx,
            "explanation": str(q.get("explanation", "")).strip(),
            "page": page if isinstance(page, int) and page > 0 else None,
        })
    return questions


def generate_quiz(username, count=5):
    context = build_context(username, max_chars=9000, randomize=True)
    prompt = f"""You are EcoEdith AI Tutor.

Using ONLY the study material below, write exactly {count} multiple-choice questions.
The material marks each part like [Page 3]; use that number for "page".

Return ONLY a JSON array, no markdown, no explanation:
[{{"question": "...", "options": ["A text", "B text", "C text", "D text"],
   "answer": 0, "explanation": "Short explanation.", "page": 3}}]

Rules: exactly 4 options; "answer" is the 0-based index (0-3) of the correct option.

Study material:
{context}"""
    try:
        questions = clean_questions(extract_json(ask_llm(prompt, temperature=0.5), list))
    except ValueError as exc:
        raise LLMError("Could not read the quiz from the AI. Please try again.") from exc
    if not questions:
        raise LLMError("The AI returned no usable questions. Please try again.")
    return questions[:count]
