import hashlib

import streamlit as st
from streamlit_mic_recorder import mic_recorder

from backend.evaluate_assignment import evaluate_assignment
from backend.session import require_login, run_ai
from backend.stats import add_voice_assignment
from backend.voice_assignment import speech_to_text

st.set_page_config(page_title="Voice Assignment", page_icon="🎤", layout="wide")
user = require_login()

st.title("🎤 AI Voice Assignment")
st.write("Record your answer, review the transcript, then let EcoEdith evaluate it.")

question = st.text_input("Assignment question", placeholder="Example: Explain Inheritance in Java.")

st.subheader("🎙️ Record your answer")
audio = mic_recorder(start_prompt="🎤 Start Recording", stop_prompt="⏹ Stop Recording",
                     just_once=True, format="wav", key="assignment_recorder")

if audio and audio.get("bytes"):
    digest = hashlib.md5(audio["bytes"]).hexdigest()
    if st.session_state.get("assignment_audio") != digest:
        text = run_ai("🎧 Converting speech to text...", speech_to_text, audio["bytes"])
        if text:
            st.session_state["assignment_audio"] = digest
            st.session_state["assignment_transcript"] = text   # set BEFORE the widget is created
            st.session_state.pop("assignment_eval", None)

# The transcript persists in session state, so typing the question afterwards no longer loses it.
transcript = st.text_area("📝 Your answer (you can fix transcription mistakes)",
                          key="assignment_transcript", height=160)

if st.button("🤖 Evaluate my answer"):
    if not question.strip():
        st.warning("⚠ Please enter the assignment question.")
    elif not transcript.strip():
        st.warning("⚠ Please record an answer first.")
    else:
        result = run_ai("🤖 Evaluating...", evaluate_assignment, question.strip(), transcript.strip())
        if result:
            score, evaluation = result
            if score is not None:
                add_voice_assignment(score, user)
            st.session_state["assignment_eval"] = (score, evaluation)

evaluation = st.session_state.get("assignment_eval")
if evaluation:
    score, text = evaluation
    st.subheader("📊 AI Evaluation")
    if score is None:
        st.warning("Could not read a score from the evaluation, so it was not added to your stats.")
    else:
        st.metric("Score", f"{score:g}/10")
    st.markdown(text)
