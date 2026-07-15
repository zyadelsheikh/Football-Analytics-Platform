from pathlib import Path
import http.client
import json
import time

COMPETITIONS_ID = [8] # Premier League only
SEASONS = [2019, 2020, 2021, 2022, 2023, 2024, 2025]

API_URL = "sdp-prem-prod.premier-league-prod.pulselive.com"
PLAYER_LISTINGS_PATH = "data/player_listings"

conn = http.client.HTTPSConnection(API_URL)

def get_page(competition_id: int, season: int, _next: str = "", limit: int = 100):
  conn.request("GET", f"/api/v1/competitions/{competition_id}/seasons/{season}/players?_limit={limit}&_next={_next}")
  res = conn.getresponse()
  data = res.read()
  return data.decode("utf-8")

def get_pages(competition_id: int, season: int):
  _next = ""  # Initialize the _next variable
  pages = []  # List to store all pages of data
  
  # Fetch the first page of data
  data = get_page(competition_id, season, _next)
  data_json = json.loads(data)
  _next = data_json["pagination"]["_next"]
  
  if len(data_json["data"]) == 0:
    print("No data found for the given competition and season.")
    return pages
  
  pages.append(data)
  print("Page 1")  # Print the first page of data
  
  while _next:
    time.sleep(0.200)
    data = get_page(competition_id, season, _next)
    data_json = json.loads(data)
    _next = data_json["pagination"]["_next"]
    pages.append(data)
    print(f"Page {len(pages)}")  # Print subsequent pages of data
  
  return pages

def main():
  for competition_id in COMPETITIONS_ID:
    for season in SEASONS:
      print(f"Fetching data for competition {competition_id} and season {season}...")
      pages = get_pages(competition_id, season)
      
      player_listings_dir = Path(PLAYER_LISTINGS_PATH, f"competition={competition_id}", f"season={season}")
      player_listings_dir.mkdir(parents=True, exist_ok=True)
      
      for i, page in enumerate(pages):
        with open (f"{PLAYER_LISTINGS_PATH}/competition={competition_id}/season={season}/page_{i+1}.json", "w") as f:
          f.write(page)

main()