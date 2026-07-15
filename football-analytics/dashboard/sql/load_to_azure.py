"""
One-off / repeatable script: pushes a fresh run of processed/*.csv (the
output of prj_fixed.ipynb) into the REAL Synapse tables (Dim_Players,
Dim_Teams, Dim_Leagues, Dim_Seasons, Fact_PlayerStats).

Only useful when you refresh the source data and need to reload Synapse --
if the tables already have the data you need, you don't have to run this.

    python sql/load_to_azure.py

Known gaps when going local-CSV -> real Synapse schema (documented, not
bugs): the local pipeline doesn't have BirthDate (only birth Year),
Height_cm, Weight_kg, or DefaultPosition for dim_player, so those load as
NULL. Similarly Key_Passes/Pass_Attempts/Pass_Completed/Touches/Carries
have no matching column in Fact_PlayerStats, so they're simply not sent.
"""

import sys
import tomllib
from pathlib import Path

import mssql_python
import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent
SECRETS_PATH = PROJECT_ROOT / ".streamlit" / "secrets.toml"
PROCESSED_DIR = PROJECT_ROOT / "processed"


def load_secrets():
    if not SECRETS_PATH.exists():
        sys.exit(f"Missing {SECRETS_PATH}. Copy secrets.toml.example and fill in your credentials first.")
    with open(SECRETS_PATH, "rb") as f:
        return tomllib.load(f)


def get_connection(creds: dict):
    azure = creds["azure_sql"]
    connection_string = (
        f"Server={azure['server']};"
        f"Database={azure['database']};"
        f"Uid={azure['username']};"
        f"Pwd={azure['password']};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
    )
    return mssql_python.connect(connection_string)


def insert_rows(cursor, table: str, columns: list, rows: list):
    placeholders = ", ".join("?" for _ in columns)
    col_list = ", ".join(columns)
    sql = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})"
    print(f"  Loading {len(rows):,} rows into {table}...")
    cursor.executemany(sql, rows)


def load_dim_players(cursor):
    df = pd.read_csv(PROCESSED_DIR / "dim_player.csv")
    out = pd.DataFrame({
        "PlayerID": df["player_id"],
        "PlayerName": df["player"],
        "BirthDate": None,          # only have birth YEAR locally, not a full date
        "Nationality": df["Nation"],
        "Height_cm": None,
        "Weight_kg": None,
        "DefaultPosition": None,
    })
    out = out.where(pd.notnull(out), None)
    rows = [tuple(r) for r in out.itertuples(index=False, name=None)]
    insert_rows(cursor, "dbo.Dim_Players", list(out.columns), rows)


def load_dim_teams(cursor):
    df = pd.read_csv(PROCESSED_DIR / "dim_team.csv")
    out = df.rename(columns={"team_id": "TeamID", "team": "TeamName"})
    rows = [tuple(r) for r in out.itertuples(index=False, name=None)]
    insert_rows(cursor, "dbo.Dim_Teams", list(out.columns), rows)


def load_dim_leagues(cursor):
    df = pd.read_csv(PROCESSED_DIR / "dim_league.csv")
    out = df.rename(columns={"league_id": "LeagueID", "league": "LeagueName"})
    rows = [tuple(r) for r in out.itertuples(index=False, name=None)]
    insert_rows(cursor, "dbo.Dim_Leagues", list(out.columns), rows)


def load_dim_seasons(cursor):
    df = pd.read_csv(PROCESSED_DIR / "dim_season.csv")
    out = df.rename(columns={"season_id": "SeasonID", "season": "Season"})
    rows = [tuple(r) for r in out.itertuples(index=False, name=None)]
    insert_rows(cursor, "dbo.Dim_Seasons", list(out.columns), rows)


def load_fact_player_stats(cursor):
    df = pd.read_csv(PROCESSED_DIR / "fact_player_stats.csv")
    out = pd.DataFrame({
        "PlayerID": df["player_id"],
        "TeamID": df["team_id"],
        "SeasonID": df["season_id"],
        "LeagueID": df["league_id"],
        "Pos": df["Pos"],
        "Age": df["Age"],
        "Matches_Played": df["Matches_Played"],
        "Matches_Started": df["Matches_Started"],
        "Minutes_Played": df["Minutes_Played"],
        "Full_Match_Equivalents": df["Full_Match_Equivalents"],
        "Goals": df["Goals"],
        "Assists": df["Assists"],
        "Goal_Contributions": df["Goal_Contributions"],
        "Shots": df["Shots"],
        "Shots_On_Target": df["Shots_On_Target"],
        "Standard_SoT_Percentage": (df["Shots_On_Target"] / df["Shots"] * 100).where(df["Shots"] > 0),
        "Expected_Goals": df["Expected_Goals"],
        "Expected_Assists": df["Expected_Assists"],
        "NonPenalty_Expected_Goals": df["NonPenalty_Expected_Goals"],
        "XG_Diff": df["xg_diff"],
        "XA_Diff": df["xa_diff"],
        "Goal_Contribution_Expected": df["Expected_Goals"] + df["Expected_Assists"],
        "Shot_Creating_Actions": df["Shot_Creating_Actions"],
        "Goal_Creating_Actions": df["Goal_Creating_Actions"],
        "Progressive_Carries": df["Progressive_Carries"],
        "Progressive_Passes": df["Progressive_Passes"],
        "Progressive_Actions": df["progressive_actions"],
        "Tackles": df["Tackles"],
        "Interceptions": df["Interceptions"],
        "Blocks": df["Blocks"],
        "Defensive_Index": df["defensive_index"],
    })
    out = out.where(pd.notnull(out), None)
    rows = [tuple(r) for r in out.itertuples(index=False, name=None)]
    insert_rows(cursor, "dbo.Fact_PlayerStats", list(out.columns), rows)


def main():
    creds = load_secrets()
    print("Connecting to Azure Synapse...")
    conn = get_connection(creds)
    cursor = conn.cursor()
    print("Connected.\n")

    load_dim_players(cursor)
    load_dim_teams(cursor)
    load_dim_leagues(cursor)
    load_dim_seasons(cursor)
    load_fact_player_stats(cursor)

    conn.commit()
    cursor.close()
    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
