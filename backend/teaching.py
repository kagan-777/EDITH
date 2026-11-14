from backend.context import sources_line
from backend.history import add_history
from backend.llm import ask_llm
from backend.retriever import search

MODES = {
    "Beginner": "Explain in simple words with an easy example.",
    "Student": "Explain with enough detail for a college student.",
    "Exam Revision": "Give concise bullet points useful for exam revision.",
    "Interview Preparation": "Explain with interview-focused concepts and examples.",
    "ELI5": "Explain like you are talking to a 5-year-old child.",
}


def teach_topic(question, mode, username):
    chunks = search(username, question, k=4)
    context = "\n\n".join(f"[{c.get('unit', 'Page')} {c['page']}]\n{c['text']}" for c in chunks)

    prompt = f"""You are EcoEdith, an AI tutor.

Answer the question using ONLY the study material below. Do not use outside knowledge.
If the material does not cover it, say so.

Teaching mode: {mode}
Instruction: {MODES.get(mode, MODES['Student'])}

Question: {question}

Study material:
{context}"""

    answer = ask_llm(prompt).replace("```", "").strip()
    add_history(f"[{mode}] {question}", answer, username)
    src = sources_line(chunks)
    return f"{answer}\n\n---\n📄 **Sources:** {src}" if src else answer
