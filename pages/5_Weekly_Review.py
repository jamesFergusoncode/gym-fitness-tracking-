"""
Weekly Review - one row per plan week: average weight, change, sessions and
runs done, so you can see the whole 14 weeks at once.
"""

from datetime import date

import streamlit as st

import analysis
import charts
import plan
import storage

st.set_page_config(page_title="Weekly Review", page_icon="📅", layout="wide")
st.title("📅 Weekly Review")

bodyweight = storage.load("bodyweight")
gym = storage.load("gym")
runs = storage.load("runs")

review = analysis.weekly_review(bodyweight, gym, runs)
current_week = plan.week_number(date.today())

# ---------------------------------------------------------------------------
# Headline numbers for the plan so far
# ---------------------------------------------------------------------------
done_sessions = analysis.sessions_done(gym)
in_plan = lambda df: df[(df["date"] >= plan.PLAN_START) & (df["date"] <= plan.PLAN_END)]

c1, c2, c3, c4 = st.columns(4)
start_avg = analysis.average_between(bodyweight, plan.PLAN_START, plan.week_dates(1)[1])
latest_avg = analysis.average_between(bodyweight, date.today() - date.resolution * 6, date.today())
if start_avg is not None and latest_avg is not None:
    c1.metric("Weight change since week 1", f"{latest_avg - start_avg:+.2f} kg")
else:
    c1.metric("Weight change since week 1", "-")
c2.metric("Gym sessions done", len(in_plan(done_sessions)))
c3.metric("Runs done", len(in_plan(runs)))
if current_week < 1:
    c4.metric("Current week", "Not started")
else:
    c4.metric("Current week", f"{min(current_week, plan.TOTAL_WEEKS)} / {plan.TOTAL_WEEKS}")

# ---------------------------------------------------------------------------
# The table
# ---------------------------------------------------------------------------
table = review.drop(columns=["_start", "_end"]).copy()
table["Week"] = [f"{w} ◀" if w == current_week else str(w) for w in table["Week"]]

st.dataframe(
    table, hide_index=True, width="stretch", height=548,
    column_config={
        "Avg weight (kg)": st.column_config.NumberColumn(format="%.2f"),
        "Change (kg)": st.column_config.NumberColumn(format="%+.2f"),
        "Target avg (kg)": st.column_config.NumberColumn(format="%.2f"),
        "Avg run feel": st.column_config.NumberColumn(format="%.1f"),
    },
)
st.caption("Gym sessions are counted once per day per session. Runs are counted against the "
           "phase's planned runs per week (5 in Build and Sharpen, 3 in Maintain).")

# ---------------------------------------------------------------------------
# Weekly change chart
# ---------------------------------------------------------------------------
if review["Change (kg)"].notna().any():
    st.subheader("Weekly weight change vs target")
    st.plotly_chart(charts.weekly_change_chart(review), width="stretch")
else:
    st.info("The weekly change chart appears once you have weigh-ins in two different plan weeks.")
