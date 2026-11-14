import streamlit as st

from backend.history import clear_history, get_history
from backend.session import require_login

st.set_page_config(page_title="Chat History", page_icon="📜", layout="wide")
user = require_login()

st.title("📜 Chat History")
st.write("Review your previous AI conversations.")
st.divider()

if st.button("🗑 Clear history"):
    clear_history(user)
    st.rerun()

history = get_history(user)
if not history:
    st.info("No chat history yet.")
else:
    for chat in history:
        with st.expander(f"🕒 {chat['time']} - {chat['question'][:70]}"):
            st.markdown("**❓ Question**")
            st.write(chat["question"])
            st.markdown("**🤖 Answer**")
            st.markdown(chat["answer"])
