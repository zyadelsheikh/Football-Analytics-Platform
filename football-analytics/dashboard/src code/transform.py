import pandas as pd
import numpy as np

def transform_data(df1, df2):
    
    # ==================================================
    # 1. Standardize season and league labels
    # ==================================================

    def expand_season_code(code_value):
        s = str(int(code_value))
        year_start = int(s[:2])
        year_end = int(s[2:])
        return f"20{year_start:02d}-20{year_end:02d}"

    df1["season"] = df1["season"].apply(expand_season_code)
    df2["season"] = "2025-2026"

    LEAGUE_NAME_MAP = {
        "ENG-Premier League": "Premier League",
        "ESP-La Liga": "La Liga",
        "FRA-Ligue 1": "Ligue 1",
        "GER-Bundesliga": "Bundesliga",
        "ITA-Serie A": "Serie A",
        "eng Premier League": "Premier League",
        "es La Liga": "La Liga",
        "fr Ligue 1": "Ligue 1",
        "it Serie A": "Serie A",
        "de Bundesliga": "Bundesliga",
    }

    df1["league"] = df1["league"].map(LEAGUE_NAME_MAP).fillna(df1["league"])
    df2["Comp"] = df2["Comp"].map(LEAGUE_NAME_MAP).fillna(df2["Comp"])

    # ==================================================
    # 2. Rename columns
    # ==================================================

    df1 = df1.rename(columns={
        "player": "player",
        "team": "team",
        "league": "league",
        "season": "season",
        "pos_": "Pos",
        "age_": "Age",
        "nation_": "Nation",
        "born_": "Born",

        "Playing Time_MP": "Matches_Played",
        "Playing Time_Starts": "Matches_Started",
        "Playing Time_Min": "Minutes_Played",
        "Playing Time_90s": "Full_Match_Equivalents",

        "Performance_Gls": "Goals",
        "Performance_Ast": "Assists",
        "Performance_G+A": "Goal_Contributions",

        "Expected_xG": "Expected_Goals",
        "Expected_xAG": "Expected_Assists",
        "Expected_npxG": "NonPenalty_Expected_Goals",

        "Standard_Sh": "Shots",
        "Standard_SoT": "Shots_On_Target",

        "Progression_PrgC": "Progressive_Carries",
        "Progression_PrgP": "Progressive_Passes",

        "KP_": "Key_Passes",
        "Total_Att": "Pass_Attempts",
        "Total_Cmp": "Pass_Completed",

        "SCA_SCA": "Shot_Creating_Actions",
        "GCA_GCA": "Goal_Creating_Actions",

        "Tackles_Tkl": "Tackles",
        "Int_": "Interceptions",
        "Blocks_Blocks": "Blocks",

        "Carries_Carries": "Carries",
        "Touches_Touches": "Touches",
    })

    df2 = df2.rename(columns={
        "Player": "player",
        "Squad": "team",
        "Comp": "league",
        "Pos": "Pos",
        "Age": "Age",
        "Nation": "Nation",
        "Born": "Born",
        "MP": "Matches_Played",
        "Starts": "Matches_Started",
        "Min": "Minutes_Played",
        "90s": "Full_Match_Equivalents",
        "Gls": "Goals",
        "Ast": "Assists",
        "G+A": "Goal_Contributions",
    })

    # ==================================================
    # 3. Merge sources
    # ==================================================

    df = pd.concat([df1, df2], ignore_index=True, sort=False)

    # ==================================================
    # 4. Select analysis columns
    # ==================================================

    key_cols = [
        "player", "team", "league", "season", "Pos", "Age", "Nation", "Born",
        "Matches_Played", "Matches_Started", "Minutes_Played", "Full_Match_Equivalents",
        "Goals", "Assists", "Goal_Contributions",
        "Expected_Goals", "Expected_Assists", "NonPenalty_Expected_Goals",
        "Shots", "Shots_On_Target", "Progressive_Carries", "Progressive_Passes", "Touches",
        "Key_Passes", "Pass_Attempts", "Pass_Completed", "Shot_Creating_Actions", "Carries",
        "Goal_Creating_Actions", "Tackles", "Interceptions", "Blocks",
    ]

    available_key_cols = [c for c in key_cols if c in df.columns]

    df_analysis = df[available_key_cols].copy()

    # ==================================================
    # 5. Clean and type-cast numeric columns
    # ==================================================

    TEXT_ID_COLS = [
        "player",
        "team",
        "league",
        "season",
        "Pos",
        "Nation"
    ]

    NUMERIC_TEXT_COLS = [
        c for c in df_analysis.columns
        if c not in TEXT_ID_COLS
        and df_analysis[c].dtype == "object"
    ]

    for col in NUMERIC_TEXT_COLS:

        df_analysis[col] = (
            df_analysis[col]
            .astype(str)
            .str.replace(r'[^\d.-]', '', regex=True)
            .replace('', np.nan)
        )

        df_analysis[col] = pd.to_numeric(
            df_analysis[col],
            errors="coerce"
        )

    df_analysis["Minutes_Played"] = (
        pd.to_numeric(
            df_analysis["Minutes_Played"],
            errors="coerce"
        )
        .fillna(0)
    )

    int_cols = [
        "Shots",
        "Shots_On_Target",
        "Progressive_Carries",
        "Progressive_Passes",
        "Pass_Attempts",
        "Pass_Completed",
        "Shot_Creating_Actions",
        "Tackles",
        "Interceptions",
        "Blocks",
    ]

    int_cols = [c for c in int_cols if c in df_analysis.columns]

    df_analysis[int_cols] = (
        df_analysis[int_cols]
        .round()
        .astype("Int64")
    )

    # ==================================================
    # 6. Feature Engineering
    # ==================================================

    df_analysis["xg_diff"] = (
        df_analysis["Goals"]
        - df_analysis["Expected_Goals"]
    )

    df_analysis["xa_diff"] = (
        df_analysis["Assists"]
        - df_analysis["Expected_Assists"]
    )

    df_analysis["progressive_actions"] = (
        df_analysis["Progressive_Carries"]
        + df_analysis["Progressive_Passes"]
    )

    df_analysis["defensive_index"] = (
        df_analysis["Tackles"]
        + df_analysis["Interceptions"]
        + df_analysis["Blocks"]
    )

    return df_analysis