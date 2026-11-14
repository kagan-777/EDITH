import re

from backend.context import sources_line
from backend.errors import NoDocumentError
from backend.history import add_history
from backend.llm import ask_llm
from backend.retriever import search

GREETING = "Hi! Ask me a question about your uploaded learning material."
GREETINGS = {"hi", "hii", "hello", "hey", "hi there", "hello there"}


def _is_greeting(question):
    normalized = re.sub(r"[^\w\s]", "", question.casefold()).strip()
    return normalized in GREETINGS


def ask_rag(question, username, k=5, conversation_history=None):
    chunks = []
    if _is_greeting(question):
        answer = GREETING
    else:
        try:
            chunks = search(username, question, k=k)
        except NoDocumentError:
            chunks = []

        context = "\n\n".join(
            f"[{c.get('unit', 'Page')} {c['page']}]\n{c['text']}" for c in chunks
        ) or "(No relevant excerpt was found in the uploaded material.)"
        conversation = "\n".join(
            f"{message['role'].capitalize()}: {message['content']}"
            for message in (conversation_history or [])[-8:]
            if message.get("role") in {"user", "assistant"}
        ) or "(No earlier messages.)"
        prompt = f"""You are EcoEdith, a helpful AI tutor.

Answer the student's question clearly and accurately. Combine relevant information
from the uploaded study material with your general knowledge to explain concepts,
add useful context, and give examples.
- Treat the uploaded excerpts as the source for claims about what the document says.
- Clearly distinguish document information from additional general knowledge.
- If the excerpts do not address the question, say so briefly and still answer from
  your general knowledge.
- Never invent quotations or page references.
- Use the conversation so far to understand follow-up questions.

Uploaded study material:
{context}

Conversation so far:
{conversation}

Student's current question:
{question}"""
        answer = ask_llm(prompt)

    add_history(question, answer, username)

    if chunks:
        src = sources_line(chunks)
        if src:
            answer += f"\n\n---\n📄 **Sources:** {src}"
    return answer
