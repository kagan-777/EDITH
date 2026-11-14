import streamlit as st

from backend.notes import generate_notes
from backend.session import require_login, run_ai
from backend.stats import add_notes

st.set_page_config(page_title="AI Notes", page_icon="📒", layout="wide")
user = require_login()

st.title("📒 AI Study Notes")
st.write("Generate concise study notes from your uploaded learning material.")

if st.button("📝 Generate Notes"):
    notes = run_ai("Generating notes...", generate_notes, user)
    if notes:
        add_notes(user)
        st.session_state["notes_result"] = notes

notes = st.session_state.get("notes_result")     # survives the download-button rerun
if notes:
    st.success("✅ Notes ready")
    st.markdown(notes)
    st.download_button("📥 Download Notes", notes, "EcoEdith_Study_Notes.txt", "text/plain")
