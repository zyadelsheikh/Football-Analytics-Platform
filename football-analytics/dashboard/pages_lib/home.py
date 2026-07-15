import pandas as pd
import plotly.express as px
import streamlit as st

from pages_lib.filters import season_league_filters, export_buttons


def render(df: pd.DataFrame):
    with st.sidebar:
        pool, league, season, _ = season_league_filters(df, "home")

    st.markdown("## 📈 Performance Overview")
    st.caption(f"{league} · {season}")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Players", pool["player"].nunique())
    c2.metric("Teams", pool["team"].nunique())
    c3.metric("Total Goals", int(pool["Goals"].sum()))
    c4.metric("Total Assists", int(pool["Assists"].sum()))
    avg_age = pool["Age"].mean()
    c5.metric("Avg. Age", f"{avg_age:.1f}" if pd.notna(avg_age) else "—")

    st.divider()

    left, right = st.columns(2)

    with left:
        st.markdown("#### 🥇 Top Scorers")
        top_scorers = (
            pool[["player", "team", "Goals"]]
            .sort_values("Goals", ascending=False)
            .head(10)
        )
        if top_scorers["Goals"].sum() > 0:
            fig = px.bar(
                top_scorers.sort_values("Goals"),
                x="Goals", y="player", orientation="h",
                hover_data=["team"],
                color_discrete_sequence=["#2dd4bf"],
            )
            fig.update_layout(yaxis_title="", height=380, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("No goal data for this competition / season.")

    with right:
        st.markdown("#### 🎯 Top Assisters")
        top_assists = (
            pool[["player", "team", "Assists"]]
            .sort_values("Assists", ascending=False)
            .head(10)
        )
        if top_assists["Assists"].sum() > 0:
            fig = px.bar(
                top_assists.sort_values("Assists"),
                x="Assists", y="player", orientation="h",
                hover_data=["team"],
                color_discrete_sequence=["#38bdf8"],
            )
            fig.update_layout(yaxis_title="", height=380, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("No assist data for this competition / season.")

    st.divider()

    st.markdown("#### ⚽ Goals by Team")
    team_goals = pool.groupby("team", as_index=False)["Goals"].sum().sort_values("Goals", ascending=False)
    if team_goals["Goals"].sum() > 0:
        fig = px.bar(
            team_goals, x="team", y="Goals",
            color_discrete_sequence=["#2dd4bf"],
        )
        fig.update_layout(xaxis_title="", height=380, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("No goal data for this competition / season.")

    with st.expander("View / export raw table for this competition & season"):
        st.dataframe(pool, width="stretch", hide_index=True)
        export_buttons(pool, f"overview_{league}_{season}".replace(" ", "_"), "home")
