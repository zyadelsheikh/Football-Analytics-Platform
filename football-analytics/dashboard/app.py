import streamlit as st

from data import load_denormalized, search_entities, player_latest_context, team_latest_context
from pages_lib import home, player_season, team_season, league_ranking

st.set_page_config(page_title="Football Analytics", page_icon="⚽", layout="wide")

CUSTOM_CSS = """
<style>
.block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
[data-testid="stMetric"] {
    background-color: rgba(45, 212, 191, 0.06);
    border: 1px solid rgba(45, 212, 191, 0.18);
    border-radius: 10px;
    padding: 10px 14px;
}
[data-testid="stMetricLabel"] {opacity: 0.75; font-size: 0.8rem;}
[data-testid="stMetricValue"] {font-size: 1.35rem;}
section[data-testid="stSidebar"] {border-right: 1px solid rgba(255,255,255,0.06);}
.search-hit-btn button {width: 100%; text-align: left;}
hr {margin: 0.6rem 0;}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def _go_to_player(player_name: str, latest: dict):
    st.session_state["nav_page"] = "Player Season"
    st.session_state["ps_league"] = latest["league"]
    st.session_state["ps_season"] = latest["season"]
    st.session_state["ps_team"] = "All Teams"
    st.session_state["ps_min_minutes"] = 0
    st.session_state["ps_player"] = player_name
    st.session_state["ps_compare_toggle"] = False
    st.session_state["global_search"] = ""


def _go_to_team(team_name: str, latest: dict):
    st.session_state["nav_page"] = "Team Season"
    st.session_state["ts_league"] = latest["league"]
    st.session_state["ts_season"] = latest["season"]
    st.session_state["ts_team"] = team_name
    st.session_state["global_search"] = ""


df = load_denormalized()

if df.empty:
    st.error("No data found. Run prj_fixed.ipynb first to generate the processed/*.csv files.")
    st.stop()

if "nav_page" not in st.session_state:
    st.session_state["nav_page"] = "Home"

with st.sidebar:
    st.markdown("## ⚽ Football Analytics")

    query = st.text_input("Quick search — player or team", key="global_search", placeholder="e.g. Messi, Arsenal…")
    if query:
        matching_players, matching_teams = search_entities(df, query)
        if not matching_players and not matching_teams:
            st.caption("No matches.")
        for p in matching_players:
            st.button(f"🧑 {p}", key=f"hit_player_{p}", on_click=_go_to_player, args=(p, player_latest_context(df, p)))
        for t in matching_teams:
            st.button(f"🛡️ {t}", key=f"hit_team_{t}", on_click=_go_to_team, args=(t, team_latest_context(df, t)))
        st.divider()

    page = st.radio(
        "Navigate",
        ["Home", "Player Season", "Team Season", "League Ranking"],
        key="nav_page",
        label_visibility="collapsed",
    )
    st.caption("Top-5 European leagues, 2017-2026")

if page == "Home":
    home.render(df)
elif page == "Player Season":
    player_season.render(df)
elif page == "Team Season":
    team_season.render(df)
elif page == "League Ranking":
    league_ranking.render(df)
