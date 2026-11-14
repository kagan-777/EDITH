import streamlit as st

from backend import user_db
from backend.auth import change_password
from backend.history import clear_history
from backend.session import require_login, reset_generated_content
from backend.themes import THEME_PRESETS
from backend.vectorstore import delete_document

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")
user = require_login()

st.title("⚙️ Settings")

if "eco_theme_choice" not in st.session_state:
    st.session_state.eco_theme_choice = user_db.get_user_theme(user)


def save_theme_choice():
    user_db.save_user_theme(user, st.session_state.eco_theme_choice)


with st.container(key="eco-settings-theme-panel", border=True):
    st.subheader("Appearance")
    st.caption("Choose a premium glass palette. Your selection is saved to your account and used across the app.")
    st.selectbox(
        "Color theme",
        options=list(THEME_PRESETS),
        format_func=lambda theme_id: THEME_PRESETS[theme_id]["label"],
        key="eco_theme_choice",
        on_change=save_theme_choice,
    )
    selected_theme = THEME_PRESETS[st.session_state.eco_theme_choice]
    st.markdown(
        f"""
        <div class="eco-theme-preview">
            <div>
                <div class="eco-theme-preview__label">Live theme preview</div>
                <strong>{selected_theme["label"]}</strong>
                <p>{selected_theme["description"]}</p>
            </div>
            <div class="eco-theme-preview__swatches" aria-label="Theme colors">
                <span style="background:{selected_theme["accent"]}"></span>
                <span style="background:{selected_theme["accent_deep"]}"></span>
                <span style="background:{selected_theme["background_start"]}"></span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with st.container(key="eco-settings-account-panel", border=True):
    st.subheader("🔑 Change password")
    with st.form("password_form"):
        old = st.text_input("Current password", type="password")
        new = st.text_input("New password (min 8 characters)", type="password")
        confirm = st.text_input("Confirm new password", type="password")
        if st.form_submit_button("Change password", type="primary"):
            if new != confirm:
                st.error("New passwords don't match")
            else:
                ok, message = change_password(user, old, new)
                (st.success if ok else st.error)(message)

with st.container(key="eco-settings-data-panel", border=True):
    st.subheader("🧹 Manage my data")
    c1, c2, c3 = st.columns(3)

    if c1.button("🗑 Clear chat history"):
        clear_history(user)
        st.success("Chat history cleared.")

    if c2.button("♻️ Reset statistics"):
        user_db.reset_user_stats(user)
        st.success("Statistics reset.")

    if c3.button("📄 Delete uploaded document"):
        delete_document(user)
        reset_generated_content()
        st.success("Document and its index deleted.")
