from backend.context import build_context
from backend.errors import LLMError
from backend.jsonutil import extract_json
from backend.llm import ask_llm


def clean_flashcards(raw):
    cards = []
    for item in raw if isinstance(raw, list) else []:
        if not isinstance(item, dict):
            continue
        front, back = str(item.get("front", "")).strip(), str(item.get("back", "")).strip()
        if not front or not back:
            continue
        page = item.get("page")
        cards.append({"front": front, "back": back,
                      "page": page if isinstance(page, int) and page > 0 else None})
    return cards


def generate_flashcards(username, count=10):
    context = build_context(username, max_chars=9000, randomize=True)
    prompt = f"""You are EcoEdith AI Tutor.

Using ONLY the study material below, create exactly {count} flashcards.
The material marks each part like [Page 3]; use that number for "page".

Return ONLY a JSON array, no markdown, no explanation:
[{{"front": "Question", "back": "Short answer", "page": 3}}]

Study material:
{context}"""
    try:
        cards = clean_flashcards(extract_json(ask_llm(prompt, temperature=0.5), list))
    except ValueError as exc:
        raise LLMError("Could not read the flashcards from the AI. Please try again.") from exc
    if not cards:
        raise LLMError("The AI returned no usable flashcards. Please try again.")
    return cards
