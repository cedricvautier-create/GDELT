# collect_gdelt.py
import requests
import json

def fetch_gdelt_alerts():
    print("📡 GDELT : Envoi de la requête avec paramètres standardisés...")
    
    # URL utilisant exclusivement des paramètres whitelistés par GDELT
    # On utilise 'timespan=7d' (la valeur '2d' brise le routeur et génère la 404)
    url = (
        "https://api.gdeltproject.org/api/v2/geo/geo"
        "?query=protest"
        "&mode=PointData"
        "&format=GeoJSON"
        "&timespan=7d"
    )
    
    try:
        # Exécution par l'infrastructure GitHub Actions
        response = requests.get(url, timeout=30)
        
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
            
            # Sauvegarde du fichier exploitable
            with open("gdelt_alerts.json", "w", encoding="utf-8") as f:
                json.dump(points, f, indent=4)
            print(f"✅ Succès : {len(points)} alertes mondiales récupérées et écrites.")
            
        else:
            print(f"❌ Erreur serveur GDELT (Code {response.status_code}).")
            
    except Exception as e:
        print(f"❌ Échec de la collecte GDELT : {e}")

if __name__ == "__main__":
    fetch_gdelt_alerts()
