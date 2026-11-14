from backend.context import build_context
from backend.llm import ask_llm


def generate_study_plan(days, username):
    context = build_context(username, max_chars=14000)
    prompt = f"""You are EcoEdith AI Tutor.

Using ONLY the study material below, create a {days}-day study plan.
- Divide the topics evenly across exactly {days} days.
- Say what to study each day, with page/section numbers where possible.
- Use the last day for revision.
- Use headings (Day 1, Day 2, ...) and bullet points.

Study material:
{context}"""
    return ask_llm(prompt)
