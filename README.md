Football Analytics Dashboard
A local Streamlit dashboard built directly on top of the star-schema output of prj_fixed.ipynb (dim_player, dim_team, dim_league, dim_season, fact_player_stats).

1. Setup
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
2. Get the data in place
This app reads five CSVs from ./processed/:

processed/dim_player.csv
processed/dim_team.csv
processed/dim_league.csv
processed/dim_season.csv
processed/fact_player_stats.csv
They are exactly the files produced by the last cell of prj_fixed.ipynb (the "Export each table to its own file" step). This copy of processed/ already contains a real run of that notebook — to refresh the data (e.g. after adding a new season), just re-run the notebook and overwrite this folder with its processed/ output.

3. Run it
streamlit run app.py
Opens at http://localhost:8501.

Pages
Home — league-wide overview: player/team counts, top scorers, top assisters, goals by team, with a raw-data export.
Player Season — player profile, percentile-rank radar chart, key stats + extra stats (pass/shot accuracy, goals & assists per 90), compare against any player from any league/season (percentiles are computed against each player's own peer group so the comparison stays fair across competitions), a season-by-season trend line (Goals/Assists/xG/xA), and a full season-by-season log table.
Team Season — squad summary, advanced team stats breakdown, top scorers, compare against any team(s) from any league (same season, cross-league), a team trend line across seasons, and the full squad table.
League Ranking — bar-chart ranking of all players by a chosen metric (Attacking / Passing / Dribbling & Carrying / Defending / Creation), with min-minutes and position filters.
Quick Search (sidebar, always visible) — type a player or team name and jump straight to their page with the right season/league preselected.
CSV / Excel export — available on Home, Player Season, Team Season, and League Ranking wherever there's a data table.
Note on cross-league comparisons
Comparisons (players and teams) are statistically valid, but keep in mind the top-5 leagues differ in competitive level — a "Goals p90" comparison between a Ligue 1 and a Premier League player is a fair stats comparison, not necessarily a fair quality comparison.

Known data limitation (carried over from the ETL notebook)
The 2025-2026 source file only has basic counting stats (Goals, Assists, Minutes, Matches). It does not contain xG, xA, Shots, Progressive actions, Tackles, Interceptions, Blocks, Touches, or Carries — those columns are genuinely missing at the source, not a bug. The app detects this per season/metric and shows a warning instead of an empty chart, the same way the reference app in your screenshots showed "No player data available for this competition / season".

Deploying to Azure later
Support for this is already built in — you don't need to change any page code, just flip a switch. See "Connecting to Azure Synapse" below.

Connecting to Azure Synapse
⚠️ Security first: never hardcode a server/database/username/password in a .py file. Credentials go in .streamlit/secrets.toml, which is already listed in .gitignore so it never gets committed or shared inside the zip.

The real Synapse schema is already in place — already handled
The actual tables on Synapse (dbo.Dim_Players, dbo.Dim_Teams, dbo.Dim_Leagues, dbo.Dim_Seasons, dbo.Fact_PlayerStats) use different names/columns than the local processed/*.csv star schema (PascalCase, PlayerID/TeamID/etc., plus a few extra columns like Height_cm that the local pipeline doesn't produce, and missing a few the local pipeline does have: Key_Passes, Pass_Attempts, Pass_Completed, Touches, Carries).

Every query in db.py explicitly qualifies each table with the dbo. schema (e.g. FROM dbo.Dim_Players, not just Dim_Players) — matching exactly what's shown in Synapse Studio's object explorer, so there's no ambiguity about which schema is being read.

Instead of rewriting every page to know two different naming conventions, db.py translates at the SQL boundary — every query aliases Synapse's real column names into the same internal names the app already uses (player, team, Nation, Born, xg_diff, ...). The 5 missing columns are added back as empty (NaN) after loading, so those specific stats just show as "unavailable" — exactly the same way the dashboard already handles the 2025-2026 season's missing advanced stats. Nothing else in the app needed to change.

1. Set up secrets
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
Edit .streamlit/secrets.toml and fill in your real Synapse server, database, username, and password.

2. Install the driver
pip install mssql-python
3. Tables already exist — nothing to create
If your Synapse tables already have the data (as they do now), skip straight to step 5. sql/create_tables.sql is kept only as reference documentation of the real schema, in case you ever need to rebuild the database from scratch.

4. (Optional) Reload the data later
python sql/load_to_azure.py
Only needed if you refresh processed/*.csv (by re-running prj_fixed.ipynb) and want to push the new data into the existing Synapse tables. (For very large refreshes, COPY INTO from Blob Storage is faster than row-by-row inserts — this script is meant to get you running quickly, not to be the production loading pattern.)

5. Switch the dashboard to Azure
In .streamlit/secrets.toml:

data_source = "azure"
That's it — data.py detects this automatically and every page reads live from Synapse instead of the local CSVs, with no other code changes. Set it back to "local" any time to go back to the CSVs.
