"""
charts.py - the Plotly charts used on the dashboard pages.

Colours are chosen once here so every chart looks the same:
  blue   = the thing you logged
  orange = the smoothed / average line
  grey   = the target or reference line
  green  = a new personal best
"""

from datetime import timedelta

import plotly.graph_objects as go

import plan

BLUE = "#2a78d6"
ORANGE = "#eb6834"
GREY = "#8a8983"
GREEN = "#0ca30c"
GRID = "rgba(128,128,128,0.15)"


def _tidy(fig, y_title):
    """Shared layout so every chart looks the same."""
    fig.update_layout(
        margin=dict(l=10, r=10, t=30, b=10),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        yaxis_title=y_title,
        xaxis_title=None,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(showgrid=False, showline=True, linecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zeroline=False)
    return fig


def bodyweight_chart(table):
    """Daily weigh-ins, the 7-day average and the +0.25 kg/week target line."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=table["date"], y=table["weight_kg"], name="Daily weigh-in",
        mode="markers", marker=dict(color=BLUE, size=8),
        hovertemplate="%{y:.1f} kg<extra>Daily</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=table["date"], y=table["avg_7d"], name="7-day average",
        mode="lines", line=dict(color=ORANGE, width=2),
        hovertemplate="%{y:.2f} kg<extra>7-day avg</extra>",
    ))
    # Draw the target line all the way to New Year so you can see the path ahead.
    first_day = min(table["date"].min(), plan.PLAN_START)
    target_days = [first_day + timedelta(days=i) for i in range((plan.PLAN_END - first_day).days + 1)]
    fig.add_trace(go.Scatter(
        x=target_days, y=[plan.target_weight(d) for d in target_days], name="Target (+0.25 kg/week)",
        mode="lines", line=dict(color=GREY, width=2, dash="dash"),
        hovertemplate="%{y:.2f} kg<extra>Target</extra>",
    ))

    # Mark the start of the plan.
    fig.add_vline(x=plan.PLAN_START, line=dict(color=GRID, width=1))
    fig.add_annotation(x=plan.PLAN_START, y=1, yref="paper", text="Plan starts",
                       showarrow=False, xanchor="left", yanchor="bottom", font=dict(size=11, color=GREY))

    return _tidy(fig, "Bodyweight (kg)")


def exercise_chart(top, exercise, metric="weight_kg"):
    """Top set over time for one exercise, with new bests marked in green."""
    df = top[top["exercise"] == exercise].sort_values("date")
    label = "Top set (kg)" if metric == "weight_kg" else "Estimated 1RM (kg)"

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"], y=df[metric], name=label,
        mode="lines+markers", line=dict(color=BLUE, width=2), marker=dict(size=8),
        customdata=df[["weight_kg", "reps"]],
        hovertemplate="%{customdata[0]:.1f} kg x %{customdata[1]:.0f} reps<extra></extra>",
    ))

    pbs = df[df["is_pb"]]
    if not pbs.empty:
        fig.add_trace(go.Scatter(
            x=pbs["date"], y=pbs[metric], name="New best",
            mode="markers+text", text=["PB"] * len(pbs), textposition="top center",
            marker=dict(color=GREEN, size=13, symbol="star",
                        line=dict(color="white", width=2)),
            hoverinfo="skip",
        ))

    return _tidy(fig, label)


AQUA = "#1baf7a"


def volume_chart(volume):
    """Grouped bars: sets per week for Push, Pull and Legs."""
    df = volume[(volume["Push"] + volume["Pull"] + volume["Legs"]) > 0]
    labels = [f"Wk {w}" for w in df["Week"]]
    fig = go.Figure()
    for name, color in (("Push", BLUE), ("Pull", ORANGE), ("Legs", AQUA)):
        fig.add_trace(go.Bar(x=labels, y=df[name], name=name, marker=dict(color=color),
                             hovertemplate="%{y} sets<extra>" + name + "</extra>"))
    fig.update_layout(barmode="group", bargap=0.25)
    return _tidy(fig, "Sets per week")


def weekly_change_chart(review):
    """Bar per week: how much the weekly average moved, against the 0.25 kg target."""
    df = review.dropna(subset=["Change (kg)"])
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[f"Wk {w}" for w in df["Week"]], y=df["Change (kg)"], name="Weekly change",
        marker=dict(color=BLUE), width=0.5,
        hovertemplate="%{y:+.2f} kg<extra></extra>",
    ))
    fig.add_hline(y=plan.TARGET_GAIN_PER_WEEK_KG, line=dict(color=GREY, width=2, dash="dash"),
                  annotation_text="Target +0.25 kg", annotation_position="top left")
    return _tidy(fig, "Change vs previous week (kg)")
