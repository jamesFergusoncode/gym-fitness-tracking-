"""
Edit Data - fix typos, delete a wrong entry or add rows straight into the
tables. Each tab is one CSV file. Click Save to write your changes.
"""

import pandas as pd
import streamlit as st

import plan
import storage

st.set_page_config(page_title="Edit Data", page_icon="✏️", layout="wide")
st.title("✏️ Edit Data")
st.caption("Edit cells directly, use the + row at the bottom to add, or select rows and press Delete.")

TABLES = {
    "Bodyweight": "bodyweight",
    "Gym sets": "gym",
}

tabs = st.tabs(list(TABLES.keys()))

for tab, (label, name) in zip(tabs, TABLES.items()):
    with tab:
        df = storage.load(name)
        # The editor wants proper datetimes for its date picker.
        df["date"] = pd.to_datetime(df["date"])

        column_config = {"date": st.column_config.DateColumn("date", format="YYYY-MM-DD")}
        if name == "gym":
            column_config["session"] = st.column_config.SelectboxColumn(options=list(plan.GYM_SESSIONS) + ["Rest"])
            column_config["exercise"] = st.column_config.SelectboxColumn(options=plan.ALL_EXERCISES + ["Rest day"])
        if name == "bodyweight":
            column_config["macros"] = st.column_config.SelectboxColumn(options=["hit", "mostly", "no"])

        edited = st.data_editor(
            df, num_rows="dynamic", hide_index=True, width="stretch",
            column_config=column_config, key=f"editor_{name}",
        )

        col1, col2 = st.columns([1, 3])
        if col1.button("Save changes", type="primary", key=f"save_{name}"):
            cleaned = edited.dropna(subset=["date"])
            storage.save(name, cleaned)
            st.success(f"Saved {len(cleaned)} rows to {storage.file_path(name).name}.")

        col2.download_button(
            "Download CSV",
            data=df.to_csv(index=False, date_format="%Y-%m-%d"),
            file_name=storage.file_path(name).name,
            mime="text/csv",
            key=f"download_{name}",
        )
