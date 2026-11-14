import streamlit as st

from backend.llm import get_model_name
from backend.session import require_login

st.set_page_config(page_title="About", page_icon="ℹ️", layout="wide")
require_login()

st.title("ℹ️ About EcoEdith")
st.write(
    "EcoEdith is an AI-powered learning platform. Upload your own study material and use "
    "retrieval-augmented generation (RAG) to chat with it, make notes, summaries, quizzes, "
    "flashcards, mind maps and study plans, and practise with voice."
)
st.markdown(
    "**Stack:** Streamlit · LangChain · ChromaDB · Sentence-Transformers · "
    f"OpenRouter (`{get_model_name()}`) · Whisper · gTTS"
)
st.caption("Answers come only from your uploaded document. Always verify important facts.")
