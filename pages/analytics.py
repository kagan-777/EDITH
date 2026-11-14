import html

import streamlit as st

from backend.session import require_login
from backend.stats import get_stats

st.set_page_config(page_title="Performance Analytics", page_icon="📈", layout="wide")
user = require_login()
stats = get_stats(user)

st.title("📈 Performance Analytics")
st.write("Monitor your EcoEdith learning activity.")

activity = [
    ("Questions", max(0, int(stats["questions"]))),
    ("Quizzes", max(0, int(stats["quizzes"]))),
    ("Flashcards", max(0, int(stats["flashcards"]))),
    ("Notes", max(0, int(stats["notes"]))),
    ("Study Plans", max(0, int(stats["study_plans"]))),
    ("Voice", max(0, int(stats["voice_assignments"]))),
    ("Summaries", max(0, int(stats["summaries"]))),
]
activity_total = sum(count for _, count in activity)

if activity_total == 0:
    st.info("No activity yet. Use the tutor features and come back to see your charts.")
else:
    palette = ["#9B7BFF", "#54C8F5", "#5DD6A0", "#F28CB8", "#FFC66D", "#6BD5D0", "#B59BFF"]
    max_activity = max(count for _, count in activity)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📊 Activity Chart")
        bar_rows = "".join(
            f"""
            <div class="eco-analytics-bar-row">
                <span class="eco-analytics-label">{html.escape(feature)}</span>
                <span class="eco-analytics-track">
                    <span style="width: {count / max_activity * 100:.2f}%"></span>
                </span>
                <strong>{count}</strong>
            </div>
            """
            for feature, count in activity
        )
        st.html(
            f"""
            <style>
                .eco-analytics-bars {{
                    display: grid;
                    gap: 0.9rem;
                    padding: 1.1rem;
                    border: 1px solid var(--eco-glass-border);
                    border-radius: 16px;
                    background: var(--eco-glass);
                }}
                .eco-analytics-bar-row {{
                    align-items: center;
                    display: grid;
                    gap: 0.65rem;
                    grid-template-columns: minmax(5.5rem, 0.8fr) minmax(3rem, 1.5fr) 2rem;
                }}
                .eco-analytics-label {{
                    color: #E8E1F1;
                    font-size: 0.84rem;
                }}
                .eco-analytics-track {{
                    background: rgba(255, 255, 255, 0.08);
                    border-radius: 999px;
                    height: 0.6rem;
                    overflow: hidden;
                }}
                .eco-analytics-track span {{
                    background: linear-gradient(90deg, var(--eco-accent-deep), var(--eco-accent));
                    border-radius: inherit;
                    box-shadow: 0 0 12px var(--eco-glow);
                    display: block;
                    height: 100%;
                }}
                .eco-analytics-bar-row strong {{
                    color: #F7F1FF;
                    font-size: 0.85rem;
                    text-align: right;
                }}
            </style>
            <div class="eco-analytics-bars" role="img" aria-label="Learning activity bar chart">
                {bar_rows}
            </div>
            """
        )

    with col2:
        st.subheader("🥧 Activity Distribution")
        segments = []
        legend_rows = []
        angle = 0.0
        for (feature, count), color in zip(activity, palette):
            if count == 0:
                continue
            next_angle = angle + count / activity_total * 360
            segments.append(f"{color} {angle:.2f}deg {next_angle:.2f}deg")
            legend_rows.append(
                f'<div class="eco-analytics-legend-row"><span class="eco-analytics-legend-swatch" '
                f'style="background: {color}"></span><span>{html.escape(feature)}</span>'
                f"<strong>{count}</strong></div>"
            )
            angle = next_angle

        gradient = ", ".join(segments)
        st.html(
            f"""
            <style>
                .eco-analytics-distribution {{
                    align-items: center;
                    background: var(--eco-glass);
                    border: 1px solid var(--eco-glass-border);
                    border-radius: 16px;
                    display: flex;
                    flex-direction: column;
                    gap: 1rem;
                    padding: 1rem;
                }}
                .eco-analytics-donut {{
                    background:
                        radial-gradient(circle, var(--eco-glass-strong) 0 53%, transparent 54%),
                        conic-gradient({gradient});
                    border: 1px solid var(--eco-glass-border);
                    border-radius: 50%;
                    box-shadow: 0 0 26px var(--eco-glow);
                    height: 11rem;
                    width: 11rem;
                }}
                .eco-analytics-legend {{
                    display: grid;
                    gap: 0.55rem;
                    width: 100%;
                }}
                .eco-analytics-legend-row {{
                    align-items: center;
                    color: #E8E1F1;
                    display: grid;
                    font-size: 0.84rem;
                    gap: 0.6rem;
                    grid-template-columns: 0.65rem 1fr auto;
                }}
                .eco-analytics-legend-swatch {{
                    border-radius: 50%;
                    height: 0.6rem;
                    width: 0.6rem;
                }}
                .eco-analytics-legend-row strong {{
                    color: #F7F1FF;
                }}
            </style>
            <div class="eco-analytics-distribution" role="img" aria-label="Learning activity distribution chart">
                <div class="eco-analytics-donut"></div>
                <div class="eco-analytics-legend">{''.join(legend_rows)}</div>
            </div>
            """
        )

st.divider()
c3, c4, c5 = st.columns(3)
c3.metric("🏆 Best Quiz Score", f"{stats['best_score']}%")
c4.metric("🎤 Best Voice Score", f"{stats['best_voice_score']:g}/10")
average = stats["voice_total_score"] / stats["voice_assignments"] if stats["voice_assignments"] else 0
c5.metric("⭐ Average Voice Score", f"{average:.1f}/10")

st.divider()
st.subheader("📋 Usage Summary")
usage_rows = "\n".join(f"| {html.escape(feature)} | {count} |" for feature, count in activity)
st.markdown(f"| Feature | Count |\n| --- | ---: |\n{usage_rows}")
