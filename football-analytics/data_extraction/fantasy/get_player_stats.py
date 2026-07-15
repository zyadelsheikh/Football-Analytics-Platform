from pathlib import Path
import http.client
import json
import time

API_URL = "sdp-prem-prod.premier-league-prod.pulselive.com"
PLAYERS_DATA_PATH = "data/players_data_premier_league"
PLAYERS_PATH = "data/players"
PLAYERS_IDS_PATH = "data/player_ids.json"

MAX_RETRIES = 3

conn = http.client.HTTPSConnection(API_URL)

def get_player_stats(player_id: int, competition_id: int, season: int):
  global conn

  for attempt in range(1, MAX_RETRIES + 1):
    try:
      conn.request("GET", f"/api/v2/competitions/{competition_id}/seasons/{season}/players/{player_id}/stats")
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

      # print(f"Error fetching data for player {player_id}: {res.status} {res.reason}")
      return False, "{}"

    except http.client.HTTPException as e:
      print(f"HTTP error: {e}")

      conn.close()
      conn = http.client.HTTPSConnection(API_URL)

      if attempt < MAX_RETRIES:
        time.sleep(1)
        continue

      return False, "{}"

  return False, "{}"



def get_player_ids():
  player_ids = []
  players_data_dir = Path(f"{PLAYERS_DATA_PATH}")

  ## Check if the directory exists and is a directory
  if not players_data_dir.exists() or not players_data_dir.is_dir():
    print(f"Directory not found: {players_data_dir}")
    return player_ids
  
  ## Return a list of player IDs from the JSON files in the directory
  for file_path in sorted(players_data_dir.iterdir()):
    if not file_path.is_file() or file_path.suffix.lower() != ".json":
      continue
    
    player_ids.append(file_path.stem)  # Use the file name (without extension) as the player ID

  return player_ids

def save_player_ids_to_file(player_ids: list, file_path: str):
  json_object = {"player_ids": player_ids}
  with open(file_path, "w") as f:
    json.dump(json_object, f, indent=2)

def load_player_ids_from_file(file_path: str):
  if not Path(file_path).exists():
    print(f"File not found: {file_path}")
    return []

  with open(file_path, "r") as f:
    data = json.load(f)
    return data.get("player_ids", [])

def load_player_data_from_file(player_id: str):
  file_path = Path(f"{PLAYERS_DATA_PATH}/{player_id}.json")
  if not file_path.exists():
    print(f"File not found: {file_path}")
    return []

  with open(file_path, "r") as f:
    data = json.load(f)
    return data

def check_directory_exists(directory_path: str):
  dir_path = Path(directory_path)
  return dir_path.exists() and dir_path.is_dir()

def create_directory(directory_path: str):
  dir_path = Path(directory_path)
  dir_path.mkdir(parents=True, exist_ok=True)

def save_player_stats_to_file(player_id: str, competition_id: int, season: int, stats_data: str):
  directory_path = Path(f"{PLAYERS_PATH}/competition={competition_id}/season={season}/{player_id}")

  file_path = directory_path / f"stats.json"
  with open(file_path, "w", encoding="utf-8") as f:
    f.write(stats_data)

def get_start_index_from_user(max_index: int):
  start_index = int(input(f"Enter the start index (1 to {max_index-1}): "))
  return start_index

def get_end_index_from_user(max_index: int):
  end_index = int(input(f"Enter the end index (2 to {max_index}): "))
  return end_index

def validate_index_range(start_index: int, end_index: int, max_index: int):
  if start_index < 1 or end_index > max_index or start_index >= end_index:
    print("Invalid index range.")
    return False
  return True

def main():
  player_ids = []
  start_index = 0  # Change this to the index you want to start from
  end_index = 0   # Change this to the index you want to end at (exclusive)
  
  player_ids = load_player_ids_from_file(PLAYERS_IDS_PATH)
    
  print(f"Loaded {len(player_ids)} player IDs from {PLAYERS_IDS_PATH}")
  
  start_index = get_start_index_from_user(len(player_ids))
  end_index = get_end_index_from_user(len(player_ids))

  if not validate_index_range(start_index, end_index, len(player_ids)):
    return

  player_ids = player_ids[start_index-1:end_index]  # Slice the list to start from the desired index

  for player_id in player_ids:  # Process player IDs
    # Load player data from file
    player_data = load_player_data_from_file(player_id)
    if (len(player_data) == 0):
      print(f"No data found for player {player_id}, skipping...")
      continue
    
    # Fetch stats for each competition and season in the player data
    for raw in player_data:
      competition_id = raw["id"]["competitionId"]
      season = raw["id"]["seasonId"]
      
      print(type(competition_id))
      
      if int(competition_id) != 8:  # Premier League only
        print(f"Skipping player {player_id} for competition {competition_id}, season {season} (not Premier League)")
        continue
      
      ## Check if the directory for the player exists, if not create it
      if check_directory_exists(f"{PLAYERS_PATH}/competition={competition_id}/season={season}/{player_id}"):
        print(f"Directory already exists for player {player_id}, competition {competition_id}, season {season}, skipping...")
        continue
      else:
        create_directory(f"{PLAYERS_PATH}/competition={competition_id}/season={season}/{player_id}")
      
      time.sleep(0.200)  # Sleep for 200 milliseconds to avoid overwhelming the server
      ret, stats = get_player_stats(player_id, competition_id, season)
      print(f"Fetching stats for player {player_id}, competition {competition_id}, season {season}... {'Found' if ret else 'Not Found'}")
      if ret:
        save_player_stats_to_file(player_id, competition_id, season, stats)

# player_ids = get_player_ids()
# save_player_ids_to_file(player_ids, PLAYERS_IDS_PATH)

main()