"""
Exercise Progress - one chart per exercise showing your top set over time,
with new bests marked, plus an all-time bests table.
"""

from datetime import date

import streamlit as st

import analysis
import charts
import plan
import storage

st.set_page_config(page_title="Exercise Progress", page_icon="📈", layout="wide")
st.title("📈 Exercise Progress")

gym = storage.load("gym")
top = analysis.top_sets(gym)

if top.empty:
    st.info("No gym sessions logged yet. Log one from **Log Gym Session** and the charts appear here.")
    st.stop()

# ---------------------------------------------------------------------------
# All-time bests
# ---------------------------------------------------------------------------
st.subheader("All-time bests")
bests = analysis.all_time_bests(gym)
recent = analysis.recent_pbs(gym, date.today())
recent_exercises = set(recent["exercise"])

show = bests.rename(columns={
    "exercise": "Exercise", "date": "Date", "weight_kg": "Weight (kg)",
    "reps": "Reps", "est_1rm": "Est. 1RM (kg)",
})
# Put a trophy next to anything you beat in the last 7 days.
show["Exercise"] = ["🏆 " + e if e in recent_exercises else e for e in show["Exercise"]]
st.dataframe(show, hide_index=True, width="stretch")
st.caption("🏆 = new best set in the last 7 days. Est. 1RM uses the Epley formula: weight x (1 + reps / 30).")

# ---------------------------------------------------------------------------
# One chart per exercise
# ---------------------------------------------------------------------------
st.subheader("Top set over time")
metric_label = st.radio("Show", ["Top set weight", "Estimated 1RM"], horizontal=True)
metric = "weight_kg" if metric_label == "Top set weight" else "est_1rm"

logged_exercises = [e for e in plan.ALL_EXERCISES if e in set(top["exercise"])]
chosen = st.multiselect("Exercises", logged_exercises, default=logged_exercises)

# Two charts side by side keeps the page short.
columns = st.columns(2)
for i, exercise in enumerate(chosen):
    with columns[i % 2]:
        history = top[top["exercise"] == exercise]
        best = history.sort_values("score").iloc[-1]
        title = f"**{exercise}** · best {best['weight_kg']:.1f} kg x {best['reps']:.0f}"
        if exercise in recent_exercises:
            title += " · 🏆 new best this week"
        st.markdown(title)
        st.plotly_chart(charts.exercise_chart(top, exercise, metric), width="stretch")
