import streamlit as st

from backend.session import require_login, run_ai
from backend.stats import add_question
from backend.teaching import MODES, teach_topic

st.set_page_config(page_title="AI Teaching Modes", page_icon="🧑‍🏫", layout="wide")
user = require_login()

st.title("🧑‍🏫 AI Teaching Modes")
st.write("Learn the same topic in different teaching styles.")

question = st.text_input("Enter your question", placeholder="Example: Explain Inheritance")
mode = st.selectbox("Choose teaching mode", list(MODES))

if st.button("🚀 Teach Me"):
    if not question.strip():
        st.warning("⚠️ Please enter a question.")
    else:
        answer = run_ai("Teaching...", teach_topic, question.strip(), mode, user)
        if answer:
            add_question(user)
            st.session_state["teach_result"] = (mode, answer)

result = st.session_state.get("teach_result")
if result:
    st.success(f"✅ Explanation ({result[0]} mode)")
    st.markdown(result[1])
