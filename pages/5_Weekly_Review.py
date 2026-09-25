"""
Weekly Review - one row per plan week: average weight, change, gym sessions,
macro days and sleep, so you can see the whole 14 weeks at once.
"""

from datetime import date

import streamlit as st

import analysis
import charts
import plan
import storage

st.set_page_config(page_title="Weekly Review", page_icon="📅", layout="wide")
st.title("📅 Weekly Review")

today = date.today()
bodyweight = storage.load("bodyweight")
gym = storage.load("gym")
review = analysis.weekly_review(bodyweight, gym)
current_week = plan.week_number(today)
adh = analysis.adherence(gym, bodyweight, today)

# ---------------------------------------------------------------------------
# Headline numbers for the plan so far
# ---------------------------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
start_avg = analysis.average_between(bodyweight, plan.PLAN_START, plan.week_dates(1)[1])
latest_avg = analysis.average_between(bodyweight, today - date.resolution * 6, today)
c1.metric("Weight change since week 1", f"{latest_avg - start_avg:+.2f} kg" if (start_avg is not None and latest_avg is not None) else "-")
c2.metric("Gym sessions", f"{adh['gym_done']} / {adh['gym_planned']}" if adh else "-",
          help="Sessions done against the training days that have happened so far")
hit, logged, rate = analysis.macro_rate(bodyweight, today - date.resolution * 27, today)
c3.metric("Macros, last 4 weeks", f"{rate:.0%}" if logged else "-", help=f"{hit} of {logged} logged days hit or mostly" if logged else None)
if current_week < 1:
    c4.metric("Current week", "Not started")
else:
    c4.metric("Current week", f"{min(current_week, plan.TOTAL_WEEKS)} / {plan.TOTAL_WEEKS}")

# ---------------------------------------------------------------------------
# The table
# ---------------------------------------------------------------------------
table = review.copy()
table["Week"] = [f"{w} ◀" if w == current_week else str(w) for w in table["Week"]]
st.dataframe(
    table, hide_index=True, width="stretch", height=548,
    column_config={
        "Avg weight (kg)": st.column_config.NumberColumn(format="%.2f"),
        "Change (kg)": st.column_config.NumberColumn(format="%+.2f"),
        "Target avg (kg)": st.column_config.NumberColumn(format="%.2f"),
        "Sleep (h)": st.column_config.NumberColumn(format="%.1f"),
    },
)
st.caption("Gym counts one session per day. Macros counts days marked hit or mostly out of days logged. Sleep is the week's average.")

# ---------------------------------------------------------------------------
# Sets per week by session type
# ---------------------------------------------------------------------------
volume = analysis.weekly_volume(gym)
if volume[["Push", "Pull", "Legs"]].to_numpy().sum() > 0:
    st.subheader("Sets per week by session")
    st.plotly_chart(charts.volume_chart(volume), width="stretch")
    st.caption("Push, pull and legs should stay roughly level week to week. A dip means missed sessions.")

# ---------------------------------------------------------------------------
# Weekly change chart
# ---------------------------------------------------------------------------
if review["Change (kg)"].notna().any():
    st.subheader("Weekly weight change vs target")
    st.plotly_chart(charts.weekly_change_chart(review), width="stretch")
else:
    st.info("The weekly change chart appears once you have weigh-ins in two different plan weeks.")
