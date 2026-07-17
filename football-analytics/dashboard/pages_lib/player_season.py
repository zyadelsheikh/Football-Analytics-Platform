import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data import (
    RADAR_DEFAULT_METRICS, per90, percentile_rank, metric_has_data, player_trend,
)
from pages_lib.filters import (
    season_league_filters, min_minutes_filter, team_filter,
    any_league_season_player_picker, export_buttons,
)

STAT_CARDS = [
    ("Goals", "Goals"), ("Assists", "Assists"),
    ("Expected_Goals", "xG"), ("Expected_Assists", "xA"),
    ("Shots", "Shots"), ("Shots_On_Target", "SoT"),
    ("Key_Passes", "Key Passes"), ("Tackles", "Tackles"),
    ("Interceptions", "Interceptions"), ("xg_diff", "G - xG"),
]

EXTRA_STAT_CARDS = [
    ("pass_accuracy", "Pass Accuracy %"),
    ("shot_accuracy", "Shot Accuracy %"),
    ("goals_per90", "Goals / 90"),
    ("assists_per90", "Assists / 90"),
]

TREND_METRICS = ["Goals", "Assists", "Expected_Goals", "Expected_Assists"]


def _with_extra_stats(row: pd.Series) -> dict:
    extra = {}
    pass_att, pass_cmp = row.get("Pass_Attempts"), row.get("Pass_Completed")
    extra["pass_accuracy"] = (pass_cmp / pass_att * 100) if pass_att and pd.notna(pass_att) and pass_att > 0 else np.nan
    shots, sot = row.get("Shots"), row.get("Shots_On_Target")
    extra["shot_accuracy"] = (sot / shots * 100) if shots and pd.notna(shots) and shots > 0 else np.nan
    nineties = row.get("Full_Match_Equivalents")
    extra["goals_per90"] = (row.get("Goals", np.nan) / nineties) if nineties and pd.notna(nineties) and nineties > 0 else np.nan
    extra["assists_per90"] = (row.get("Assists", np.nan) / nineties) if nineties and pd.notna(nineties) and nineties > 0 else np.nan
    return extra


def _render_header(player, league, season, row):

    st.markdown(f"# {player}")
    st.caption(f"{row['team']} · {league} · {season}")

    pos = row.get("Pos", "—")
    nation = row.get("Nation", "—")
    born = row.get("Born", "—")

    st.caption(
        f"🌍 {nation} · 🎂 Born {int(born) if pd.notna(born) else '—'} · Position: {pos}"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric("Minutes", f"{int(row['Minutes_Played']):,}")

    with c2:
        st.metric("Apps", int(row["Matches_Played"]))

    with c3:
        avg_min = (
            row["Minutes_Played"] / row["Matches_Played"]
            if row["Matches_Played"]
            else 0
        )
        st.metric("Avg Min", f"{avg_min:.0f}")

    with c4:
        st.metric(
            "90s",
            f"{row['Full_Match_Equivalents']:.1f}"
            if pd.notna(row["Full_Match_Equivalents"])
            else "—"
        )

    st.divider()
    st.markdown(f"#### 📈 {player} — Performance Trend Across Seasons")
    trend_metrics = [m for m in TREND_METRICS if metric_has_data(full_df, m)]
    trend_df = player_trend(full_df, player, trend_metrics)
    if len(trend_df) >= 2:
        fig = px.line(
            trend_df, x="season", y=trend_metrics, markers=True,
            labels={"value": "Total", "season": "Season", "variable": "Metric"},
        )
        fig.update_layout(height=380, margin=dict(l=10, r=10, t=20, b=10), legend_title="")
        st.plotly_chart(fig, width="stretch")
    else:
        st.info(f"{player} only has one season on record — nothing to trend yet.")

    st.divider()
    st.markdown("#### 📋 Season-by-Season Log")
    log_cols = [
        "season", "league", "team", "Pos", "Age", "Matches_Played", "Minutes_Played",
        "Goals", "Assists",
    ]
    if metric_has_data(full_df, "Expected_Goals"):
        log_cols += ["Expected_Goals", "Expected_Assists", "Shots", "Key_Passes", "Tackles"]
    player_rows = full_df[full_df["player"] == player].sort_values("season_id")
    st.dataframe(player_rows[log_cols], width="stretch", hide_index=True)
    export_buttons(player_rows, f"{player.replace(' ', '_')}_stats", "ps")


def _render_header(player, league, season, row):
    c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])
    with c1:
        st.markdown(f"## {player}")
        st.caption(f"{row['team']} · {league} · {season}")
        pos = row.get("Pos", "—")
        nation = row.get("Nation", "—")
        born = row.get("Born", "—")
        st.caption(f"🌍 {nation}  ·  🎂 Born {int(born) if pd.notna(born) else '—'}  ·  Position: {pos}")
    c2.metric("Minutes", f"{int(row['Minutes_Played']):,}")
    c3.metric("Apps", int(row["Matches_Played"]))
    avg_min = row["Minutes_Played"] / row["Matches_Played"] if row["Matches_Played"] else 0
    c4.metric("Avg Min", f"{avg_min:.0f}")
    c5.metric("90s", f"{row['Full_Match_Equivalents']:.1f}" if pd.notna(row["Full_Match_Equivalents"]) else "—")


def _render_compare_table(pool: pd.DataFrame, player: str, compare_pool: pd.DataFrame, compare_player: str):
    st.markdown("#### Head-to-Head")
    row_a = pool[pool["player"] == player].iloc[0]
    row_b = compare_pool[compare_pool["player"] == compare_player].iloc[0]
    data = {
        "Stat": [label for _, label in STAT_CARDS],
        player: [row_a.get(col, np.nan) for col, _ in STAT_CARDS],
        compare_player: [row_b.get(col, np.nan) for col, _ in STAT_CARDS],
    }
    table = pd.DataFrame(data)
    st.dataframe(table, width="stretch", hide_index=True)


def _build_radar(pool: pd.DataFrame, player: str, metrics: list, compare_pool: pd.DataFrame = None, compare_player: str = None):
    def values_for(name, ref_pool):
        vals = []
        for m in metrics:
            if not metric_has_data(ref_pool, m):
                vals.append(0)
                continue
            pct_series = percentile_rank(per90(ref_pool, m))
            idx = ref_pool.index[ref_pool["player"] == name]
            this_pct = pct_series.loc[idx].mean() if len(idx) else np.nan
            vals.append(0 if pd.isna(this_pct) else round(this_pct, 1))
        return vals

    labels = [m.replace("_", " ") for m in metrics]
    values = values_for(player, pool)

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]], theta=labels + [labels[0]],
        fill="toself", name=player, line_color="#2dd4bf",
    ))

    if compare_player and compare_pool is not None:
        cmp_values = values_for(compare_player, compare_pool)
        fig.add_trace(go.Scatterpolar(
            r=cmp_values + [cmp_values[0]], theta=labels + [labels[0]],
            fill="toself", name=compare_player, line_color="#f97316",
            opacity=0.7,
        ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=bool(compare_player),
        legend=dict(orientation="h", yanchor="bottom", y=-0.15),
        margin=dict(l=40, r=40, t=20, b=20),
        height=420,
    )
    return fig
