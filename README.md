# Road to New Year: Lean Bulk Dashboard

A simple Streamlit dashboard for the 14-week "Road to New Year" plan
(28 Sep 2026 to 3 Jan 2027). Log your gym sessions, morning weigh-ins and runs,
then watch your progress against the plan.

All data is stored in plain CSV files in the `data/` folder, so nothing is
locked away: open them in Excel or edit them inside the app.

## Run it

```bash
pip install -r requirements.txt
streamlit run Dashboard.py
```

Your browser opens at http://localhost:8501. Use the sidebar to move between pages.

## Pages

| Page | What it does |
|---|---|
| **Dashboard** (`Dashboard.py`) | Phase and week you are in, today's gym session and run, bodyweight chart with 7-day average and the +0.25 kg/week target line, macros with the plan's +/- 200 kcal rule applied, this week's checklist, new bests in the last 7 days. |
| **Log Gym Session** | Pick a session (or Rest) and enter weight x reps per set. The table is pre-filled from last time, with a target for each exercise: hit the top of the rep range on every set and it tells you the next weight to try. |
| **Log Bodyweight** | One weigh-in per morning, plus sleep hours and a soreness score. Saving the same date again replaces it. |
| **Log Run** | Type, minutes, how it felt 1-10, and for hard runs the reps completed out of planned (the plan's "8 intervals" test). |
| **Exercise Progress** | A chart per exercise of your top set over time, new bests marked with a star, all-time bests table, estimated 1RM. |
| **Weekly Review** | One row per plan week, adherence per phase, the "ready for Maintain?" check, sets per week by session type, and weekly weight change vs target. |
| **Progress Photos** | One photo every two weeks (start, then every fortnight, then the finish), stored in `data/photos/` (not committed to git), with a then-and-now comparison. |
| **Edit Data** | Fix or delete any row in the three CSV files, or download them. |
| **Settings** | Set the date you actually move to Maintain if you stay in Sharpen longer, as the plan allows. Everything follows it. |

## Files

```
Dashboard.py      Dashboard page (start here)
plan.py           The plan as data: dates, phases, sessions, runs, macros. Edit this if the plan changes.
storage.py        Reads and writes the CSV files
analysis.py       Turns raw rows into averages, top sets, PBs and the weekly review
charts.py         The Plotly charts
pages/            One file per sidebar page
data/             Your CSV files (created automatically on first run)
```

## Tips

- Bodyweight moves like pull-ups: log the weight as 0 (or the added weight).
- Bike: put the minutes in the reps column and leave weight at 0.
- Leave reps empty for any set you skipped; only sets with reps are saved.
- A "new best" is a heavier top set, or the same weight for more reps than ever before.

## Web version (no Python needed)

`web/road-to-new-year.html` is the same dashboard as a single web page. It is
published as a Claude artifact so it can be used straight from the Claude app,
where logs are saved to the artifact's database. Opened as a plain file it still
works, saving to the browser's local storage instead.
