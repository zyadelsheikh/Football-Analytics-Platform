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


def render(full_df: pd.DataFrame):
    with st.sidebar:
        pool, league, season, _ = season_league_filters(full_df, "ps")
        pool = min_minutes_filter(pool, "ps")
        st.markdown("### Player Selection")
        pool, team = team_filter(pool, "ps")

        players = sorted(pool["player"].dropna().unique())
        if not players:
            st.warning("No players match these filters.")
            return
        player = st.selectbox("Select Player", players, key="ps_player")

        compare_on = st.toggle("Compare Player", value=False, key="ps_compare_toggle")
        compare_player, compare_pool = None, None
        if compare_on:
            st.caption("Compare against any player, from any league/season:")
            compare_player, compare_pool = any_league_season_player_picker(full_df, "ps_cmp")

    row = pool[pool["player"] == player]
    if row.empty:
        st.warning("No player data available for this competition / season.")
        return
    row = row.iloc[0]

    _render_header(player, league, season, row)
    st.divider()

    advanced_available = metric_has_data(pool, "Expected_Goals")
    if not advanced_available:
        st.warning(
            f"Advanced stats (xG, xA, Shots, Progressive actions, Tackles, etc.) are not available "
            f"in the source data for **{season}** — the 2025-2026 file only contains basic counting "
            f"stats (Goals, Assists, Minutes). Showing what's available below."
        )

    left, right = st.columns([1.1, 1])

    with left:
        st.markdown("#### Attribute Radar (percentile rank)")
        metrics = [m for m in RADAR_DEFAULT_METRICS if metric_has_data(pool, m)]
        if len(metrics) >= 3:
            fig = _build_radar(pool, player, metrics, compare_pool, compare_player)
            st.plotly_chart(fig, width="stretch")
            if compare_player:
                st.caption(
                    "Each player's percentile is computed against **their own** league/season "
                    "peer group — this keeps a cross-league comparison fair instead of mixing "
                    "two different competition levels into one ranking."
                )
        else:
            st.info("Not enough metrics with data in this season to draw a radar chart.")

    with right:
        if compare_player and compare_pool is not None:
            _render_compare_table(pool, player, compare_pool, compare_player)
        else:
            st.markdown("#### Key Stats Overview")
            cols = st.columns(2)
            for i, (col, label) in enumerate(STAT_CARDS):
                val = row.get(col, np.nan)
                display = f"{val:.2f}" 
                cols[i % 2].metric(label, display)

            st.markdown("#### Extra Stats")
            extra = _with_extra_stats(row)
            cols2 = st.columns(2)
            for i, (key, label) in enumerate(EXTRA_STAT_CARDS):
                val = extra.get(key, np.nan)
                display = f"{val:.1f}" if pd.notna(val) else "—"
                cols2[i % 2].metric(label, display)

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
