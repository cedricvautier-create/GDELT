# collect_reliefweb.py (Version officielle validée OCHA v2)
import requests
import json

def fetch_reliefweb_v2_official():
    print("🇺🇳 GitHub Actions : Connexion authentifiée à ReliefWeb API (v2)...")
    
    # 🌟 CONFIGURATION OFFICIELLE : Intégration de votre appname approuvé
    url = "https://api.reliefweb.int/v2/reports?appname=AFD-monitoring-AfCent75"
    
    # Liste ciblée des pays de la zone CEMAC
    countries = ["Cameroon", "Central African Republic", "Gabon", "Republic of the Congo", "Chad", "Equatorial Guinea"]
    
    # Structure de requête POST native v2
    payload = {
        "filter": {
            "field": "primary_country.name",
            "value": countries,
            "operator": "OR"
        },
        "fields": {
            # ➡️ AJOUT DE "body" ICI POUR ASPIRER LE TEXTE INTEGRAL
            "include": ["title", "url", "primary_country", "source", "date", "body"]
        },
        "limit": 40,
        "sort": ["date:desc"]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=15)
        if response.status_code == 200:
            data = response.json().get("data", [])
            print(f"✅ {len(data)} bulletins humanitaires extraits avec succès via l'API v2 officielle.")
            
            # Écriture du fichier de cache qui sera ramassé par le workflow Git
            with open("reliefweb_alerts.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        else:
            print(f"❌ Erreur serveur OCHA v2 ({response.status_code}) : {response.text}")
            
    except Exception as e:
        print(f"⚠️ Échec critique de la collecte : {e}")

if __name__ == "__main__":
    fetch_reliefweb_v2_official()
