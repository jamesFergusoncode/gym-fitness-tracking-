"""
Settings - the one thing the plan lets you change: when Maintain starts.

The calendar says 26 Oct, but the plan says to stay in Sharpen longer if you
can't yet finish 8 intervals. Set the date you actually switch and the
schedule, run targets, squat sets and tips all follow it.
"""

from datetime import date

import streamlit as st

import plan

st.set_page_config(page_title="Settings", page_icon="⚙️")
st.title("⚙️ Settings")

settings = plan.load_settings()
calendar_start = plan.week_dates(plan.PHASES[2]["first_week"])[0]
current = plan.maintain_start()

st.subheader("Maintain phase")
st.caption(f"Calendar start: {calendar_start:%A %d %b}. "
           + (f"Currently set to {current:%A %d %b}." if settings.get("maintain_start") else "Using the calendar."))

chosen = st.date_input("Maintain starts on", value=current,
                       min_value=plan.week_dates(3)[0], max_value=plan.PLAN_END)
col1, col2 = st.columns(2)
if col1.button("Save", type="primary"):
    settings["maintain_start"] = chosen.isoformat()
    plan.save_settings(settings)
    st.success(f"Maintain starts {chosen:%A %d %b}.")
if col2.button("Back to the calendar (26 Oct)", disabled=not settings.get("maintain_start")):
    settings.pop("maintain_start", None)
    plan.save_settings(settings)
    st.success("Back to the calendar phases.")
    st.rerun()

st.markdown("**The plan's test for moving on:** finish 8 intervals without dying and recover "
            "quickly between sprints. Not there by week 5? Stay in Sharpen a bit longer.")
