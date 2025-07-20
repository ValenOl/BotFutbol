import requests

API_KEY = 'AQUI_TU_API_KEY'  # Reemplaza por tu API Key real

headers = {
    'x-apisports-key': '9a44b9ab4bb7260880bc284c12969a10'
}

# Endpoint para partidos en vivo
url = 'https://v3.football.api-sports.io/fixtures?live=all'

response = requests.get(url, headers=headers)

if response.status_code == 200:
    data = response.json()
    print("Partidos en vivo encontrados:")
    for fixture in data['response']:
        league = fixture['league']['name']
        home = fixture['teams']['home']['name']
        away = fixture['teams']['away']['name']
        goals_home = fixture['goals']['home']
        goals_away = fixture['goals']['away']
        print(f"[{league}] {home} {goals_home} - {goals_away} {away}")
else:
    print("Error:", response.status_code, response.text)