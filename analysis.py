"""
analysis.py - turning the raw CSV rows into useful numbers.

Nothing here touches Streamlit; these are plain pandas functions so they are
easy to test and reuse. Each function takes DataFrames from storage.load().
"""

from datetime import timedelta

import numpy as np
import pandas as pd

import plan


# ---------------------------------------------------------------------------
# Bodyweight
# ---------------------------------------------------------------------------
def bodyweight_table(bw):
    """Add a 7-day rolling average and the target weight to the bodyweight log."""
    if bw.empty:
        return bw.assign(avg_7d=pd.Series(dtype=float), target=pd.Series(dtype=float))

    df = bw.sort_values("date").copy()
    # A time-based rolling window: the mean of every weigh-in in the last 7 days.
    stamps = pd.to_datetime(df["date"])
    df["avg_7d"] = (
        pd.Series(df["weight_kg"].values, index=stamps).rolling("7D").mean().values
    )
    df["target"] = [plan.target_weight(d) for d in df["date"]]
    return df


def average_between(bw, start, end):
    """Average bodyweight for weigh-ins between two dates (inclusive), or None."""
    mask = (bw["date"] >= start) & (bw["date"] <= end)
    values = bw.loc[mask, "weight_kg"].dropna()
    return float(values.mean()) if len(values) else None


def calorie_suggestion(bw, today):
    """
    Apply the plan's rule of thumb:
      * gaining faster than 0.25 kg/week  -> take 200 kcal off (from carbs)
      * no change after 2 weeks           -> add 200 kcal
      * otherwise                         -> stay the course
    Returns (calories to eat, status icon, message).
    """
    base = plan.MACROS["Calories"]
    this_week = average_between(bw, today - timedelta(days=6), today)
    last_week = average_between(bw, today - timedelta(days=13), today - timedelta(days=7))
    two_weeks_ago = average_between(bw, today - timedelta(days=20), today - timedelta(days=14))

    if this_week is None or last_week is None:
        return base, "ℹ️", "Keep weighing in daily. Suggestions start once you have two weeks of data."

    weekly_change = this_week - last_week
    if weekly_change > plan.TARGET_GAIN_PER_WEEK_KG + 0.10:   # small tolerance for noise
        return (base - plan.CALORIE_ADJUSTMENT, "⬇️",
                f"Gaining {weekly_change:+.2f} kg/week, faster than the 0.25 kg target. "
                f"Drop about {plan.CALORIE_ADJUSTMENT} kcal from carbs.")

    if two_weeks_ago is not None and abs(this_week - two_weeks_ago) < 0.1:
        return (base + plan.CALORIE_ADJUSTMENT, "⬆️",
                "No real change over the last two weeks. "
                f"Add about {plan.CALORIE_ADJUSTMENT} kcal (easy carb wins below).")

    return base, "✅", f"Gaining {weekly_change:+.2f} kg/week. On track, keep the macros as they are."


# ---------------------------------------------------------------------------
# Gym
# ---------------------------------------------------------------------------
def top_sets(gym):
    """
    One row per exercise per day: the best set that day.
    "Best" = heaviest weight, and for the same weight, the most reps.
    Adds:
      est_1rm  - estimated one-rep max (Epley formula)
      is_pb    - True if this beat every earlier top set for that exercise
    """
    columns = ["date", "exercise", "session", "weight_kg", "reps", "est_1rm", "score", "is_pb"]
    if gym.empty:
        return pd.DataFrame(columns=columns)

    df = gym.dropna(subset=["weight_kg", "reps"]).copy()
    df = df[df["reps"] > 0]
    if df.empty:
        return pd.DataFrame(columns=columns)

    # A single number that ranks sets: heavier always wins, then more reps.
    df["score"] = df["weight_kg"] * 1000 + df["reps"]
    df["est_1rm"] = (df["weight_kg"] * (1 + df["reps"] / 30)).round(1)

    # Keep the highest-scoring set for each exercise on each date.
    df = df.sort_values(["exercise", "date", "score"], ascending=[True, True, False])
    top = df.groupby(["exercise", "date"], as_index=False).first()

    # A new best = better than the best of all previous days for that exercise.
    top = top.sort_values(["exercise", "date"]).reset_index(drop=True)
    previous_best = top.groupby("exercise")["score"].transform(lambda s: s.cummax().shift(1))
    top["is_pb"] = previous_best.notna() & (top["score"] > previous_best)

    return top[columns]


def all_time_bests(gym):
    """The best ever top set for each exercise, plus how recent it is."""
    top = top_sets(gym)
    if top.empty:
        return top
    best = top.sort_values("score", ascending=False).groupby("exercise", as_index=False).first()
    # Order by position in the plan, not alphabetically.
    order = {name: i for i, name in enumerate(plan.ALL_EXERCISES)}
    best = best.assign(_order=best["exercise"].map(order).fillna(999)).sort_values("_order")
    return best[["exercise", "date", "weight_kg", "reps", "est_1rm"]]


def recent_pbs(gym, today, days=7):
    """New bests set in the last `days` days (used for the dashboard highlight)."""
    top = top_sets(gym)
    if top.empty:
        return top
    since = today - timedelta(days=days - 1)   # 7 days including today
    return top[top["is_pb"] & (top["date"] >= since)].sort_values("date", ascending=False)


def sessions_done(gym):
    """One row per (date, session) that has at least one set logged."""
    if gym.empty:
        return gym[["date", "session"]]
    return gym[["date", "session"]].drop_duplicates()


# ---------------------------------------------------------------------------
# Weekly review (one row per plan week)
# ---------------------------------------------------------------------------
def weekly_review(bw, gym, runs):
    rows = []
    previous_avg = None
    done = sessions_done(gym)

    for week in range(1, plan.TOTAL_WEEKS + 1):
        start, end = plan.week_dates(week)
        phase = plan.phase_for_week(week)

        avg = average_between(bw, start, end)
        change = None if (avg is None or previous_avg is None) else avg - previous_avg
        if avg is not None:
            previous_avg = avg

        gym_count = int(((done["date"] >= start) & (done["date"] <= end)).sum())
        run_mask = (runs["date"] >= start) & (runs["date"] <= end)
        run_count = int(run_mask.sum())
        feel = runs.loc[run_mask, "feel"].mean() if run_count else None

        rows.append({
            "Week": week,
            "Dates": f"{start:%d %b} - {end:%d %b}",
            "Phase": phase["name"],
            "Avg weight (kg)": np.nan if avg is None else round(avg, 2),
            "Change (kg)": np.nan if change is None else round(change, 2),
            "Target avg (kg)": round(plan.target_weight(start + timedelta(days=3)), 2),
            "Gym sessions": f"{gym_count} / 6",
            "Runs": f"{run_count} / {phase['runs_per_week']}",
            "Avg run feel": np.nan if feel is None else round(float(feel), 1),
            "_start": start,
            "_end": end,
        })

    return pd.DataFrame(rows)
