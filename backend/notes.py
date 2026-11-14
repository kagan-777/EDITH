from backend.context import build_context
from backend.llm import ask_llm


def generate_notes(username):
    context = build_context(username, max_chars=14000)
    prompt = f"""You are EcoEdith AI Tutor.

Using ONLY the study material below, write concise study notes.
- Use headings and bullet points.
- Include important concepts, definitions and formulas (if any).
- Mention page/section numbers where relevant.

Study material:
{context}"""
    return ask_llm(prompt)
