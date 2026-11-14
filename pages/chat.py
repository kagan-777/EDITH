import streamlit as st

from backend.rag import ask_rag
from backend.session import require_login, run_ai
from backend.stats import add_question
from backend.user_db import get_doc_meta

st.set_page_config(
    page_title="EcoEdith Chat",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)
user = require_login()

if "messages" not in st.session_state:
    st.session_state.messages = []
pending_question = st.session_state.pop("pending_chat_question", None)
document = get_doc_meta(user)

actions = (
    [
        ("Analyze", "Analyze the key ideas in my uploaded document and explain their connections."),
        ("Create", "Create clear study notes from my uploaded document."),
        (
            "Translate",
            "Translate the key ideas in my uploaded document. Ask me for the target language if I have not named one.",
        ),
        ("Summarize", "Summarize my uploaded document in five concise bullet points."),
    ]
    if document
    else [
        ("Analyze", "Analyze a topic I'm studying. Ask me which topic I want to explore."),
        ("Create", "Help me create a study resource. Ask what I'm learning."),
        ("Translate", "Help me translate a text. Ask me to paste it and choose a target language."),
        ("Summarize", "Help me summarize a text. Ask me to paste it or upload a file."),
    ]
)

with st.container(key="eco-assistant-stage"):
    st.markdown(
        '<p class="eco-hero-kicker">EcoEdith · AI assistant</p>'
        '<h1 class="eco-hero-title">How can I help you today?</h1>'
        '<p class="eco-hero-copy">Ask about your uploaded material or explore any topic. '
        'When a file is available, its relevant information is combined with AI knowledge.</p>',
        unsafe_allow_html=True,
    )

    with st.container(key="eco-assistant-panel", border=True):
        header, status = st.columns([3, 1], vertical_alignment="center")
        with header:
            st.markdown("#### :material/auto_awesome: EcoEdith")
        with status:
            st.badge("Ready", icon=":material/check_circle:", color="violet")

        if document:
            st.caption(
                f":material/description: {document['name']} · "
                f"{document['chunks']} sections connected"
            )
        else:
            st.caption("General AI chat · Upload a file to include your study material")

        if st.session_state.messages:
            with st.container(height=360, key="eco-chat-transcript"):
                for message in st.session_state.messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])
        else:
            st.markdown("### Start with a question")
            st.caption(
                "Your conversation stays here while you explore ideas and your study material."
            )

        question = st.chat_input(
            "Message EcoEdith...",
            key="eco-chat-question",
        ) or pending_question

        action_columns = st.columns(4, gap="small")
        for column, (label, action_prompt) in zip(action_columns, actions):
            if column.button(label, key=f"eco-chat-action-{label.lower()}", width="stretch"):
                st.session_state.pending_chat_question = action_prompt
                st.rerun()

        utility_columns = st.columns(2, gap="small")
        if not document:
            utility_columns[0].page_link(
                "pages/upload.py",
                label="Upload a document",
                icon=":material/upload_file:",
            )
        else:
            utility_columns[0].caption("Document context is included when relevant.")
        utility_columns[1].page_link(
            "pages/voice_chat.py",
            label="Try voice chat",
            icon=":material/mic:",
        )

    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            conversation_history = st.session_state.messages[:-1][-8:]
            answer = run_ai(
                "Searching your material and preparing an answer...",
                ask_rag,
                question,
                user,
                conversation_history=conversation_history,
            )
            if answer:
                st.markdown(answer)
                add_question(user)
                st.session_state.messages.append(
                    {"role": "assistant", "content": answer}
                )
                st.rerun()
