-- REFERENCE ONLY -- these tables already exist on football-project-synapse.
-- You do NOT need to run this unless you're rebuilding the database from
-- scratch. This file just documents the real schema that db.py maps to.
--
-- Real column names are PascalCase (PlayerID, TeamName, ...), different
-- from the local processed/*.csv star schema (player_id, team, ...).
-- db.py's SQL queries (DIM_PLAYER_QUERY, FACT_QUERY, ...) alias every
-- column back to the internal names the rest of the app uses -- that's the
-- ONLY place that needs to know about this real schema.

CREATE TABLE dbo.Dim_Leagues (
    LeagueID INT NOT NULL,
    LeagueName VARCHAR(150),
    CONSTRAINT PK_Dim_League PRIMARY KEY NONCLUSTERED (LeagueID) NOT ENFORCED
)
WITH (DISTRIBUTION = REPLICATE, CLUSTERED INDEX (LeagueID));

CREATE TABLE dbo.Dim_Players (
    PlayerID INT NOT NULL,
    PlayerName VARCHAR(150),
    BirthDate DATE NULL,
    Nationality VARCHAR(100) NULL,
    Height_cm INT NULL,
    Weight_kg INT NULL,
    DefaultPosition VARCHAR(50) NULL,
    CONSTRAINT PK_Dim_Players PRIMARY KEY NONCLUSTERED (PlayerID) NOT ENFORCED
)
WITH (DISTRIBUTION = REPLICATE, CLUSTERED INDEX (PlayerID));

CREATE TABLE dbo.Dim_Seasons (
    SeasonID INT NOT NULL,
    Season VARCHAR(150),
    CONSTRAINT PK_Dim_Season PRIMARY KEY NONCLUSTERED (SeasonID) NOT ENFORCED
)
WITH (DISTRIBUTION = REPLICATE, CLUSTERED INDEX (SeasonID));

CREATE TABLE dbo.Dim_Teams (
    TeamID INT NOT NULL,
    TeamName VARCHAR(150),
    CONSTRAINT PK_Dim_Team PRIMARY KEY NONCLUSTERED (TeamID) NOT ENFORCED
)
WITH (DISTRIBUTION = REPLICATE, CLUSTERED INDEX (TeamID));

CREATE TABLE dbo.Fact_PlayerStats (
    StatID INT IDENTITY(1,1) NOT NULL,
    PlayerID INT NOT NULL,
    TeamID INT NOT NULL,
    SeasonID INT NOT NULL,
    LeagueID INT NOT NULL,
    Pos VARCHAR(50) NULL,
    Age INT NULL,
    Matches_Played INT,
    Matches_Started INT,
    Minutes_Played INT,
    Full_Match_Equivalents DECIMAL(5,2),
    Goals INT,
    Assists INT,
    Goal_Contributions INT,
    Shots INT,
    Shots_On_Target INT,
    Standard_SoT_Percentage DECIMAL(5,2),
    Expected_Goals DECIMAL(5,2),
    Expected_Assists DECIMAL(5,2),
    NonPenalty_Expected_Goals DECIMAL(5,2),
    XG_Diff DECIMAL(5,2),
    XA_Diff DECIMAL(5,2),
    Goal_Contribution_Expected DECIMAL(5,2),
    Shot_Creating_Actions INT,
    Goal_Creating_Actions INT,
    Progressive_Carries INT,
    Progressive_Passes INT,
    Progressive_Actions INT,
    Tackles INT,
    Interceptions INT,
    Blocks INT,
    Defensive_Index DECIMAL(5,2)
    -- NOTE: no Key_Passes / Pass_Attempts / Pass_Completed / Touches / Carries
    -- columns exist here. The dashboard handles this the same way it already
    -- handles the 2025-2026 season's missing advanced stats: those specific
    -- charts/metrics just show as unavailable instead of erroring.
)
WITH (
    DISTRIBUTION = HASH(PlayerID),
    CLUSTERED COLUMNSTORE INDEX
);
