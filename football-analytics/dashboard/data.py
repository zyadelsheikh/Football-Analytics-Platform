"""
Data access layer for the Football Analytics dashboard.

Reads the star-schema CSVs produced by prj_fixed.ipynb (dim_player, dim_team,
dim_league, dim_season, fact_player_stats) and exposes a single denormalized
view for the UI to filter on, plus small helpers for per-90 metrics and
percentile ranks.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).parent / "processed"

# Base counting stats available for every row (2017-2018 .. 2025-2026)
CORE_METRICS = [
    "Goals", "Assists", "Goal_Contributions",
    "Matches_Played", "Matches_Started", "Minutes_Played",
]

# Advanced stats that only exist for the 2017-2024 seasons (missing entirely
# from the 2025-2026 source file). Kept separate so the UI can warn instead
# of silently showing blank charts.
ADVANCED_METRICS = [
    "Expected_Goals", "Expected_Assists", "NonPenalty_Expected_Goals",
    "Shots", "Shots_On_Target",
    "Progressive_Carries", "Progressive_Passes", "Touches",
    "Key_Passes", "Pass_Attempts", "Pass_Completed",
    "Shot_Creating_Actions", "Goal_Creating_Actions",
    "Tackles", "Interceptions", "Blocks",
    "xg_diff", "xa_diff", "progressive_actions", "defensive_index",
]

METRIC_GROUPS = {
    "Attacking": ["Goals", "Assists", "Goal_Contributions", "Expected_Goals",
                  "Expected_Assists", "Shots", "Shots_On_Target", "xg_diff"],
    "Passing": ["Key_Passes", "Pass_Attempts", "Pass_Completed", "Progressive_Passes"],
    "Dribbling & Carrying": ["Progressive_Carries", "Touches", "progressive_actions"],
    "Defending": ["Tackles", "Interceptions", "Blocks", "defensive_index"],
    "Creation": ["Shot_Creating_Actions", "Goal_Creating_Actions"],
}

RADAR_DEFAULT_METRICS = [
    "Goals", "Assists", "Expected_Goals", "Expected_Assists",
    "Shots", "Key_Passes", "Progressive_Carries", "Tackles",
]


def _get_data_source() -> str:
    """'local' (default, reads processed/*.csv) or 'azure' (reads Synapse
    tables via db.py). Controlled by data_source in .streamlit/secrets.toml
    -- if that file doesn't exist at all, we safely fall back to 'local'."""
    try:
        return st.secrets.get("data_source", "local")
    except Exception:
        return "local"


@st.cache_data
def load_star_schema():
    if _get_data_source() == "azure":
        from db import load_star_schema_from_azure
        try:
            return load_star_schema_from_azure()
        except Exception as e:
            st.error(
                "**Couldn't connect to Azure Synapse.** Check "
                "`.streamlit/secrets.toml` — most likely the password still "
                "needs to be filled in, or the server/database/username has "
                "a typo.\n\n"
                f"Technical detail: `{e}`"
            )
            st.stop()

    dim_player = pd.read_csv(DATA_DIR / "dim_player.csv")
    dim_team = pd.read_csv(DATA_DIR / "dim_team.csv")
    dim_league = pd.read_csv(DATA_DIR / "dim_league.csv")
    dim_season = pd.read_csv(DATA_DIR / "dim_season.csv")
    fact = pd.read_csv(DATA_DIR / "fact_player_stats.csv")
    return dim_player, dim_team, dim_league, dim_season, fact


@st.cache_data
def load_denormalized():
    """Join the fact table back to its dimensions for easy filtering/display."""
    dim_player, dim_team, dim_league, dim_season, fact = load_star_schema()

    df = (
        fact
        .merge(dim_player, on="player_id", how="left")
        .merge(dim_team, on="team_id", how="left")
        .merge(dim_league, on="league_id", how="left")
        .merge(dim_season, on="season_id", how="left")
    )
    return df


def per90(df: pd.DataFrame, col: str) -> pd.Series:
    """Value per 90 minutes (Full_Match_Equivalents). NaN-safe."""
    denom = df["Full_Match_Equivalents"].replace(0, np.nan)
    return df[col] / denom


def percentile_rank(series: pd.Series) -> pd.Series:
    """0-100 percentile rank within the given series, NaN-safe."""
    return series.rank(pct=True, na_option="keep") * 100


def metric_has_data(df: pd.DataFrame, col: str) -> bool:
    return col in df.columns and df[col].notna().any()


def search_entities(df: pd.DataFrame, query: str, limit: int = 5):
    """Case-insensitive substring search across player and team names.

    Returns (matching_players, matching_teams), each a list of up to `limit`
    unique names.
    """
    query = (query or "").strip().lower()
    if not query:
        return [], []

    players = df["player"].dropna().unique()
    teams = df["team"].dropna().unique()

    matching_players = sorted([p for p in players if query in p.lower()])[:limit]
    matching_teams = sorted([t for t in teams if query in t.lower()])[:limit]
    return matching_players, matching_teams


def player_latest_context(df: pd.DataFrame, player: str):
    """League/season/team of a player's most recent season on record."""
    rows = df[df["player"] == player]
    if rows.empty:
        return None
    latest = rows.loc[rows["season_id"].idxmax()]
    return {"league": latest["league"], "season": latest["season"], "team": latest["team"]}


def team_latest_context(df: pd.DataFrame, team: str):
    """League/season of a team's most recent season on record."""
    rows = df[df["team"] == team]
    if rows.empty:
        return None
    latest = rows.loc[rows["season_id"].idxmax()]
    return {"league": latest["league"], "season": latest["season"]}


def player_trend(df: pd.DataFrame, player: str, metrics: list) -> pd.DataFrame:
    """Season-by-season totals for a player across every season on record
    (sums across teams/leagues in case of a mid-season transfer)."""
    rows = df[df["player"] == player]
    if rows.empty:
        return pd.DataFrame(columns=["season", "season_id"] + metrics)
    agg = rows.groupby(["season_id", "season"], as_index=False)[metrics].sum(min_count=1)
    return agg.sort_values("season_id")


def team_trend(df: pd.DataFrame, team: str, metrics: list) -> pd.DataFrame:
    """Season-by-season totals for a team (squad-wide sums) across every
    season on record."""
    rows = df[df["team"] == team]
    if rows.empty:
        return pd.DataFrame(columns=["season", "season_id"] + metrics)
    agg = rows.groupby(["season_id", "season"], as_index=False)[metrics].sum(min_count=1)
    return agg.sort_values("season_id")


def seasons_sorted(df: pd.DataFrame) -> pd.DataFrame:
    """Unique (season_id, season) pairs sorted chronologically."""
    return (
        df[["season_id", "season"]]
        .drop_duplicates()
        .sort_values("season_id")
        .reset_index(drop=True)
    )


def team_metric_totals(df: pd.DataFrame, teams: list, season_id: int, metrics: list) -> pd.DataFrame:
    """Summed metrics for a list of teams (any league) within a single
    season. Used for cross-league team comparisons."""
    subset = df[df["team"].isin(teams) & (df["season_id"] == season_id)]
    cols = [c for c in metrics if c in subset.columns]
    if subset.empty:
        return pd.DataFrame(columns=["team"] + cols)
    return subset.groupby("team", as_index=False)[cols].sum(min_count=1)


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Sheet1") -> bytes:
    from io import BytesIO
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return buffer.getvalue()
