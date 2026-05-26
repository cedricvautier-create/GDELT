# collect_reliefweb.py (À placer sur GitHub)
import requests
import json

def fetch_reliefweb_on_github():
    print("🇺🇳 GitHub Actions : Connexion libre à ReliefWeb API...")
    url = "https://api.reliefweb.int/v1/reports?appname=radar_strat"
    
    countries = ["Cameroon", "Central African Republic", "Gabon", "Republic of the Congo", "Chad", "Equatorial Guinea"]
    
    payload = {
        "filter": {
            "field": "primary_country.name",
            "value": countries,
            "operator": "OR"
        },
        "fields": {
            "include": ["title", "url", "primary_country", "source", "date"]
        },
        "limit": 40,
        "sort": ["date:desc"]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=15)
        if response.status_code == 200:
            data = response.json().get("data", [])
            print(f"✅ {len(data)} rapports extraits avec succès.")
            
            # Sauvegarde dans le dépôt qui sera poussé sur votre branche principale
            with open("reliefweb_alerts.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        else:
            print(f"❌ Erreur serveur ONU : {response.status_code}")
    except Exception as e:
        print(f"⚠️ Échec : {e}")

if __name__ == "__main__":
    fetch_reliefweb_on_github()