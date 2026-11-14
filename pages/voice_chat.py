import hashlib

import streamlit as st
from streamlit_mic_recorder import mic_recorder

from backend.rag import ask_rag
from backend.session import require_login, run_ai
from backend.stats import add_question
from backend.voice import text_to_speech
from backend.voice_assignment import speech_to_text

st.set_page_config(page_title="Voice Chat", page_icon="🎙️", layout="wide")
user = require_login()

st.title("🎙️ AI Voice Chat")
st.write("Ask by voice (or type) and listen to the answer.")

audio = mic_recorder(start_prompt="🎤 Start Recording", stop_prompt="⏹ Stop Recording",
                     just_once=True, format="wav", key="voice_recorder")

# The recording is now actually transcribed (the old page ignored it).
if audio and audio.get("bytes"):
    digest = hashlib.md5(audio["bytes"]).hexdigest()
    if st.session_state.get("voice_audio") != digest:
        text = run_ai("🎧 Converting speech to text...", speech_to_text, audio["bytes"])
        if text:
            st.session_state["voice_audio"] = digest
            st.session_state["voice_question"] = text      # set BEFORE the widget is created

question = st.text_input("Your question", key="voice_question",
                         placeholder="Record above, or type: Explain Inheritance")

if st.button("🚀 Ask AI"):
    if not question.strip():
        st.warning("Please record or type a question.")
    else:
        answer = run_ai("Thinking...", ask_rag, question.strip(), user)
        if answer:
            add_question(user)
            try:
                speech = text_to_speech(answer)
            except RuntimeError as exc:
                speech = None
                st.warning(f"Audio unavailable: {exc}")
            st.session_state["voice_answer"] = (answer, speech)

result = st.session_state.get("voice_answer")
if result:
    answer, speech = result
    st.success("✅ AI answer")
    st.markdown(answer)
    if speech:
        st.audio(speech, format="audio/mp3")
        st.download_button("📥 Download Audio", speech, "EcoEdith_Answer.mp3", "audio/mpeg")
