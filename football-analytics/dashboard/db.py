"""
Azure Synapse connection layer.

Credentials are read from `.streamlit/secrets.toml` (see
`.streamlit/secrets.toml.example`) -- NEVER hardcode them in source code.

IMPORTANT: the real tables on Synapse use different names/columns than the
local processed/*.csv star schema (PascalCase, PlayerID/TeamID/etc., extra
columns like Height_cm, and it's missing a few columns the local CSVs have:
Key_Passes, Pass_Attempts, Pass_Completed, Touches, Carries).

Rather than rewrite every page to know two different column-naming
conventions, we translate at the SQL boundary: every query below aliases
Synapse's real column names (AS ...) into the exact same internal names
`data.py` / the pages already use (player_id, player, Nation, Born,
xg_diff, defensive_index, progressive_actions, ...). This is the ONLY
place that needs to know about Synapse's actual schema.
"""

import numpy as np
import pandas as pd
import streamlit as st
import mssql_python

# Columns the local pipeline produces that do NOT exist in Fact_PlayerStats
# on Synapse yet. Added back as NaN after loading so every page (which
# already guards with metric_has_data()) behaves exactly like local mode --
# it just shows those specific stats as unavailable, same as it already
# does for the 2025-2026 season locally.
MISSING_FACT_COLUMNS = ["Key_Passes", "Pass_Attempts", "Pass_Completed", "Touches", "Carries"]

DIM_PLAYER_QUERY = """
    SELECT
        PlayerID     AS player_id,
        PlayerName   AS player,
        Nationality  AS Nation,
        YEAR(BirthDate) AS Born
    FROM dbo.Dim_Players
"""

DIM_TEAM_QUERY = "SELECT TeamID AS team_id, TeamName AS team FROM dbo.Dim_Teams"

DIM_LEAGUE_QUERY = "SELECT LeagueID AS league_id, LeagueName AS league FROM dbo.Dim_Leagues"

DIM_SEASON_QUERY = "SELECT SeasonID AS season_id, Season AS season FROM dbo.Dim_Seasons"

FACT_QUERY = """
    SELECT
        PlayerID   AS player_id,
        TeamID     AS team_id,
        SeasonID   AS season_id,
        LeagueID   AS league_id,
        Pos,
        Age,
        Matches_Played,
        Matches_Started,
        Minutes_Played,
        Full_Match_Equivalents,
        Goals,
        Assists,
        Goal_Contributions,
        Expected_Goals,
        Expected_Assists,
        NonPenalty_Expected_Goals,
        Shots,
        Shots_On_Target,
        Progressive_Carries,
        Progressive_Passes,
        Progressive_Actions       AS progressive_actions,
        Shot_Creating_Actions,
        Goal_Creating_Actions,
        Tackles,
        Interceptions,
        Blocks,
        Defensive_Index           AS defensive_index,
        XG_Diff                   AS xg_diff,
        XA_Diff                   AS xa_diff
    FROM dbo.Fact_PlayerStats
"""


@st.cache_resource(show_spinner=False)
def get_connection():
    """One cached connection per Streamlit session/server process."""
    creds = st.secrets["azure_sql"]
    connection_string = (
        f"Server={creds['server']};"
        f"Database={creds['database']};"
        f"Uid={creds['username']};"
        f"Pwd={creds['password']};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
    )
    return mssql_python.connect(connection_string)


@st.cache_data(ttl=3600, show_spinner="Loading from Azure Synapse…")
def _read_query(sql: str) -> pd.DataFrame:
    conn = get_connection()
    return pd.read_sql(sql, conn)


def load_star_schema_from_azure():
    """Returns (dim_player, dim_team, dim_league, dim_season, fact) with
    exactly the same shape/column names as the local CSV path, sourced
    from the real Dim_*/Fact_PlayerStats tables on Synapse."""
    dim_player = _read_query(DIM_PLAYER_QUERY)
    dim_team = _read_query(DIM_TEAM_QUERY)
    dim_league = _read_query(DIM_LEAGUE_QUERY)
    dim_season = _read_query(DIM_SEASON_QUERY)
    fact = _read_query(FACT_QUERY)

    for col in MISSING_FACT_COLUMNS:
        if col not in fact.columns:
            fact[col] = np.nan

    return dim_player, dim_team, dim_league, dim_season, fact
