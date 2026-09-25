"""
storage.py - reading and writing the CSV files.

All data is kept in plain CSV files inside the `data/` folder so you can open
them in Excel or a text editor at any time:

    data/bodyweight.csv   one row per morning weigh-in
    data/gym_sets.csv     one row per set you lift
    data/runs.csv         one row per run

Every page uses the same three functions: load(), save() and add_rows().
"""

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "data"

# name -> (file name, column names in order)
FILES = {
    "bodyweight": ("bodyweight.csv", ["date", "weight_kg", "sleep_h", "soreness", "macros", "notes"]),
    "gym": ("gym_sets.csv", ["date", "session", "exercise", "set_number", "weight_kg", "reps"]),
    "runs": ("runs.csv", ["date", "run_type", "duration_min", "feel", "reps_done", "reps_planned", "notes"]),
}

# Columns that should always be numbers.
NUMERIC_COLUMNS = ["weight_kg", "set_number", "reps", "duration_min", "feel", "sleep_h", "soreness", "reps_done", "reps_planned"]


def file_path(name):
    """Full path of one of the CSV files."""
    return DATA_DIR / FILES[name][0]


def load(name):
    """Read a CSV into a DataFrame. Creates an empty file if it doesn't exist yet."""
    _, columns = FILES[name]
    path = file_path(name)

    if not path.exists():
        DATA_DIR.mkdir(exist_ok=True)
        pd.DataFrame(columns=columns).to_csv(path, index=False)

    df = pd.read_csv(path)

    # Make sure every expected column exists (protects against hand-edited files).
    for col in columns:
        if col not in df.columns:
            df[col] = None
    df = df[columns]

    # Tidy up the types: real dates, real numbers, notes as text.
    df["date"] = pd.to_datetime(df["date"]).dt.date
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "notes" in df.columns:
        df["notes"] = df["notes"].fillna("").astype(str)
    if "macros" in df.columns:
        df["macros"] = df["macros"].fillna("").astype(str)      # "hit", "mostly", "no" or empty

    return df.sort_values("date").reset_index(drop=True)


def save(name, df):
    """Overwrite a CSV with the DataFrame (dates written as YYYY-MM-DD)."""
    _, columns = FILES[name]
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    for col in columns:                      # older files may lack newer columns
        if col not in out.columns:
            out[col] = None
    out = out[columns].sort_values("date")
    DATA_DIR.mkdir(exist_ok=True)
    out.to_csv(file_path(name), index=False)


def add_rows(name, new_rows):
    """Append new rows (a DataFrame) to a CSV and return the combined data."""
    combined = pd.concat([load(name), new_rows], ignore_index=True)
    save(name, combined)
    return combined
