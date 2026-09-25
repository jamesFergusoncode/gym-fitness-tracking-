"""
Dashboard.py - the main Dashboard page.

Start the app from this folder with:
    streamlit run Dashboard.py

The other pages (logging forms, exercise progress, weekly review, edit data)
live in the `pages/` folder and Streamlit adds them to the sidebar for you.
"""

from datetime import date, timedelta

import pandas as pd
import streamlit as st

import analysis
import charts
import plan
import storage

st.set_page_config(page_title="Road to New Year", page_icon="🏋️", layout="wide")

# ---------------------------------------------------------------------------
# Load everything once at the top
# ---------------------------------------------------------------------------
today = date.today()
bodyweight = storage.load("bodyweight")
gym = storage.load("gym")
runs = storage.load("runs")

week = plan.week_number(today)
phase = plan.phase_for_date(today)
status = plan.plan_status(today)

# ---------------------------------------------------------------------------
# Header: where am I in the plan?
# ---------------------------------------------------------------------------
st.title("🏋️ Road to New Year: Lean Bulk Dashboard")
st.caption(
    f"{plan.PLAN_START:%d %b %Y} → {plan.PLAN_END:%d %b %Y} · {plan.TOTAL_WEEKS} weeks · "
    f"Today is {today:%A %d %B %Y}"
)

col1, col2, col3, col4 = st.columns(4)
if status == "before":
    days_to_go = (plan.PLAN_START - today).days
    col1.metric("Phase", "Not started")
    col2.metric("Week", "-")
    col3.metric("Plan starts in", f"{days_to_go} days")
    st.info(f"The plan starts on Monday {plan.PLAN_START:%d %B}. "
            "You can already log weigh-ins so the chart has a baseline.")
elif status == "after":
    col1.metric("Phase", "Finished 🎉")
    col2.metric("Week", f"{plan.TOTAL_WEEKS} / {plan.TOTAL_WEEKS}")
    col3.metric("Days to New Year", "0")
else:
    col1.metric("Phase", phase["name"])
    col2.metric("Week", f"{week} / {plan.TOTAL_WEEKS}")
    col3.metric("Days to 3 Jan", f"{(plan.PLAN_END - today).days}")
col4.metric("Runs this phase", f"{phase['runs_per_week']} per week")
if plan.load_settings().get("maintain_start"):
    st.caption(f"Maintain phase set to start {plan.maintain_start():%A %d %b} (change it on the Settings page).")

# ---------------------------------------------------------------------------
# Today's session
# ---------------------------------------------------------------------------
st.subheader("Today")
gym_col, run_col = st.columns(2)

with gym_col:
    session = plan.gym_for_date(today)
    logged_today = not gym[(gym["date"] == today) & (gym["session"] == session)].empty
    if session == "Rest":
        st.markdown("### 🛋️ Gym: Rest day" + (" ✅ logged" if logged_today else ""))
        if not logged_today and st.button("Mark rest day done"):
            rest_row = pd.DataFrame([{"date": today, "session": "Rest", "exercise": "Rest day",
                                      "set_number": 0, "weight_kg": 0.0, "reps": 0}])
            storage.save("gym", pd.concat([gym, rest_row], ignore_index=True))
            st.rerun()
    else:
        tick = " ✅ logged" if logged_today else ""
        st.markdown(f"### 🏋️ Gym: {session}{tick}")
        for exercise in plan.GYM_SESSIONS[session]:
            sets = plan.default_sets(exercise, phase["name"])
            extra = " (4 x 5-8)" if exercise == "Barbell squats" and sets == 4 else ""
            st.markdown(f"- {exercise}{extra}")

with run_col:
    run = plan.run_for_date(today)
    run_logged = not runs[runs["date"] == today].empty
    if run is None:
        st.markdown("### 🏃 Run: none today")
    else:
        run_type, prescription = run
        tick = " ✅ logged" if run_logged else ""
        st.markdown(f"### 🏃 Run: {run_type}{tick}")
        st.markdown(f"**{prescription}**")
        st.caption("Warm-up 10 min easy jog + leg swings · cool-down 10 min easy jog")

with st.expander(f"Tips for the {phase['name']} phase"):
    for tip in plan.PHASE_TIPS[phase["name"]]:
        st.markdown(f"- {tip}")
    st.markdown("**Running reminders**")
    for note in plan.RUN_NOTES:
        st.markdown(f"- {note}")

# ---------------------------------------------------------------------------
# Bodyweight
# ---------------------------------------------------------------------------
st.subheader("Bodyweight")
if bodyweight.empty:
    st.info("No weigh-ins yet. Use **Log Bodyweight** in the sidebar after your first morning weigh-in.")
else:
    table = analysis.bodyweight_table(bodyweight)
    latest = table.iloc[-1]
    target_today = plan.target_weight(today)

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Latest", f"{latest['weight_kg']:.1f} kg", help=f"Logged {latest['date']:%d %b}")
    m2.metric("7-day average", f"{latest['avg_7d']:.2f} kg")
    m3.metric("Target today", f"{target_today:.2f} kg")
    m4.metric("Avg vs target", f"{latest['avg_7d'] - target_today:+.2f} kg")
    proj = analysis.projection(bodyweight, today)
    m5.metric("On pace for 3 Jan", f"{proj[1]:.1f} kg" if proj else "-",
              help=f"{proj[0]:+.2f} kg/week lately. The plan says 89-90 kg." if proj else "Needs two weeks of data")
    m6.metric("Weigh-in streak", f"{analysis.weigh_streak(bodyweight, today)} days")

    st.plotly_chart(charts.bodyweight_chart(table), width="stretch")

# ---------------------------------------------------------------------------
# Macros (with the plan's +/- 200 kcal rule applied)
# ---------------------------------------------------------------------------
st.subheader("Macros")
calories, icon, message = analysis.calorie_suggestion(bodyweight, today)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Calories", f"{calories:,} kcal",
          delta=None if calories == plan.MACROS["Calories"] else f"{calories - plan.MACROS['Calories']:+} kcal")
c2.metric("Protein", f"{plan.MACROS['Protein']} g")
c3.metric("Fat", f"{plan.MACROS['Fat']} g")
c4.metric("Carbs", f"{plan.MACROS['Carbs']} g")
st.markdown(f"{icon} {message}")
hit, logged, rate = analysis.macro_rate(bodyweight, today - timedelta(days=27), today)
if logged:
    st.caption(f"Macro hit rate, last 4 weeks: {hit} of {logged} logged days on or near plan ({rate:.0%}). "
               "Mark it each morning on the Log Bodyweight page.")
st.caption("Easy carb wins: " + " · ".join(plan.EASY_CARB_WINS))

# ---------------------------------------------------------------------------
# This week at a glance
# ---------------------------------------------------------------------------
st.subheader("This week")
monday = today - timedelta(days=today.weekday())
st.caption(f"Mon {monday:%d %b} to Sun {monday + timedelta(days=6):%d %b}. Starts fresh every Monday.")
done_sessions = analysis.sessions_done(gym)
rows = []
for offset in range(7):
    day = monday + timedelta(days=offset)
    gym_session = plan.gym_for_date(day)
    gym_done = not done_sessions[(done_sessions["date"] == day) & (done_sessions["session"] == gym_session)].empty
    run = plan.run_for_date(day)
    run_done = not runs[runs["date"] == day].empty
    rows.append({
        "Day": f"{plan.WEEKDAY_NAMES[offset]} {day:%d %b}" + ("  ← today" if day == today else ""),
        "Gym": gym_session,
        "Gym done": "✅" if gym_done else "",
        "Run": "—" if run is None else f"{run[0]}: {run[1]}",
        "Run done": "✅" if run_done else ("—" if run is None else ""),
    })
st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

# ---------------------------------------------------------------------------
# New bests
# ---------------------------------------------------------------------------
st.subheader("New bests in the last 7 days")
pbs = analysis.recent_pbs(gym, today)
if pbs.empty:
    st.caption("None yet. New bests show up here automatically when a top set beats your previous best.")
else:
    for _, row in pbs.iterrows():
        st.markdown(f"🏆 **{row['exercise']}**: {row['weight_kg']:.1f} kg x {row['reps']:.0f} "
                    f"on {row['date']:%a %d %b}")
