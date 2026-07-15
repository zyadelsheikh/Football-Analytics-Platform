import http.client

seasons = [2022, 2023, 2024]
countries = ["England", "Spain", "Italy", "Germany", "France", "Netherlands", "Portugal", "Brazil", "Argentina"];

conn = http.client.HTTPSConnection("v3.football.api-sports.io")

checkpoint = open("checkpoint.txt", "r").read().strip() or "0_2022"

headers = {
    'x-apisports-key': "53b2b19e75b917c167661182712ea834",
    'Content-Type': "application/json"
}

def get_leagues_by_country(country):
    conn.request("GET", f"/leagues?country={country}", headers=headers)
    res = conn.getresponse()
    data = res.read()
    return data.decode("utf-8")