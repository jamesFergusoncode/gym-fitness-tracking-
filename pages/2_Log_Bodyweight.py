"""
Log Bodyweight - one number every morning. Saving the same date twice just
replaces the earlier entry.
"""

from datetime import date

import pandas as pd
import streamlit as st

import analysis
import plan
import storage

st.set_page_config(page_title="Log Bodyweight", page_icon="⚖️")
st.title("⚖️ Log Bodyweight")
st.caption("Weigh in every morning and let the 7-day average do the talking.")

bodyweight = storage.load("bodyweight")

# Pre-fill with the last weight so you only have to nudge it up or down.
last_weight = float(bodyweight["weight_kg"].iloc[-1]) if not bodyweight.empty else plan.START_WEIGHT_KG

with st.form("bodyweight_form"):
    log_date = st.date_input("Date", value=date.today())
    weight = st.number_input("Weight (kg)", min_value=40.0, max_value=200.0,
                             value=last_weight, step=0.1, format="%.1f")
    sleep_h = st.number_input("Sleep last night (hours)", min_value=0.0, max_value=14.0, value=7.5, step=0.5)
    macros = st.radio("Macros yesterday (3,700 kcal, 195 g protein)", ["hit", "mostly", "no"],
                      horizontal=True, format_func=lambda v: {"hit": "Hit", "mostly": "Mostly", "no": "Missed"}[v])
    notes = st.text_input("Notes (optional)", placeholder="e.g. after a big dinner")
    submitted = st.form_submit_button("Save weigh-in", type="primary")

if submitted:
    # Drop any existing entry for this date, then add the new one.
    keep = bodyweight[bodyweight["date"] != log_date]
    new_row = pd.DataFrame([{"date": log_date, "weight_kg": weight, "sleep_h": sleep_h,
                             "macros": macros, "notes": notes}])
    storage.save("bodyweight", pd.concat([keep, new_row], ignore_index=True))
    st.success(f"Saved {weight:.1f} kg for {log_date:%A %d %b}.")
    bodyweight = storage.load("bodyweight")

# A quick look at the last week of entries.
if not bodyweight.empty:
    table = analysis.bodyweight_table(bodyweight).tail(7)
    st.subheader("Last 7 entries")
    show = table[["date", "weight_kg", "avg_7d", "target", "sleep_h", "macros", "notes"]].rename(columns={
        "date": "Date", "weight_kg": "Weight (kg)", "avg_7d": "7-day avg (kg)",
        "target": "Target (kg)", "sleep_h": "Sleep (h)", "macros": "Macros", "notes": "Notes",
    })
    st.dataframe(show.iloc[::-1], hide_index=True, width="stretch",
                 column_config={
                     "7-day avg (kg)": st.column_config.NumberColumn(format="%.2f"),
                     "Target (kg)": st.column_config.NumberColumn(format="%.2f"),
                 })
