import streamlit as st

from backend.session import require_login
from backend.stats import get_stats

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
user = require_login()
stats = get_stats(user)

st.title("📊 EcoEdith Dashboard")
st.write("Track your learning progress.")
st.divider()

c1, c2, c3, c4 = st.columns(4)
c1.metric("💬 Questions Asked", stats["questions"])
c2.metric("📝 Quizzes Taken", stats["quizzes"])
c3.metric("🏆 Best Quiz Score", f"{stats['best_score']}%")
c4.metric("🎤 Best Voice Score", f"{stats['best_voice_score']:g}/10")

c5, c6, c7, c8, c9 = st.columns(5)
c5.metric("📇 Flashcards", stats["flashcards"])
c6.metric("📒 Notes", stats["notes"])
c7.metric("📅 Study Plans", stats["study_plans"])
c8.metric("🎤 Voice Assignments", stats["voice_assignments"])
c9.metric("📄 Summaries", stats["summaries"])

st.divider()

total = sum(stats[k] for k in ("questions", "quizzes", "flashcards", "notes",
                               "study_plans", "voice_assignments", "summaries"))
goal = 50
st.subheader("📈 Overall Learning Progress")
st.progress(min(total / goal, 1.0))
st.write(f"Completed activities: **{total}/{goal}**")
st.divider()

st.subheader("🎤 Voice Assignment Statistics")
if stats["voice_assignments"] > 0:
    average = stats["voice_total_score"] / stats["voice_assignments"]
    a, b = st.columns(2)
    a.metric("⭐ Average Voice Score", f"{average:.1f}/10")
    b.metric("🏅 Best Voice Score", f"{stats['best_voice_score']:g}/10")
else:
    st.info("No voice assignments completed yet.")
st.divider()

st.subheader("🏅 Achievements")
achievements = [
    (stats["questions"] >= 10, "💬 Curious Learner - asked 10+ questions"),
    (stats["quizzes"] >= 5, "📝 Quiz Master - completed 5 quizzes"),
    (stats["flashcards"] >= 5, "📇 Flashcard Creator - generated 5 flashcard sets"),
    (stats["notes"] >= 5, "📒 Note Expert - generated 5 note sets"),
    (stats["study_plans"] >= 5, "📅 Planner Pro - created 5 study plans"),
    (stats["voice_assignments"] >= 5, "🎤 Voice Expert - completed 5 voice assignments"),
    (stats["summaries"] >= 5, "📄 Summary Expert - generated 5 summaries"),
    (stats["best_score"] >= 100, "🏆 Perfect Quiz Score - scored 100%"),   # fixed: was '== 5', never true
    (stats["best_voice_score"] >= 10, "🎙️ Perfect Voice Score - scored 10/10"),
]
earned = [text for ok, text in achievements if ok]
for text in earned:
    st.success(text)
if not earned:
    st.info("Start using EcoEdith to unlock achievements!")

st.caption("EcoEdith AI Tutor • Student Dashboard")
