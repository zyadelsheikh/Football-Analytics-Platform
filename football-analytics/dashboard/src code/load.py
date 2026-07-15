from pathlib import Path
import pandas as pd


def build_star_schema(df_analysis):
    """
    Build dimension tables and fact table
    using a star schema design.
    """

    # ==================================================
    # 7. Dimensional Modeling
    # ==================================================

    dim_player = (
        df_analysis[["player", "Nation", "Born"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    dim_player.insert(0, "player_id", dim_player.index + 1)

    dim_team = pd.DataFrame({
        "team": df_analysis["team"].dropna().unique()
    })
    dim_team.insert(0, "team_id", dim_team.index + 1)

    dim_league = pd.DataFrame({
        "league": df_analysis["league"].dropna().unique()
    })
    dim_league.insert(0, "league_id", dim_league.index + 1)

    dim_season = pd.DataFrame({
        "season": df_analysis["season"].dropna().unique()
    })
    dim_season.insert(0, "season_id", dim_season.index + 1)

    fact_player_stats = (
        df_analysis
        .merge(dim_player, on=["player", "Nation", "Born"], how="left")
        .merge(dim_team, on="team", how="left")
        .merge(dim_league, on="league", how="left")
        .merge(dim_season, on="season", how="left")
    )

    fact_player_stats = fact_player_stats.drop(
        columns=[
            "player",
            "team",
            "league",
            "season",
            "Nation",
            "Born"
        ]
    )

    key_id_cols = [
        "player_id",
        "team_id",
        "league_id",
        "season_id"
    ]

    fact_player_stats = fact_player_stats[
        key_id_cols +
        [c for c in fact_player_stats.columns if c not in key_id_cols]
    ]

    # ==================================================
    # 8. Export Tables
    # ==================================================

    OUT_DIR = Path(
        r"C:\Users\3D STORE\Documents\depi project\football-analytics\data"
    )

    dim_player.to_csv(OUT_DIR / "dim_player.csv", index=False)
    dim_team.to_csv(OUT_DIR / "dim_team.csv", index=False)
    dim_league.to_csv(OUT_DIR / "dim_league.csv", index=False)
    dim_season.to_csv(OUT_DIR / "dim_season.csv", index=False)

    fact_player_stats.to_csv(
        OUT_DIR / "fact_player_stats.csv",
        index=False
    )

    return (
        dim_player,
        dim_team,
        dim_league,
        dim_season,
        fact_player_stats
    )