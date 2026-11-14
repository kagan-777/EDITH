import streamlit as st

from backend.flashcards import generate_flashcards
from backend.session import require_login, run_ai
from backend.stats import add_flashcards

st.set_page_config(page_title="Flashcards", page_icon="📇", layout="wide")
user = require_login()

st.title("📇 AI Flashcard Generator")
st.write("Generate flashcards from your uploaded study material. Each click gives a fresh set.")

count = st.selectbox("Number of flashcards", [5, 10, 15], index=1)

if st.button("📚 Generate Flashcards"):
    cards = run_ai("Generating flashcards...", generate_flashcards, user, count)
    if cards:
        add_flashcards(user)
        st.session_state["flashcards_result"] = cards

cards = st.session_state.get("flashcards_result")
if cards:
    st.success(f"✅ {len(cards)} flashcards")
    for i, card in enumerate(cards, start=1):
        with st.expander(f"📇 {i}. {card['front']}"):
            st.markdown(f"**Answer:** {card['back']}")
            if card.get("page"):
                st.caption(f"📄 Source: page/section {card['page']}")
