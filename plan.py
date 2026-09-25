"""
plan.py - The "Road to New Year" lean bulk plan, written down as Python data.

Everything the dashboard knows about the plan lives in this one file:
dates, gym sessions and macro targets. If the plan changes, edit this file.
"""

from datetime import date, timedelta

# ---------------------------------------------------------------------------
# Key dates and numbers
# ---------------------------------------------------------------------------
PLAN_START = date(2026, 9, 28)   # Monday of week 1
TOTAL_WEEKS = 14
PLAN_END = PLAN_START + timedelta(weeks=TOTAL_WEEKS) - timedelta(days=1)   # Sunday 3 Jan 2027

START_WEIGHT_KG = 86.0           # where the target line starts
TARGET_GAIN_PER_WEEK_KG = 0.25   # lean bulk pace (about 89-90 kg by New Year)

# ---------------------------------------------------------------------------
# Lean bulk macros
# ---------------------------------------------------------------------------
MACROS = {"Calories": 3700, "Protein": 195, "Fat": 90, "Carbs": 530}
MACRO_UNITS = {"Calories": "kcal", "Protein": "g", "Fat": "g", "Carbs": "g"}
EASY_CARB_WINS = ["Oats", "Bagels", "Bananas", "Juice", "Milk"]
CALORIE_ADJUSTMENT = 200         # add or remove this many kcal (from carbs)

RULES = [
    "Weigh every morning and judge by the weekly average, not the daily number.",
    "Target +0.25 kg a week: about 89-90 kg by New Year.",
    "Gaining faster than that? Take about 200 kcal off, from carbs.",
    "No change after two weeks? Add about 200 kcal. Easy carb wins: oats, bagels, bananas, juice, milk.",
    "Barbell squats 4 x 5-8. Everything else 3 sets of 8-12. Add weight once you own the top of the range on every set.",
    "Six sessions a week, Sunday off.",
]

# ---------------------------------------------------------------------------
# Gym sessions (exercise lists straight from the plan)
# ---------------------------------------------------------------------------
LEGS = ["Barbell squats", "RDL", "Smith single-leg squats", "Leg extension", "Hamstring curl", "Bike"]

GYM_SESSIONS = {
    "Push A": ["Bench press", "Incline bench", "Chest fly", "Shoulder press",
               "Cable lateral raise", "Tricep pushdown", "Tricep overhead"],
    "Push B": ["Incline bench", "Chest fly", "Shoulder press", "Lateral raise",
               "Face pulls", "Tricep overhead", "Tricep pushdown"],
    "Pull A": ["Pull-ups", "Bent-over rows", "Single-arm DB rows", "Lat pulldown",
               "Cable rows", "Bicep curl", "Hammer curl"],
    "Pull B": ["Bent-over rows", "Tricep pushdown", "Cable pullovers", "Bicep curl",
               "Cable curl", "Hammer curl"],
    "Legs A": LEGS,
    "Legs B": LEGS,
}

# Every exercise that appears in any session, in a stable order (no duplicates).
ALL_EXERCISES = []
for _exercises in GYM_SESSIONS.values():
    for _ex in _exercises:
        if _ex not in ALL_EXERCISES:
            ALL_EXERCISES.append(_ex)

# Which gym session happens on which weekday (0 = Monday ... 6 = Sunday).
GYM_SCHEDULE = {0: "Push A", 1: "Pull A", 2: "Legs A", 3: "Push B", 4: "Pull B", 5: "Legs B", 6: "Rest"}
WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Progression: the rep range to work in, and the jump to make once you own the top of it.
ISOLATION = ["Chest fly", "Cable lateral raise", "Lateral raise", "Face pulls", "Tricep pushdown",
             "Tricep overhead", "Bicep curl", "Hammer curl", "Cable curl", "Cable pullovers",
             "Leg extension", "Hamstring curl"]


def default_sets(exercise):
    """How many sets to pre-fill in the gym log form for an exercise."""
    return 4 if exercise == "Barbell squats" else 3


def rep_range(exercise):
    return (5, 8) if exercise == "Barbell squats" else (8, 12)


def increment(exercise):
    """Weight jump when you hit the top of the rep range on every set."""
    if exercise == "Pull-ups":
        return 0            # bodyweight: progress by reps
    return 1.0 if exercise in ISOLATION else 2.5


# ---------------------------------------------------------------------------
# Helper functions: "what does the plan say for this date?"
# ---------------------------------------------------------------------------
def week_number(d):
    """Plan week for a date. 0 = before the plan, 15 = after it finished."""
    if d < PLAN_START:
        return 0
    week = (d - PLAN_START).days // 7 + 1
    return min(week, TOTAL_WEEKS + 1)


def week_dates(week):
    """(Monday, Sunday) of a plan week."""
    start = PLAN_START + timedelta(weeks=week - 1)
    return start, start + timedelta(days=6)


def plan_status(d):
    """'before', 'during' or 'after' the 14-week plan."""
    if d < PLAN_START:
        return "before"
    if d > PLAN_END:
        return "after"
    return "during"


def target_weight(d):
    """Where bodyweight should be on a date if gaining 0.25 kg every week."""
    days = max(0, (d - PLAN_START).days)
    return START_WEIGHT_KG + TARGET_GAIN_PER_WEEK_KG * days / 7


def gym_for_date(d):
    """Gym session name for a date, e.g. 'Push A' or 'Rest'."""
    return GYM_SCHEDULE[d.weekday()]
