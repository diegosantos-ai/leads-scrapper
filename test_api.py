import requests

url = "http://localhost:8000/scrape"
payload = {
    "query": "Teste API SP",
    "limit": 1,
    "segment": "Teste",
    "no_enrich": True
}

try:
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
