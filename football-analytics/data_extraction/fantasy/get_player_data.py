from pathlib import Path
import http.client
import json
import time

COMPETITIONS_ID = [8] ## Premier League only
SEASONS = [2019, 2020, 2021, 2022, 2023, 2024, 2025]

API_URL = "sdp-prem-prod.premier-league-prod.pulselive.com"
PLAYERS_DATA_PATH = "data/players_data_premier_league"
PLAYER_LISTINGS_PATH = "data/player_listings"

MAX_RETRIES = 3

conn = http.client.HTTPSConnection(API_URL)

def get_player_data(player_id: int):
  global conn

  for attempt in range(1, MAX_RETRIES + 1):
    try:
      conn.request("GET", f"/api/v1/players/{player_id}")
      res = conn.getresponse()

      body = res.read()   # Always consume the response

      if res.status == 200:
        return True, body.decode("utf-8")

      if res.status == 504:
        print(f"Bad gateway for player {player_id} (attempt {attempt}/{MAX_RETRIES}), retrying...")

        if attempt < MAX_RETRIES:
          conn.close()
          conn = http.client.HTTPSConnection(API_URL)
          time.sleep(1)
          continue

      print(f"Error fetching data for player {player_id}: {res.status} {res.reason}")
      return False, "{}"

    except http.client.HTTPException as e:
      print(f"HTTP error: {e}")

      conn.close()
      conn = http.client.HTTPSConnection(API_URL)

      if attempt < MAX_RETRIES:
          time.sleep(1)

      return False, "{}"

  return False, "{}"

def get_player_ids(competition_id: int, season: int):
  player_ids = []
  listings_dir = Path(f"{PLAYER_LISTINGS_PATH}/competition={competition_id}/season={season}")

  ## Check if the directory exists and is a directory
  if not listings_dir.exists() or not listings_dir.is_dir():
    print(f"Directory not found: {listings_dir}")
    return player_ids

  ## Iterate through all JSON files in the directory
  for file_path in sorted(listings_dir.iterdir()):
    if not file_path.is_file() or file_path.suffix.lower() != ".json":
      continue
    
    ## Read the JSON data from the file
    with file_path.open("r", encoding="utf-8") as file:
      page = json.load(file)

    ## Extract player IDs from the JSON data
    for player in page["data"]:
      player_ids.append(player["id"]["playerId"])
  
  return player_ids

def main():
  players_dir = Path(PLAYERS_DATA_PATH)
  players_dir.mkdir(parents=True, exist_ok=True)
  
  count = 0
  
  for competition_id in COMPETITIONS_ID:
    for season in SEASONS:
      print(f"Fetching player IDs for competition {competition_id} and season {season}...")
      player_ids = get_player_ids(competition_id, season)
      
      for player_id in player_ids:
        if (players_dir / f"{player_id}.json").exists():
          continue
        
        time.sleep(0.200)  # Sleep for 200 milliseconds to avoid overwhelming the server
        success, player_data = get_player_data(player_id)
        if success:
          with open(players_dir / f"{player_id}.json", "w", encoding="utf-8") as f:
            f.write(player_data)
          count += 1
        else:
          print(f"Failed to fetch data for player {player_id}")
          

  print(f"Total players fetched: {count}")

main()