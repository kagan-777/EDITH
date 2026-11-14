"""Streamlit session helpers: login guard, sidebar, logout."""
import streamlit as st

from backend.auth import get_user_info
from backend.ui import apply_app_styles


def current_user():
    if st.session_state.get("logged_in"):
        return st.session_state.get("username")
    return None


def logout():
    """Clear EVERYTHING (chat, quiz, results) so the next user sees nothing."""
    st.session_state.clear()
    st.rerun()


def render_sidebar(user):
    info = get_user_info(user) or {"username": user, "email": ""}
    with st.sidebar:
        st.markdown("### :material/school: EcoEdith")
        st.caption("AI learning assistant")
        st.page_link("app.py", label="Home", icon=":material/home:")

        st.caption("Learn")
        for page, label, icon in (
            ("pages/chat.py", "AI chat", "chat"),
            ("pages/upload.py", "Upload materials", "upload_file"),
            ("pages/notes.py", "Notes", "description"),
            ("pages/summary.py", "Summaries", "summarize"),
            ("pages/quiz.py", "Quiz", "quiz"),
            ("pages/flashcards.py", "Flashcards", "style"),
            ("pages/mindmap.py", "Mind map", "account_tree"),
            ("pages/study_plan.py", "Study plan", "calendar_month"),
            ("pages/teaching.py", "Teaching modes", "school"),
        ):
            st.page_link(page, label=label, icon=f":material/{icon}:")

        st.caption("Practice")
        st.page_link(
            "pages/voice_chat.py",
            label="Voice chat",
            icon=":material/mic:",
        )
        st.page_link(
            "pages/voice_assignment.py",
            label="Voice assignment",
            icon=":material/assignment:",
        )

        st.caption("Progress")
        for page, label, icon in (
            ("pages/dashboard.py", "Dashboard", "dashboard"),
            ("pages/analytics.py", "Analytics", "analytics"),
            ("pages/history.py", "Chat history", "history"),
        ):
            st.page_link(page, label=label, icon=f":material/{icon}:")

        st.page_link("pages/about.py", label="About", icon=":material/info:")
        st.page_link("pages/settings.py", label="Settings", icon=":material/settings:")
        st.divider()
        st.markdown(f"**{info['username']}**")
        if info["email"]:
            st.caption(info["email"])
        if st.button("Log out", icon=":material/logout:", key="sidebar_logout"):
            logout()


def require_login():
    """Call at the top of EVERY page. Stops the page if nobody is logged in."""
    user = current_user()
    apply_app_styles(user)
    if not user:
        st.switch_page("app.py")
        st.stop()
    render_sidebar(user)
    return user


def reset_generated_content():
    """Drop cached AI results (called when a new document is uploaded)."""
    for key in ("messages", "quiz", "quiz_id", "quiz_result", "flashcards_result",
                "notes_result", "summary_result", "plan_result", "mindmap_result",
                "teach_result", "voice_answer", "voice_audio"):
        st.session_state.pop(key, None)


def run_ai(label, fn, *args, **kwargs):
    """Run an AI task with a spinner. Shows a friendly error and returns None on failure."""
    from backend.errors import LLMError, NoDocumentError
    with st.spinner(label):
        try:
            return fn(*args, **kwargs)
        except (LLMError, NoDocumentError, ValueError, RuntimeError, ImportError) as exc:
            st.error(f"❌ {exc}")
        except Exception as exc:  # unexpected - still don't crash the page
            st.error(f"❌ Unexpected error: {exc}")
    return None
