import http.client

seasons = [2022, 2023, 2024]
countries = ["England", "Spain", "Italy", "Germany", "France", "Netherlands", "Portugal", "Brazil", "Argentina"];
leagues = []

conn = http.client.HTTPSConnection("v3.football.api-sports.io")

headers = {
    'x-apisports-key': "53b2b19e75b917c167661182712ea834",
    'Content-Type': "application/json"
}

def get_players_by_league_and_season(league_id, season):
    conn.request("GET", f"/players?league={league_id}&season={season}", headers=headers)
    res = conn.getresponse()
    data = res.read()
    return data.decode("utf-8")

def main():
    players = get_players_by_league_and_season(40, 2022)
    open("league_40_season_2022.json", "w").write(players)

main()