import requests

# Testando com uma agência, que geralmente tem email no rodapé
url = "http://localhost:8000/scrape"
payload = {
    "query": "Agência Marketing Av Paulista",
    "limit": 3,
    "segment": "Teste Enrich",
    "no_enrich": True,  # Skip Gemini for speed
    "deep_enrich": True # ENABLE web scraping for emails
}

print(f"🚀 Triggering Deep Enrich Test...")
try:
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
