"""
Progress Photos - one photo every two weeks, saved under data/photos/.

Bodyweight lies week to week. A fortnightly photo, same spot and same light,
tells you whether the bulk is lean. Checkpoints are the start of week 1, then
every two weeks, then the final day.
"""

from datetime import date, timedelta
from pathlib import Path

import streamlit as st
from PIL import Image, ImageOps

import plan
import storage

st.set_page_config(page_title="Progress Photos", page_icon="📷", layout="wide")
st.title("📷 Progress Photos")
st.caption("One photo every two weeks: same spot, same light, same pose.")

PHOTO_DIR = storage.DATA_DIR / "photos"
PHOTO_DIR.mkdir(parents=True, exist_ok=True)

# Checkpoint dates: 28 Sep, 12 Oct, 26 Oct, ... and the final day, 3 Jan.
CHECKPOINTS = [plan.PLAN_START + timedelta(weeks=2 * k) for k in range(7)] + [plan.PLAN_END]


def label(d):
    if d == plan.PLAN_END:
        return "Finish"
    if d == plan.PLAN_START:
        return "Start"
    return f"Week {plan.week_number(d)}"


def photo_path(d):
    return PHOTO_DIR / f"{d:%Y-%m-%d}.jpg"


bodyweight = storage.load("bodyweight")


def weight_near(d):
    """The weigh-in closest to a date (within 3 days), or None."""
    near = bodyweight[(bodyweight["date"] >= d - timedelta(days=3)) & (bodyweight["date"] <= d + timedelta(days=3))]
    if near.empty:
        return None
    near = near.assign(gap=(near["date"] - d).abs()).sort_values("gap")
    return float(near["weight_kg"].iloc[0])


# ---------------------------------------------------------------------------
# What is due?
# ---------------------------------------------------------------------------
today = date.today()
missing = [c for c in CHECKPOINTS if not photo_path(c).exists()]
due = next((c for c in missing if (c - today).days >= -6), None)
if due is None:
    st.success("All checkpoints have a photo. Nice work.")
elif due <= today:
    st.success(f"Photo due now: **{label(due)}** ({due:%a %d %b}).")
else:
    st.info(f"Next photo: **{label(due)}** on {due:%a %d %b}, in {(due - today).days} days.")

# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------
with st.form("photo_form"):
    col1, col2 = st.columns(2)
    default = due or min(CHECKPOINTS, key=lambda c: abs((c - today).days))
    slot = col1.selectbox("Checkpoint", CHECKPOINTS, index=CHECKPOINTS.index(default),
                          format_func=lambda c: f"{label(c)} · {c:%d %b}" + (" (has photo)" if photo_path(c).exists() else ""))
    uploaded = col2.file_uploader("Photo", type=["jpg", "jpeg", "png", "webp"])
    saved = st.form_submit_button("Save photo", type="primary")

if saved:
    if uploaded is None:
        st.warning("Choose a photo first.")
    else:
        # Shrink to a long edge of 1280px and fix phone rotation before saving.
        img = ImageOps.exif_transpose(Image.open(uploaded)).convert("RGB")
        img.thumbnail((1280, 1280))
        img.save(photo_path(slot), "JPEG", quality=85)
        st.success(f"Saved photo for {label(slot)}.")
        st.rerun()

# ---------------------------------------------------------------------------
# Then and now
# ---------------------------------------------------------------------------
have = [c for c in CHECKPOINTS if photo_path(c).exists()]
if len(have) >= 2:
    st.subheader("Then and now")
    a, b = st.columns(2)
    for col, c in ((a, have[0]), (b, have[-1])):
        kg = weight_near(c)
        col.image(str(photo_path(c)), caption=f"{label(c)} · {c:%d %b}" + (f" · {kg:.1f} kg" if kg else ""), use_container_width=True)

# ---------------------------------------------------------------------------
# All checkpoints
# ---------------------------------------------------------------------------
st.subheader("Checkpoints")
cols = st.columns(4)
for i, c in enumerate(CHECKPOINTS):
    with cols[i % 4]:
        kg = weight_near(c)
        caption = f"{label(c)} · {c:%d %b}" + (f" · {kg:.1f} kg" if kg else "")
        if photo_path(c).exists():
            st.image(str(photo_path(c)), caption=caption, use_container_width=True)
            if st.button("Delete", key=f"del_{c}"):
                photo_path(c).unlink()
                st.rerun()
        else:
            status = "Due now" if c == due else ("Missed" if c < today else f"Due {c:%d %b}")
            st.markdown(f"**{label(c)}** · {c:%d %b}  \n:grey[{status}]")
