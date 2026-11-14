from backend.context import build_context
from backend.llm import ask_llm


def generate_summary(username):
    context = build_context(username, max_chars=14000)
    prompt = f"""You are EcoEdith AI.

Using ONLY the study material below, write a well-structured study summary.
- Start with the title/topic if available.
- Explain the main concepts, important definitions, key points and formulas.
- Mention page/section numbers where useful.
- Use headings and bullet points. Keep it about one page.
- Do NOT invent information.

Study material:
{context}"""
    return ask_llm(prompt)
