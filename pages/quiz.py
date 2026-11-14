import streamlit as st

from backend.quiz import generate_quiz
from backend.session import require_login, run_ai
from backend.stats import add_quiz

st.set_page_config(page_title="Quiz Generator", page_icon="📝", layout="wide")
user = require_login()

st.title("📝 AI Quiz Generator")
st.write("Generate a quiz from your uploaded study material. Each click gives new questions.")

count = st.selectbox("Number of questions", [3, 5, 10], index=1)

if st.button("🎯 Generate Quiz"):
    quiz = run_ai("Generating quiz...", generate_quiz, user, count)
    if quiz:
        st.session_state.quiz = quiz
        st.session_state.quiz_id = st.session_state.get("quiz_id", 0) + 1   # resets the radio buttons
        st.session_state.pop("quiz_result", None)

quiz = st.session_state.get("quiz")
quiz_id = st.session_state.get("quiz_id", 0)

if quiz and not st.session_state.get("quiz_result"):
    with st.form("quiz_form"):
        answers = []
        for i, q in enumerate(quiz):
            st.subheader(f"Q{i + 1}. {q['question']}")
            answers.append(st.radio("Choose one", q["options"], index=None, key=f"quiz_{quiz_id}_{i}"))
        submitted = st.form_submit_button("📤 Submit Quiz")

    if submitted:
        if any(a is None for a in answers):
            st.warning("Please answer every question before submitting.")
        else:
            score = sum(1 for q, a in zip(quiz, answers) if a == q["options"][q["answer"]])
            percentage = round(score / len(quiz) * 100)
            add_quiz(percentage, user)                      # recorded once per submit
            st.session_state.quiz_result = {"answers": answers, "score": score, "percentage": percentage}
            st.rerun()

result = st.session_state.get("quiz_result")
if quiz and result:
    st.header("📊 Quiz Result")
    wrong = 0
    for i, (q, a) in enumerate(zip(quiz, result["answers"])):
        correct = q["options"][q["answer"]]
        st.subheader(f"Q{i + 1}. {q['question']}")
        st.write(f"📝 Your answer: **{a}**")
        if a == correct:
            st.success("✅ Correct")
        else:
            wrong += 1
            st.error("❌ Incorrect")
            st.success(f"Correct answer: **{correct}**")
        if q.get("explanation"):
            st.info(q["explanation"])
        if q.get("page"):
            st.caption(f"📄 Source: page/section {q['page']}")
        st.divider()

    st.success(f"🎉 Final score: {result['score']}/{len(quiz)} ({result['percentage']}%)")
    st.progress(result["percentage"] / 100)
    if result["percentage"] >= 50:
        st.success("🎓 PASS")
    else:
        st.error("❌ FAIL - review the explanations above and try again.")
    if wrong == 0:
        st.balloons()
    if st.button("🔁 Retake this quiz"):
        st.session_state.quiz_id = quiz_id + 1
        st.session_state.pop("quiz_result", None)
        st.rerun()
