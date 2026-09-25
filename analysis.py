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
    stamps = pd.to_datetime(df["date"])
    df["avg_7d"] = pd.Series(df["weight_kg"].values, index=stamps).rolling("7D").mean().values
    df["target"] = [plan.target_weight(d) for d in df["date"]]
    return df


def average_between(bw, start, end):
    """Average bodyweight for weigh-ins between two dates (inclusive), or None."""
    mask = (bw["date"] >= start) & (bw["date"] <= end)
    values = bw.loc[mask, "weight_kg"].dropna()
    return float(values.mean()) if len(values) else None


def macro_rate(bw, start, end):
    """(days hit or mostly, days logged, rate) between two dates. Hit counts 1, mostly half."""
    rows = bw[(bw["date"] >= start) & (bw["date"] <= end) & (bw["macros"] != "")]
    if rows.empty:
        return 0, 0, None
    score = (rows["macros"] == "hit").sum() + 0.5 * (rows["macros"] == "mostly").sum()
    return int(((rows["macros"] == "hit") | (rows["macros"] == "mostly")).sum()), len(rows), score / len(rows)


def calorie_suggestion(bw, today):
    """
    The plan's rule of thumb:
      * gaining faster than 0.25 kg/week  -> take 200 kcal off (from carbs)
      * no change after 2 weeks           -> add 200 kcal (if macros were actually hit)
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
    if weekly_change > plan.TARGET_GAIN_PER_WEEK_KG + 0.10:
        return (base - plan.CALORIE_ADJUSTMENT, "⬇️",
                f"Gaining {weekly_change:+.2f} kg/week, faster than the 0.25 kg target. "
                f"Drop about {plan.CALORIE_ADJUSTMENT} kcal from carbs.")
    if two_weeks_ago is not None and abs(this_week - two_weeks_ago) < 0.1:
        hit, logged, rate = macro_rate(bw, today - timedelta(days=13), today)
        if logged >= 7 and rate < 0.7:
            return (base, "🍽️",
                    f"No real change over two weeks, but macros were only hit or nearly hit {hit} of the last {logged} days. "
                    "Eat the plan as written before adding calories.")
        return (base + plan.CALORIE_ADJUSTMENT, "⬆️",
                f"No real change over the last two weeks. Add about {plan.CALORIE_ADJUSTMENT} kcal (easy carb wins below).")
    return base, "✅", f"Gaining {weekly_change:+.2f} kg/week. On track, keep the macros as they are."


def projection(bw, today):
    """Where the 7-day average lands on 3 Jan if the last week's rate continues."""
    table = bodyweight_table(bw)
    if len(table) < 8:
        return None
    last = table.iloc[-1]
    earlier = table[table["date"] <= last["date"] - timedelta(days=7)]
    if earlier.empty:
        return None
    ago = earlier.iloc[-1]
    per_week = (last["avg_7d"] - ago["avg_7d"]) / ((last["date"] - ago["date"]).days / 7)
    return per_week, last["avg_7d"] + per_week * (plan.PLAN_END - last["date"]).days / 7


def weigh_streak(bw, today):
    """Consecutive days with a weigh-in, ending today or yesterday."""
    dates = set(bw["date"])
    d = today if today in dates else today - timedelta(days=1)
    n = 0
    while d in dates:
        n += 1
        d -= timedelta(days=1)
    return n


# ---------------------------------------------------------------------------
# Gym
# ---------------------------------------------------------------------------
def top_sets(gym):
    """
    One row per exercise per day: the best set that day (heaviest, then most reps).
    Adds est_1rm (Epley) and is_pb (beat every earlier top set for that exercise).
    """
    columns = ["date", "exercise", "session", "weight_kg", "reps", "est_1rm", "score", "is_pb"]
    if gym.empty:
        return pd.DataFrame(columns=columns)
    df = gym.dropna(subset=["weight_kg", "reps"]).copy()
    df = df[df["reps"] > 0]
    if df.empty:
        return pd.DataFrame(columns=columns)
    df["score"] = df["weight_kg"] * 1000 + df["reps"]
    df["est_1rm"] = (df["weight_kg"] * (1 + df["reps"] / 30)).round(1)
    df = df.sort_values(["exercise", "date", "score"], ascending=[True, True, False])
    top = df.groupby(["exercise", "date"], as_index=False).first()
    top = top.sort_values(["exercise", "date"]).reset_index(drop=True)
    previous_best = top.groupby("exercise")["score"].transform(lambda s: s.cummax().shift(1))
    top["is_pb"] = previous_best.notna() & (top["score"] > previous_best)
    return top[columns]


def all_time_bests(gym):
    """The best ever top set for each exercise, in the plan's order."""
    top = top_sets(gym)
    if top.empty:
        return top
    best = top.sort_values("score", ascending=False).groupby("exercise", as_index=False).first()
    order = {name: i for i, name in enumerate(plan.ALL_EXERCISES)}
    best = best.assign(_order=best["exercise"].map(order).fillna(999)).sort_values("_order")
    return best[["exercise", "date", "weight_kg", "reps", "est_1rm"]]


def recent_pbs(gym, today, days=7):
    """New bests set in the last `days` days."""
    top = top_sets(gym)
    if top.empty:
        return top
    since = today - timedelta(days=days - 1)
    return top[top["is_pb"] & (top["date"] >= since)].sort_values("date", ascending=False)


def progression(exercise, last_sets):
    """What to aim for next time, from the last time you did this exercise. Returns (kg, text) or None."""
    last_sets = last_sets[last_sets["reps"] > 0]
    if last_sets.empty or exercise == "Bike":
        return None
    lo, hi = plan.rep_range(exercise)
    inc = plan.increment(exercise)
    kg = float(last_sets["weight_kg"].max())
    top = last_sets[last_sets["weight_kg"] == kg]
    if (top["reps"] >= hi).all():
        return (kg + inc, f"Try {kg + inc:.1f} kg x {lo}-{hi}") if inc else (kg, f"Add a rep: aim for {hi + 1}+")
    if (top["reps"] < lo).any():
        return kg, f"Stay at {kg:.1f} kg, get every set to {lo}+"
    return kg, f"Stay at {kg:.1f} kg, push toward {hi} reps"


def sessions_done(gym):
    """One row per (date, session) that has at least one set logged (or a rest day marked)."""
    if gym.empty:
        return gym[["date", "session"]]
    return gym[["date", "session"]].drop_duplicates()


def weekly_volume(gym):
    """Sets per plan week, split by Push / Pull / Legs."""
    rows = []
    working = gym[gym["reps"] > 0] if not gym.empty else gym
    for week in range(1, plan.TOTAL_WEEKS + 1):
        start, end = plan.week_dates(week)
        in_week = working[(working["date"] >= start) & (working["date"] <= end)] if not working.empty else working
        groups = in_week["session"].str.split(" ").str[0].value_counts() if not in_week.empty else {}
        rows.append({"Week": week, "Push": int(groups.get("Push", 0)), "Pull": int(groups.get("Pull", 0)), "Legs": int(groups.get("Legs", 0))})
    return pd.DataFrame(rows)


def adherence(gym, bw, today):
    """Gym sessions and macro days against the days that have happened so far, or None before the plan."""
    if plan.PLAN_START > today:
        return None
    upto = min(today, plan.PLAN_END)
    days = (upto - plan.PLAN_START).days + 1
    gym_planned = sum(1 for i in range(days) if plan.gym_for_date(plan.PLAN_START + timedelta(days=i)) != "Rest")
    done = sessions_done(gym)
    gym_done = int(((done["date"] >= plan.PLAN_START) & (done["date"] <= upto) & (done["session"] != "Rest")).sum())
    hit, logged, rate = macro_rate(bw, plan.PLAN_START, upto)
    return {"days": days, "gym_planned": gym_planned, "gym_done": gym_done, "macro_hit": hit, "macro_logged": logged}


# ---------------------------------------------------------------------------
# Weekly review (one row per plan week)
# ---------------------------------------------------------------------------
def weekly_review(bw, gym):
    rows = []
    previous_avg = None
    done = sessions_done(gym)
    for week in range(1, plan.TOTAL_WEEKS + 1):
        start, end = plan.week_dates(week)
        avg = average_between(bw, start, end)
        change = None if (avg is None or previous_avg is None) else avg - previous_avg
        if avg is not None:
            previous_avg = avg
        in_week = (done["date"] >= start) & (done["date"] <= end) & (done["session"] != "Rest")
        hit, logged, _ = macro_rate(bw, start, end)
        sleep = bw.loc[(bw["date"] >= start) & (bw["date"] <= end), "sleep_h"].dropna()
        rows.append({
            "Week": week,
            "Dates": f"{start:%d %b} - {end:%d %b}",
            "Avg weight (kg)": np.nan if avg is None else round(avg, 2),
            "Change (kg)": np.nan if change is None else round(change, 2),
            "Target avg (kg)": round(plan.target_weight(start + timedelta(days=3)), 2),
            "Gym sessions": f"{int(in_week.sum())} / 6",
            "Macros": f"{hit} / {logged}" if logged else None,
            "Sleep (h)": np.nan if sleep.empty else round(float(sleep.mean()), 1),
        })
    return pd.DataFrame(rows)
