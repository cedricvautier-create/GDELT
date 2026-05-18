# collect_gdelt.py
import requests
import json

def fetch_gdelt_alerts():
    print("📡 GDELT : Préparation de la requête sécurisée...")
    
    url = "https://api.gdeltproject.org/api/v2/geo/geo"
    
    # On passe par les paramètres natifs de requests pour un encodage parfait
    # GDELT est extrêmement sensible à la casse (minuscules obligatoires ici)
    params = {
        "query": "conflict OR crisis OR protest OR incident",
        "mode": "PointData",
        "format": "geojson",  # Tout en minuscules
        "timespan": "2d"      # '2d' pour 2 jours, en minuscules
    }
    
    try:
        # Exécution par GitHub (pas de proxy requis)
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            geojson_data = response.json()
            features = geojson_data.get("features", [])
            points = []
            
            for f in features:
                coords = f.get("geometry", {}).get("coordinates", [])
                props = f.get("properties", {})
                
                if len(coords) == 2:
                    count = int(props.get("count", 1))
                    points.append({
                        "lon": coords[0],
                        "lat": coords[1],
                        "name": props.get("name", "Alerte"),
                        "count": count,
                        "radius": min(150000, max(20000, count * 4000))
                    })
            
            with open("gdelt_alerts.json", "w", encoding="utf-8") as f:
                json.dump(points, f, indent=4)
            print(f"✅ Succès : {len(points)} alertes mondiales récupérées.")
            
        else:
            print(f"❌ Erreur serveur GDELT (Code {response.status_code}).")
            print("Vérifiez la structure de l'URL ou des paramètres.")
            
    except Exception as e:
        print(f"❌ Échec de la collecte GDELT : {e}")

if __name__ == "__main__":
    fetch_gdelt_alerts()
