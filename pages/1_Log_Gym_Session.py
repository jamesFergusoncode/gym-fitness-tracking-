"""
Log Gym Session - pick a session, fill in weight x reps for each set, save.

The table is pre-filled with what you lifted the last time you did the same
session, so most days you only need to change a few numbers.
"""

from datetime import date, timedelta

import pandas as pd
import streamlit as st

import analysis
import plan
import storage

st.set_page_config(page_title="Log Gym Session", page_icon="🏋️", layout="wide")
st.title("🏋️ Log Gym Session")

gym = storage.load("gym")

# ---------------------------------------------------------------------------
# 1. Which day and which session?
# ---------------------------------------------------------------------------
session_names = list(plan.GYM_SESSIONS.keys()) + ["Rest"]


def follow_date():
    """When the date changes, switch the session box to that day's planned session."""
    planned_session = plan.gym_for_date(st.session_state["log_date"])
    if planned_session in session_names:
        st.session_state["session"] = planned_session


def follow_session():
    """When the session changes, move the date to that session's day in the same week."""
    chosen = st.session_state["session"]
    current = st.session_state["log_date"]
    for weekday, name in plan.GYM_SCHEDULE.items():
        if name == chosen:
            st.session_state["log_date"] = current - timedelta(days=current.weekday()) + timedelta(days=weekday)
            return


# First visit: start from today and today's planned session.
if "log_date" not in st.session_state:
    st.session_state["log_date"] = date.today()
    follow_date()
if "session" not in st.session_state:
    st.session_state["session"] = session_names[0]

col1, col2 = st.columns(2)
log_date = col1.date_input("Date", key="log_date", on_change=follow_date)
session = col2.selectbox("Session", session_names, key="session", on_change=follow_session)
planned = plan.gym_for_date(log_date)

phase = plan.phase_for_date(log_date)
st.caption(f"{log_date:%A %d %b} · {phase['name']} phase · planned session: {planned}")

# ---------------------------------------------------------------------------
# Rest day: nothing to lift, but you can mark it done so the week shows complete.
# ---------------------------------------------------------------------------
if session == "Rest":
    rest_saved = not gym[(gym["session"] == "Rest") & (gym["date"] == log_date)].empty
    if rest_saved:
        st.success("Rest day logged ✅")
        if st.button("Undo rest day"):
            storage.save("gym", gym[~((gym["session"] == "Rest") & (gym["date"] == log_date))])
            st.rerun()
    else:
        st.info("No exercises today. Easy run on Sundays only.")
        if st.button("Mark rest day done", type="primary"):
            rest_row = pd.DataFrame([{"date": log_date, "session": "Rest", "exercise": "Rest day",
                                      "set_number": 0, "weight_kg": 0.0, "reps": 0}])
            storage.save("gym", pd.concat([gym, rest_row], ignore_index=True))
            st.rerun()
    st.stop()

# ---------------------------------------------------------------------------
# 2. Build the table to fill in
# ---------------------------------------------------------------------------
# Find the most recent time this session was logged (before the chosen date).
previous = gym[(gym["session"] == session) & (gym["date"] < log_date)]
last_time = previous[previous["date"] == previous["date"].max()] if not previous.empty else previous

# If this exact date + session was already saved, load it so it can be edited.
already_saved = gym[(gym["session"] == session) & (gym["date"] == log_date)]
source = already_saved if not already_saved.empty else last_time

rows = []
for exercise in plan.GYM_SESSIONS[session]:
    saved_sets = source[source["exercise"] == exercise]
    n_sets = max(plan.default_sets(exercise, phase["name"]), len(saved_sets))
    for set_number in range(1, n_sets + 1):
        match = saved_sets[saved_sets["set_number"] == set_number]
        rows.append({
            "Exercise": exercise,
            "Set": set_number,
            "Weight (kg)": float(match["weight_kg"].iloc[0]) if not match.empty else float("nan"),
            "Reps": int(match["reps"].iloc[0]) if not match.empty else float("nan"),
        })

if not already_saved.empty:
    st.info("This session is already saved for this date. Saving again will replace it.")
elif not last_time.empty:
    st.caption(f"Pre-filled from your last {session} on {last_time['date'].iloc[0]:%d %b}. "
               "Leave reps empty for any set you skip.")
else:
    st.caption("First time logging this session. Leave reps empty for any set you skip. "
               "Bodyweight moves (pull-ups): weight 0. Bike: put minutes in reps.")

edited = st.data_editor(
    pd.DataFrame(rows),
    num_rows="dynamic",              # lets you add an extra set if you did one
    hide_index=True,
    width="stretch",
    column_config={
        "Exercise": st.column_config.SelectboxColumn(options=plan.ALL_EXERCISES, required=True),
        "Set": st.column_config.NumberColumn(min_value=1, step=1, format="%d"),
        "Weight (kg)": st.column_config.NumberColumn(min_value=0, step=0.5, format="%.1f"),
        "Reps": st.column_config.NumberColumn(min_value=0, step=1, format="%d"),
    },
)

# ---------------------------------------------------------------------------
# 3. Save
# ---------------------------------------------------------------------------
if st.button("Save session", type="primary"):
    filled = edited.dropna(subset=["Reps"])
    filled = filled[filled["Reps"] > 0]
    # Keep the plan's exercise order, whatever order the table ended up in.
    order = {name: i for i, name in enumerate(plan.ALL_EXERCISES)}
    filled = filled.assign(_order=filled["Exercise"].map(order).fillna(999)).sort_values(["_order", "Set"])

    if filled.empty:
        st.warning("Nothing to save. Enter reps for at least one set.")
    else:
        new_rows = pd.DataFrame({
            "date": log_date,
            "session": session,
            "exercise": filled["Exercise"],
            "set_number": filled["Set"].fillna(0).astype(int),
            "weight_kg": filled["Weight (kg)"].fillna(0).astype(float),
            "reps": filled["Reps"].astype(int),
        })

        # Remove any earlier copy of this date + session, then add the new rows.
        keep = gym[~((gym["session"] == session) & (gym["date"] == log_date))]
        storage.save("gym", pd.concat([keep, new_rows], ignore_index=True))
        st.success(f"Saved {len(new_rows)} sets for {session} on {log_date:%d %b}.")

        # Celebrate any new bests from this session.
        top = analysis.top_sets(storage.load("gym"))
        todays_pbs = top[(top["date"] == log_date) & top["is_pb"]]
        for _, row in todays_pbs.iterrows():
            st.balloons()
            st.markdown(f"🏆 New best: **{row['exercise']}** {row['weight_kg']:.1f} kg x {row['reps']:.0f}")
