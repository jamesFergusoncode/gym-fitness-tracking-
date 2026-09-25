"""
Log Run - what you ran, how long, and how it felt from 1 (awful) to 10 (great).
"""

from datetime import date

import pandas as pd
import streamlit as st

import plan
import storage

st.set_page_config(page_title="Log Run", page_icon="🏃")
st.title("🏃 Log Run")

runs = storage.load("runs")

log_date = st.date_input("Date", value=date.today())

# Show what the plan says for that day and pre-select it.
planned = plan.run_for_date(log_date)
if planned is None:
    st.caption(f"{log_date:%A %d %b}: no run planned. Log one anyway if you went out.")
    default_index = 0
else:
    st.caption(f"{log_date:%A %d %b}: planned run is **{planned[0]}** ({planned[1]}).")
    default_index = plan.RUN_TYPES.index(planned[0])

# The selectbox sits outside the form so the reps fields can react to it.
run_type = st.selectbox("Type", plan.RUN_TYPES, index=default_index)
planned_reps = plan.RUN_REPS[plan.phase_for_date(log_date)["name"]].get(run_type)
guide = plan.RUN_GUIDE[run_type]
st.info(f"**{run_type}** · {guide['what']} {guide['how']}\n\nEffort {guide['effort']}. "
        "Warm-up 10 min easy jog + leg swings, cool-down 10 min easy jog.")

with st.form("run_form"):
    duration = st.number_input("Duration (minutes, including warm-up and cool-down)",
                               min_value=1, max_value=300, value=30, step=1)
    reps_done = reps_planned = None
    if planned_reps:
        c1, c2 = st.columns(2)
        reps_done = c1.number_input("Reps completed", min_value=0, max_value=30, value=planned_reps, step=1)
        reps_planned = c2.number_input("Reps planned", min_value=1, max_value=30, value=planned_reps, step=1)
    feel = st.slider("How did it feel? (1 = terrible, 10 = amazing)", 1, 10, 7)
    notes = st.text_input("Notes (optional)", placeholder="e.g. did all 8 intervals, legs heavy")
    submitted = st.form_submit_button("Save run", type="primary")

if submitted:
    new_row = pd.DataFrame([{
        "date": log_date, "run_type": run_type, "duration_min": duration,
        "feel": feel, "reps_done": reps_done, "reps_planned": reps_planned, "notes": notes,
    }])
    storage.add_rows("runs", new_row)
    st.success(f"Saved {run_type} run, {duration} min, felt {feel}/10.")
    runs = storage.load("runs")

if not runs.empty:
    st.subheader("Recent runs")
    show = runs.tail(10).iloc[::-1].rename(columns={
        "date": "Date", "run_type": "Type", "duration_min": "Minutes",
        "feel": "Feel (1-10)", "reps_done": "Reps done", "reps_planned": "Reps planned", "notes": "Notes",
    })
    st.dataframe(show, hide_index=True, width="stretch")

    # Simple weekly summary: how many runs and the average feel.
    this_week_start = date.today() - pd.Timedelta(days=date.today().weekday())
    this_week = runs[runs["date"] >= this_week_start]
    phase = plan.phase_for_date(date.today())
    st.metric("Runs this week", f"{len(this_week)} / {phase['runs_per_week']}",
              help="Planned runs per week for the current phase")
