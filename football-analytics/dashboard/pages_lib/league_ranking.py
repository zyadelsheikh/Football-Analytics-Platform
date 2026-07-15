import pandas as pd
import plotly.express as px
import streamlit as st

from data import METRIC_GROUPS, per90, metric_has_data
from pages_lib.filters import season_league_filters, min_minutes_filter, export_buttons


def render(df: pd.DataFrame):
    with st.sidebar:
        pool, league, season, _ = season_league_filters(df, "lr")
        pool = min_minutes_filter(pool, "lr")

    st.markdown("## 🏆 League Ranking")

    c1, c2, c3, c4 = st.columns([1.2, 1.2, 1, 1])
    with c1:
        group = st.selectbox("Metric Group", list(METRIC_GROUPS.keys()), key="lr_group")
    with c2:
        metric_options = [m for m in METRIC_GROUPS[group] if metric_has_data(pool, m)]
        if not metric_options:
            st.warning(f"No data available for the '{group}' metrics in {season} ({league}).")
            return
        metric = st.selectbox("Metric", metric_options, key="lr_metric")
    with c3:
        show_n = st.slider("Show N Players", 5, 50, 20, key="lr_n")
    with c4:
        ascending = st.toggle("Ascending", value=False, key="lr_asc")

    positions = sorted(pool["Pos"].dropna().unique())
    selected_pos = st.multiselect("Position Filter (applied after ranking)", positions, key="lr_pos")

    pool = pool.copy()
    pool["metric_p90"] = per90(pool, metric)
    ranked = pool.dropna(subset=["metric_p90"]).sort_values("metric_p90", ascending=ascending)

    if selected_pos:
        ranked = ranked[ranked["Pos"].isin(selected_pos)]

    ranked = ranked.head(show_n)

    if ranked.empty:
        st.info("No players match these filters.")
        return

    fig = px.bar(
        ranked.sort_values("metric_p90"),
        x="metric_p90", y="player", orientation="h",
        text="metric_p90",
        labels={"metric_p90": f"{metric.replace('_', ' ')} p90", "player": ""},
        title=f"League Ranking — {metric.replace('_', ' ')} p90 ({season}, {league})",
    )
    fig.update_traces(texttemplate="%{text:.2f}", textposition="outside", marker_color="#2dd4bf")
    fig.update_layout(height=max(400, 20 * len(ranked)), margin=dict(l=10, r=10, t=60, b=10))
    st.plotly_chart(fig, width='stretch')

    with st.expander("View underlying data"):
        ranking_table = (
            ranked[["player", "team", "Pos", "Age", "Minutes_Played", metric, "metric_p90"]]
            .rename(columns={"metric_p90": f"{metric}_p90"})
        )
        st.dataframe(ranking_table, width="stretch")
        export_buttons(ranking_table, f"league_ranking_{metric}_{season}".replace(" ", "_"), "lr")
