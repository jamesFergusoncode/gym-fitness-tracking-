"""
plan.py - The "Road to New Year" plan written down as Python data.

Everything the dashboard knows about the plan lives in this one file:
dates, phases, gym sessions, run prescriptions and macro targets.
If the plan ever changes, this is the only file you need to edit.
"""

import json
from datetime import date, timedelta
from pathlib import Path

SETTINGS_FILE = Path(__file__).resolve().parent / "data" / "settings.json"


def load_settings():
    """Small JSON file of things you can change: for now, when Maintain starts."""
    try:
        return json.loads(SETTINGS_FILE.read_text())
    except (OSError, ValueError):
        return {}


def save_settings(settings):
    SETTINGS_FILE.parent.mkdir(exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(settings, indent=2))

# ---------------------------------------------------------------------------
# Key dates and numbers
# ---------------------------------------------------------------------------
PLAN_START = date(2026, 9, 28)   # Monday of week 1
TOTAL_WEEKS = 14
# The last day of the plan is the Sunday of week 14 (3 Jan 2027).
PLAN_END = PLAN_START + timedelta(weeks=TOTAL_WEEKS) - timedelta(days=1)

START_WEIGHT_KG = 86.0           # where the target line starts
TARGET_GAIN_PER_WEEK_KG = 0.25   # lean bulk pace (about 89-90 kg by New Year)

# ---------------------------------------------------------------------------
# Lean bulk macros
# ---------------------------------------------------------------------------
MACROS = {
    "Calories": 3700,
    "Protein": 195,
    "Fat": 90,
    "Carbs": 530,
}
MACRO_UNITS = {"Calories": "kcal", "Protein": "g", "Fat": "g", "Carbs": "g"}
EASY_CARB_WINS = ["Oats", "Bagels", "Bananas", "Juice", "Milk"]
CALORIE_ADJUSTMENT = 200         # add or remove this many kcal (from carbs)

# ---------------------------------------------------------------------------
# Phases
# ---------------------------------------------------------------------------
PHASES = [
    {"name": "Build",    "first_week": 1, "last_week": 2,  "runs_per_week": 5},
    {"name": "Sharpen",  "first_week": 3, "last_week": 4,  "runs_per_week": 5},
    {"name": "Maintain", "first_week": 5, "last_week": 14, "runs_per_week": 3},
]

# Short reminders from the "Making It Work" section of the plan.
PHASE_TIPS = {
    "Build": [
        "Wed: do intervals before legs (or split them by a few hours).",
        "Legs A: squats down to 3 sets, skip the bike.",
        "Legs B: stop 1-2 reps short of failure.",
    ],
    "Sharpen": [
        "Wed: do intervals before legs (or split them by a few hours).",
        "Legs A: squats down to 3 sets, skip the bike.",
        "Legs B: stop 1-2 reps short of failure.",
        "Move to Maintain when you can finish 8 intervals without dying and "
        "recover quickly between sprints. Not there by week 5? Stay in Sharpen a bit longer.",
    ],
    "Maintain": [
        "Back to full leg volume: 4 sets of squats, bike included.",
        "Push your lifts harder now that running is lighter.",
        "You're running less, so if weight climbs faster than 0.25 kg/week, "
        "drop about 200 kcal from carbs.",
    ],
}

# ---------------------------------------------------------------------------
# Gym sessions (exercise lists straight from the plan)
# ---------------------------------------------------------------------------
LEGS = [
    "Barbell squats",
    "RDL",
    "Smith single-leg squats",
    "Leg extension",
    "Hamstring curl",
    "Bike",
]

GYM_SESSIONS = {
    "Push A": [
        "Bench press", "Incline bench", "Chest fly", "Shoulder press",
        "Cable lateral raise", "Tricep pushdown", "Tricep overhead",
    ],
    "Push B": [
        "Incline bench", "Chest fly", "Shoulder press", "Lateral raise",
        "Face pulls", "Tricep overhead", "Tricep pushdown",
    ],
    "Pull A": [
        "Pull-ups", "Bent-over rows", "Single-arm DB rows", "Lat pulldown",
        "Cable rows", "Bicep curl", "Hammer curl",
    ],
    "Pull B": [
        "Bent-over rows", "Tricep pushdown", "Cable pullovers", "Bicep curl",
        "Cable curl", "Hammer curl",
    ],
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
GYM_SCHEDULE = {
    0: "Push A",
    1: "Pull A",
    2: "Legs A",
    3: "Push B",
    4: "Pull B",
    5: "Legs B",
    6: "Rest",
}
WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def default_sets(exercise, phase_name):
    """How many sets to pre-fill in the gym log form for an exercise."""
    if exercise == "Barbell squats":
        # The plan says 4 x 5-8, but drop to 3 sets while running is heavy.
        return 4 if phase_name == "Maintain" else 3
    return 3


# ---------------------------------------------------------------------------
# Running
# ---------------------------------------------------------------------------
RUN_TYPES = ["Sprints", "Intervals", "Shuttles", "Easy"]

# For each phase: weekday -> (run type, what to do). Days missing = no run.
RUN_SCHEDULE = {
    "Build": {
        0: ("Sprints",   "8 x 20s"),
        1: ("Easy",      "30 min"),
        2: ("Intervals", "6 x 1 min on / 1 min off"),
        4: ("Shuttles",  "6 rounds, 60s rest"),
        6: ("Easy",      "35 min"),
    },
    "Sharpen": {
        0: ("Sprints",   "10 x 20s"),
        1: ("Easy",      "30 min"),
        2: ("Intervals", "8 x 1 min on / 1 min off"),
        4: ("Shuttles",  "8 rounds, 45s rest"),
        6: ("Easy",      "40 min"),
    },
    "Maintain": {
        0: ("Sprints",   "8 x 20s + 6 shuttle rounds"),
        2: ("Intervals", "8 x 1 min on / 1 min off"),
        6: ("Easy",      "40 min"),
    },
}

# How many reps of each hard run the plan asks for, per phase.
RUN_REPS = {
    "Build":    {"Sprints": 8,  "Intervals": 6, "Shuttles": 6},
    "Sharpen":  {"Sprints": 10, "Intervals": 8, "Shuttles": 8},
    "Maintain": {"Sprints": 8,  "Intervals": 8, "Shuttles": 6},
}

# Progression: the rep range to work in, and the jump to make once you own the top of it.
ISOLATION = ["Chest fly", "Cable lateral raise", "Lateral raise", "Face pulls", "Tricep pushdown",
             "Tricep overhead", "Bicep curl", "Hammer curl", "Cable curl", "Cable pullovers",
             "Leg extension", "Hamstring curl"]


def rep_range(exercise):
    return (5, 8) if exercise == "Barbell squats" else (8, 12)


def increment(exercise):
    """Weight jump when you hit the top of the rep range on every set."""
    if exercise == "Pull-ups":
        return 0            # bodyweight: progress by reps
    return 1.0 if exercise in ISOLATION else 2.5


# What each run session actually is, in plain words.
RUN_GUIDE = {
    "Sprints": {
        "what": "Short, all-out efforts on flat grass, a track or a quiet path.",
        "how": "Build to full speed over the first few strides, hold it for 20 seconds, then walk back to the start "
               "and take about 90 seconds before the next one. Every rep should feel as fast as the first; "
               "if you slow down a lot, rest longer.",
        "effort": "9-10 / 10, you could not say a word",
    },
    "Intervals": {
        "what": "One minute hard, one minute easy, repeated.",
        "how": "The hard minute is around 5 km race effort: breathing heavily, unable to chat. The easy minute is a "
               "slow jog, not a stop. Aim to run the last hard minute at the same pace as the first. This is the "
               "session the plan uses to judge when you are ready for Maintain.",
        "effort": "8 / 10, a few words at most",
    },
    "Shuttles": {
        "what": "Sprint 10 m out, turn, sprint back, turn, sprint 10 m out again. That is one round.",
        "how": "Mark two lines 10 m apart. Stay low into each turn, plant the outside foot and drive out. Rest between "
               "rounds standing or walking. About 30 m of sprinting and three turns per round.",
        "effort": "9 / 10, sharp and fast, quality over quantity",
    },
    "Easy": {
        "what": "A relaxed, conversational-pace run. Recovery and base, not a workout to push.",
        "how": "If you cannot chat in full sentences, slow down. Keep it flat and steady. Sunday's easy run is a "
               "little longer than Tuesday's.",
        "effort": "3-4 / 10, could talk the whole way",
    },
}

RUN_NOTES = [
    "Warm-up: 10 min easy jog + leg swings.",
    "Cool-down: 10 min easy jog.",
    "Every session is 30+ minutes including warm-up and cool-down.",
    "Shuttle round: sprint 10 m, turn, back, turn, 10 m.",
    "Easy runs: if you can't chat, slow down.",
]


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


def phase_for_week(week):
    """The phase dict for a plan week (clamped to Build / Maintain outside the plan)."""
    if week < 1:
        return PHASES[0]
    for phase in PHASES:
        if phase["first_week"] <= week <= phase["last_week"]:
            return phase
    return PHASES[-1]


def maintain_start():
    """The date Maintain actually starts: the calendar's 26 Oct, unless you set your own."""
    value = load_settings().get("maintain_start")
    if value:
        try:
            return date.fromisoformat(value)
        except ValueError:
            pass
    return week_dates(PHASES[2]["first_week"])[0]


def phase_for_date(d):
    """Phase on a date. Honours a Maintain start date you chose in Settings."""
    week = week_number(d)
    if week < 1:
        return PHASES[0]
    if d >= maintain_start():
        return PHASES[2]
    return PHASES[0] if week <= 2 else PHASES[1]


def phase_starts():
    """[(name, first date)] for each phase, honouring the override."""
    return [("Build", PLAN_START), ("Sharpen", week_dates(3)[0]), ("Maintain", maintain_start())]


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


def run_for_date(d):
    """(run type, prescription) for a date, or None if no run that day."""
    phase = phase_for_date(d)
    return RUN_SCHEDULE[phase["name"]].get(d.weekday())
