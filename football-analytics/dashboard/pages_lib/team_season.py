import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from data import metric_has_data, team_trend, team_metric_totals
from pages_lib.filters import (
    season_league_filters, export_buttons, any_league_team_multiselect,
)

COMPARE_METRICS = ["Goals", "Assists", "Minutes_Played"]
ADVANCED_TEAM_METRICS = [
    ("Expected_Goals", "Total xG"), ("Shots", "Total Shots"),
    ("Key_Passes", "Total Key Passes"), ("Tackles", "Total Tackles"),
]
TREND_METRICS = ["Goals", "Assists"]


def render(full_df: pd.DataFrame):
    with st.sidebar:
        pool, league, season, season_id = season_league_filters(full_df, "ts")
        st.markdown("### Team Selection")
        teams = sorted(pool["team"].dropna().unique())
        if not teams:
            st.warning("No teams found for this competition / season.")
            return
        team = st.selectbox("Select Team", teams, key="ts_team")
        st.caption(f"{len(teams)} teams in this competition")

        st.markdown("### Compare")
        compare_teams = any_league_team_multiselect(full_df, team, "ts")

    squad = pool[pool["team"] == team]
    if squad.empty:
        st.warning("No team data available for this competition / season.")
        return

    st.markdown(f"## {team}")
    st.caption(f"{league} · {season}")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Squad Size", squad["player"].nunique())
    c2.metric("Goals", int(squad["Goals"].sum()))
    c3.metric("Assists", int(squad["Assists"].sum()))
    avg_age = squad["Age"].mean()
    c4.metric("Avg Age", f"{avg_age:.1f}" if pd.notna(avg_age) else "—")
    total_min = int(squad["Minutes_Played"].sum())
    c5.metric("Total Minutes", f"{total_min:,}")

    if metric_has_data(squad, "Expected_Goals"):
        st.markdown("#### Team Stats Breakdown")
        cols = st.columns(len(ADVANCED_TEAM_METRICS))
        for i, (col, label) in enumerate(ADVANCED_TEAM_METRICS):
            total = squad[col].sum() if col in squad.columns else np.nan
            cols[i].metric(label, f"{total:.0f}" if pd.notna(total) else "—")

    st.divider()

    st.markdown("#### Top Scorers")
    top = squad.sort_values("Goals", ascending=False).head(10)
    if top["Goals"].sum() > 0:
        fig = px.bar(
            top, x="Goals", y="player", orientation="h",
            labels={"player": "", "Goals": "Goals"},
            color_discrete_sequence=["#2dd4bf"],
        )
        fig.update_layout(yaxis=dict(categoryorder="total ascending"), height=350, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("No goal data available for this squad in this season.")

    if compare_teams:
        st.divider()
        st.markdown(f"#### 🆚 Team Comparison — {team} vs {', '.join(compare_teams)}")
        st.caption("Compared using the same season as the primary team, regardless of league.")
        all_teams = [team] + compare_teams
        summary = team_metric_totals(full_df, all_teams, season_id, COMPARE_METRICS)
        if summary.empty:
            st.info("No overlapping season data found for the selected teams.")
        else:
            summary = summary.set_index("team").reindex(all_teams).reset_index()
            melted = summary.melt(id_vars="team", var_name="Metric", value_name="Total")
            fig = px.bar(
                melted, x="Metric", y="Total", color="team", barmode="group",
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig.update_layout(height=380, margin=dict(l=10, r=10, t=20, b=10), legend_title="")
            st.plotly_chart(fig, width="stretch")
            st.dataframe(summary, width="stretch", hide_index=True)

    st.divider()
    st.markdown(f"#### 📈 {team} — Trend Across Seasons")
    trend_metrics = [m for m in TREND_METRICS if metric_has_data(full_df, m)]
    trend_df = team_trend(full_df, team, trend_metrics)
    if len(trend_df) >= 2:
        fig = px.line(
            trend_df, x="season", y=trend_metrics, markers=True,
            labels={"value": "Total", "season": "Season", "variable": "Metric"},
        )
        fig.update_layout(height=350, margin=dict(l=10, r=10, t=20, b=10), legend_title="")
        st.plotly_chart(fig, width="stretch")
    else:
        st.info(f"{team} only has one season on record — nothing to trend yet.")

    st.divider()
    st.markdown("#### Full Squad")
    display_cols = ["player", "Pos", "Age", "Nation", "Matches_Played", "Minutes_Played", "Goals", "Assists"]
    if metric_has_data(squad, "Expected_Goals"):
        display_cols += ["Expected_Goals", "Expected_Assists"]
    squad_table = squad[display_cols].sort_values("Minutes_Played", ascending=False)
    st.dataframe(squad_table, width="stretch", hide_index=True)
    export_buttons(squad_table, f"{team.replace(' ', '_')}_{season}_squad", "ts")
