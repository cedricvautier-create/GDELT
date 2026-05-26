# collect_reliefweb.py (À mettre à jour sur GitHub)
import requests
import json

def fetch_reliefweb_on_github():
    print("🇺🇳 GitHub Actions : Connexion libre à ReliefWeb API (v2)...")
    
    # LE CORRECTIF : Passage crucial de /v1/ à /v2/
    url = "https://api.reliefweb.int/v2/reports?appname=radar_strat"
    
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
            print(f"✅ {len(data)} rapports extraits avec succès via l'API v2.")
            
            # Sauvegarde du fichier de cache pour votre application Streamlit
            with open("reliefweb_alerts.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        else:
            print(f"❌ Erreur serveur ONU v2 : {response.status_code}")
    except Exception as e:
        print(f"⚠️ Échec de la collecte : {e}")

if __name__ == "__main__":
    fetch_reliefweb_on_github()
