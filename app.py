from html import escape as html_escape

import streamlit as st

from backend.auth import login_user, register_user
from backend.session import current_user, render_sidebar
from backend.ui import apply_app_styles
from backend.user_db import normalize_username

st.set_page_config(page_title="EcoEdith", page_icon="🎓", layout="wide")
apply_app_styles(current_user())

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None


def show_login_page():
    with st.container(key="eco-login-stage"):
        welcome, account = st.columns([1.2, 0.9], gap="large", vertical_alignment="top")

        with welcome:
            with st.container(key="eco-login-story", border=True):
                st.markdown(
                    """
                    <div class="eco-login-brand">
                        <span class="eco-login-mark" aria-hidden="true">E</span>
                        <span><strong>EcoEdith</strong><small>AI learning studio</small></span>
                    </div>
                    <p class="eco-login-eyebrow">STUDY WITH MORE CLARITY</p>
                    <h1 class="eco-login-heading">Make every study session count.</h1>
                    <p class="eco-login-copy">Bring your materials and turn questions into
                    clear explanations, useful practice, and confident learning.</p>
                    <div class="eco-login-workspace" aria-hidden="true">
                        <div class="eco-login-workspace__glow"></div>
                        <div class="eco-login-workspace__orbit"></div>
                        <div class="eco-login-workspace__floor"></div>
                        <div class="eco-login-workspace__desk"></div>
                        <div class="eco-login-workspace__document">
                            <div class="eco-login-workspace__document-head">
                                <span></span><span></span><span></span>
                            </div>
                            <small>YOUR MATERIAL</small>
                            <strong>Ideas become<br>understanding.</strong>
                            <i></i><i></i><i></i>
                            <div class="eco-login-workspace__chart">
                                <span></span><span></span><span></span><span></span>
                            </div>
                        </div>
                        <div class="eco-login-workspace__tutor">
                            <div class="eco-login-workspace__spark">✦</div>
                            <small>AI TUTOR</small>
                            <strong>Ask. Explore. Learn.</strong>
                            <div class="eco-login-workspace__dots"><span></span><span></span><span></span></div>
                        </div>
                        <div class="eco-login-workspace__orb"></div>
                        <div class="eco-login-workspace__tag">YOUR STUDY STUDIO</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.caption(
                    "Document-aware answers · Notes and practice · Voice learning"
                )

        with account:
            with st.container(key="eco-login-panel", border=True):
                st.markdown(
                    '<p class="eco-login-eyebrow">YOUR PERSONAL LEARNING SPACE</p>',
                    unsafe_allow_html=True,
                )
                st.subheader("Welcome to EcoEdith")
                st.caption("Sign in to pick up where your learning begins.")
                sign_in_tab, register_tab = st.tabs(["Sign in", "Create account"])

                with sign_in_tab:
                    with st.form("login_form"):
                        username = st.text_input(
                            "Username",
                            placeholder="Enter your username",
                        )
                        password = st.text_input(
                            "Password",
                            type="password",
                            placeholder="Enter your password",
                        )
                        if st.form_submit_button("Sign in", type="primary"):
                            if username.strip() and password:
                                ok, message = login_user(username, password)
                                if ok:
                                    st.session_state.logged_in = True
                                    st.session_state.username = normalize_username(username)
                                    st.rerun()
                                else:
                                    st.error(message)
                            else:
                                st.warning("Please enter username and password")

                with register_tab:
                    st.caption("Create an account to save your learning progress.")
                    with st.form("register_form"):
                        new_username = st.text_input(
                            "Username",
                            placeholder="Letters, numbers, underscore",
                            key="reg_user",
                        )
                        email = st.text_input(
                            "Email",
                            placeholder="you@example.com",
                            key="reg_email",
                        )
                        new_password = st.text_input(
                            "Password",
                            type="password",
                            placeholder="At least 8 characters",
                            key="reg_pass",
                        )
                        confirm = st.text_input(
                            "Confirm password",
                            type="password",
                            key="reg_confirm",
                        )
                        if st.form_submit_button("Create account", type="primary"):
                            if not new_username.strip() or not email.strip() or not new_password:
                                st.warning("Please fill all fields")
                            elif new_password != confirm:
                                st.error("Passwords don't match")
                            else:
                                ok, message = register_user(new_username, new_password, email)
                                if ok:
                                    st.success(message + " - you can now sign in.")
                                else:
                                    st.error(message)


def show_home(user):
    render_sidebar(user)
    with st.container(key="eco-home-stage"):
        search_col, profile_col = st.columns([5, 1.2], vertical_alignment="center")
        with search_col:
            search_term = st.text_input(
                "Search learning tools",
                type="search",
                placeholder="Search learning tools...",
                icon=":material/search:",
                live=True,
                label_visibility="collapsed",
                key="home_tool_search",
            )
        with profile_col:
            first_initial = html_escape(user[:1].upper())
            escaped_user = html_escape(user)
            st.markdown(
                f"""
                <div class="eco-home-profile">
                    <span class="eco-home-avatar">{first_initial}</span>
                    <span><strong>{escaped_user}</strong><small>LEARNER</small></span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        hero_copy, hero_art = st.columns([3, 1], vertical_alignment="center")
        with hero_copy:
            st.html(
                """
                <p class="eco-home-kicker">YOUR PERSONAL AI TUTOR</p>
                <h1 class="eco-home-title">What would you like to <span>learn?</span></h1>
                <p class="eco-home-copy">Upload materials, ask questions, and explore your study tools.</p>
                """,
            )
        with hero_art:
            st.html(
                """
                <div class="eco-brain-art" aria-hidden="true">
                    <div class="eco-brain-art__orbit"></div>
                    <div class="eco-brain-art__glow"></div>
                    <div class="eco-brain-art__core">
                        <span class="eco-brain-art__emoji">🧠</span>
                    </div>
                    <i class="eco-brain-art__spark eco-brain-art__spark--one"></i>
                    <i class="eco-brain-art__spark eco-brain-art__spark--two"></i>
                </div>
                """
            )

        with st.container(key="eco-home-panel", border=True):
            panel_title, panel_note = st.columns([2, 1], vertical_alignment="center")
            panel_title.subheader("✦  Start learning")
            panel_note.caption("Smarter learning. Better you.")

            upload, chat, dashboard = st.columns(3, gap="medium")
            if upload.button(
                "Upload materials",
                icon=":material/upload_file:",
                type="primary",
                width="stretch",
            ):
                st.switch_page("pages/upload.py")
            if chat.button(
                "Ask a question",
                icon=":material/chat_bubble_outline:",
                width="stretch",
            ):
                st.switch_page("pages/chat.py")
            if dashboard.button(
                "View progress",
                icon=":material/analytics:",
                width="stretch",
            ):
                st.switch_page("pages/dashboard.py")

            st.markdown(
                """
                <div class="eco-home-benefits">
                    <span><b class="eco-benefit-symbol">▤</b> PDF · DOCX · TXT</span>
                    <span><b class="eco-benefit-symbol">✦</b> AI powered</span>
                    <span><b class="eco-benefit-symbol">◎</b> Personalized learning</span>
                    <span><b class="eco-benefit-symbol">✓</b> Private and secure</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        tools = [
            ("Notes", "📝", "Study notes.", "pages/notes.py", "#A855F7"),
            ("Mind Map", "🧠", "Connect ideas.", "pages/mindmap.py", "#14B8A6"),
            ("Quiz", "📋", "Quick quizzes.", "pages/quiz.py", "#F59E0B"),
            ("Flashcards", "🗂️", "Active recall.", "pages/flashcards.py", "#3B82F6"),
            ("Analytics", "📊", "Track progress.", "pages/analytics.py", "#EC4899"),
        ]
        query = search_term.strip().casefold()
        visible_tools = [
            tool for tool in tools
            if not query or query in f"{tool[0]} {tool[2]}".casefold()
        ]

        with st.container(key="eco-home-tools"):
            section_title, more_tools = st.columns([4, 1], vertical_alignment="center")
            section_title.markdown('<h2 class="eco-tools-heading">Explore tools</h2>', unsafe_allow_html=True)
            more_tools.page_link(
                "pages/study_plan.py",
                label="More tools",
                icon=":material/arrow_forward:",
            )

            if visible_tools:
                for column, (label, icon, description, page, color) in zip(
                    st.columns(len(visible_tools), gap="small"),
                    visible_tools,
                ):
                    with column:
                        with st.container(key=f"eco-tool-card-{label.lower().replace(' ', '-')}", border=True):
                            st.markdown(
                                f"""
                                <div class="eco-tool-icon" style="--tool-color: {color}">
                                    <span>{icon}</span>
                                </div>
                                <strong class="eco-tool-title">{label}</strong>
                                <p class="eco-tool-description">{description}</p>
                                """,
                                unsafe_allow_html=True,
                            )
                            st.page_link(
                                page,
                                label="Open",
                                icon=":material/arrow_forward:",
                            )
            else:
                st.info("No learning tools match that search. Try another keyword.")

        st.markdown(
            '<div class="eco-home-footer"><span>Keep learning. Keep growing.</span>'
            '<span>Small steps every day lead to big results.</span></div>',
            unsafe_allow_html=True,
        )


user = current_user()
if user:
    show_home(user)
else:
    show_login_page()
