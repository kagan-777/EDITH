from backend import user_db
from backend.errors import LLMError, NoDocumentError
from backend.jsonutil import extract_json
from backend.llm import ask_llm


def sample_text(text, max_chars=12000, parts=4):
    """Take evenly spaced slices so the WHOLE document is represented,
    not just its first 12000 characters."""
    if len(text) <= max_chars:
        return text
    size = max_chars // parts
    step = (len(text) - size) // (parts - 1)
    return "\n...\n".join(text[i * step:i * step + size] for i in range(parts))


def clean_mindmap(raw):
    if not isinstance(raw, dict):
        raise ValueError("not an object")
    root = str(raw.get("root", "")).strip() or "Study Material"
    branches = []
    for b in raw.get("branches", []) if isinstance(raw.get("branches"), list) else []:
        if not isinstance(b, dict):
            continue
        title = str(b.get("title", "")).strip()
        items = [str(i).strip() for i in b.get("items", []) if str(i).strip()] \
            if isinstance(b.get("items"), list) else []
        if title:
            branches.append({"title": title, "items": items[:5]})
    if not branches:
        raise ValueError("no branches")
    return {"root": root, "branches": branches[:5]}


def generate_mindmap(username):
    text = user_db.get_user_full_text(username)      # per-user file (old code used data/full_text.txt)
    if not text.strip():
        raise NoDocumentError("No document found. Please upload your study material first.")

    prompt = f"""You are EcoEdith AI Tutor.

Read the study material below and create a hierarchical mind map.

Return ONLY valid JSON, no markdown:
{{"root": "Main Topic", "branches": [{{"title": "Branch", "items": ["Keyword1", "Keyword2"]}}]}}

Rules:
- Root = the document title or subject.
- Maximum 5 branches, maximum 5 keywords per branch, keywords 1-3 words.
- Focus only on important concepts. Ignore authors, references and page numbers.

Study material:
{sample_text(text)}"""
    try:
        return clean_mindmap(extract_json(ask_llm(prompt), dict))
    except ValueError as exc:
        raise LLMError("Could not read the mind map from the AI. Please try again.") from exc
