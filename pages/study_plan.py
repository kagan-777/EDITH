import streamlit as st

from backend.session import require_login, run_ai
from backend.stats import add_study_plan
from backend.study_plan import generate_study_plan

st.set_page_config(page_title="Study Planner", page_icon="📅", layout="wide")
user = require_login()

st.title("📅 AI Study Planner")
st.write("Generate a study plan from your uploaded learning material.")

days = st.selectbox("Select study duration (days)", [3, 5, 7, 10, 15])

if st.button("📅 Generate Study Plan"):
    plan = run_ai("Generating study plan...", generate_study_plan, days, user)
    if plan:
        add_study_plan(user)
        st.session_state["plan_result"] = (days, plan)

result = st.session_state.get("plan_result")
if result:
    plan_days, plan = result
    st.success(f"✅ {plan_days}-day study plan ready")
    st.markdown(plan)
    st.download_button("📥 Download Study Plan", plan,
                       f"EcoEdith_{plan_days}_Day_Study_Plan.txt", "text/plain")
