import streamlit as st

from backend.session import require_login, run_ai
from backend.stats import add_summary
from backend.summary import generate_summary

st.set_page_config(page_title="AI Summary", page_icon="📄", layout="wide")
user = require_login()

st.title("📄 AI Document Summary")
st.write("Generate a concise summary of your uploaded learning material.")

if st.button("📄 Generate Summary"):
    summary = run_ai("Generating summary...", generate_summary, user)
    if summary:
        add_summary(user)
        st.session_state["summary_result"] = summary

summary = st.session_state.get("summary_result")
if summary:
    st.success("✅ Summary ready")
    st.markdown(summary)
    st.download_button("📥 Download Summary", summary, "EcoEdith_Summary.txt", "text/plain")
