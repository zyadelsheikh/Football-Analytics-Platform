import pandas as pd
import streamlit as st

from data import seasons_sorted


def season_league_filters(df: pd.DataFrame, key_prefix: str):
    """Renders Competition + Season selectors (single season only).

    Returns (filtered_pool, league, season, season_id) -- season_id lets
    callers look up the same season across OTHER leagues (used for
    cross-league team comparisons).
    """
    st.markdown("### Data Filters")

    league_key = f"{key_prefix}_league"
    season_key = f"{key_prefix}_season"

    leagues = sorted(df["league"].dropna().unique())
    league = st.selectbox("Competition", leagues, key=league_key)

    season_lookup = seasons_sorted(df[df["league"] == league])
    season_options = season_lookup["season"].tolist()

    if season_key in st.session_state and st.session_state[season_key] in season_options:
        season = st.selectbox("Season", season_options, key=season_key)
    else:
        season = st.selectbox("Season", season_options, index=len(season_options) - 1, key=season_key)

    season_id = int(season_lookup.loc[season_lookup["season"] == season, "season_id"].iloc[0])
    filtered = df[(df["league"] == league) & (df["season"] == season)]
    return filtered, league, season, season_id


def min_minutes_filter(df: pd.DataFrame, key_prefix: str):
    key = f"{key_prefix}_min_minutes"
    max_minutes = int(df["Minutes_Played"].max()) if not df.empty else 0
    if key in st.session_state:
        min_minutes = st.slider("Min. Minutes Played", 0, max(max_minutes, 90), step=10, key=key)
    else:
        min_minutes = st.slider(
            "Min. Minutes Played", 0, max(max_minutes, 90), min(500, max_minutes),
            step=10, key=key,
        )
    return df[df["Minutes_Played"] >= min_minutes]


def team_filter(df: pd.DataFrame, key_prefix: str):
    teams = ["All Teams"] + sorted(df["team"].dropna().unique().tolist())
    team = st.selectbox("Team", teams, key=f"{key_prefix}_team")
    if team != "All Teams":
        df = df[df["team"] == team]
    st.caption(f"{df['player'].nunique()} players found")
    return df, team


def any_league_season_player_picker(full_df: pd.DataFrame, key_prefix: str, label: str = "Compare with"):
    """A self-contained League + Season + Player picker sourced from the
    FULL dataset (not the current page's filtered pool) -- lets the user
    compare against any player from any league/season.

    Returns (player_name, its_own_peer_pool) or (None, None).
    """
    leagues = sorted(full_df["league"].dropna().unique())
    league = st.selectbox("Compare League", leagues, key=f"{key_prefix}_league")

    season_lookup = seasons_sorted(full_df[full_df["league"] == league])
    season_options = season_lookup["season"].tolist()
    season = st.selectbox("Compare Season", season_options, index=len(season_options) - 1, key=f"{key_prefix}_season")

    peer_pool = full_df[(full_df["league"] == league) & (full_df["season"] == season)]
    players = sorted(peer_pool["player"].dropna().unique())
    if not players:
        st.caption("No players found for that league/season.")
        return None, None

    player = st.selectbox(label, players, key=f"{key_prefix}_player")
    return player, peer_pool


def any_league_team_multiselect(full_df: pd.DataFrame, exclude_team: str, key_prefix: str):
    """Team multiselect sourced from ALL leagues (not just the current
    page's league), so you can compare teams across competitions."""
    teams = sorted(t for t in full_df["team"].dropna().unique() if t != exclude_team)
    return st.multiselect("Add teams to compare (any league)", teams, key=f"{key_prefix}_compare_teams")


def export_buttons(df: pd.DataFrame, filename_prefix: str, key_prefix: str):
    """Renders CSV + Excel download buttons for the given table."""
    from data import to_csv_bytes, to_excel_bytes

    c1, c2 = st.columns(2)
    c1.download_button(
        "⬇️ Download CSV", data=to_csv_bytes(df),
        file_name=f"{filename_prefix}.csv", mime="text/csv",
        key=f"{key_prefix}_csv", width="stretch",
    )
    c2.download_button(
        "⬇️ Download Excel", data=to_excel_bytes(df, sheet_name=filename_prefix[:31]),
        file_name=f"{filename_prefix}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=f"{key_prefix}_xlsx", width="stretch",
    )
