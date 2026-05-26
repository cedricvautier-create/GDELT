# collect_climate.py (Version augmentée NASA EONET + POWER)
import requests
import pandas as pd
import json
import time
from datetime import datetime, timedelta

def collect_thermal_anomalies():
    print("🛰️ NASA FIRMS : Extraction des anomalies thermiques...")
    MAP_KEY = "075c84c6c7cab1cfb60f6f70f77b45af" # Remettez votre clé FIRMS active
    url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/MODIS_NRT/8,-6,24,14/1"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200 and "latitude" in response.text:
            with open("climate_fires_cache.csv", "w", encoding="utf-8") as f:
                f.write(response.text)
            print("✅ Cache FIRMS mis à jour.")
        else:
            print("⚠️ FIRMS indisponible, génération d'un cache vide.")
            pd.DataFrame(columns=['latitude', 'longitude', 'brightness', 'acq_date']).to_csv("climate_fires_cache.csv", index=False)
    except Exception as e:
        print(f"❌ Échec FIRMS : {e}")

def collect_eonet_events():
    print("🌊 NASA EONET : Recherche des inondations et glissements de terrain...")
    # Requête publique sans clé sur les événements ouverts
    url = "https://eonet.gsfc.nasa.gov/api/v3/events?category=floods,landslides&status=open"
    try:
        response = requests.get(url, timeout=15)
        events_filtered = []
        if response.status_code == 200:
            events = response.json().get("events", [])
            for e in events:
                geometry = e.get("geometry", [])
                if geometry:
                    # Extraction des dernières coordonnées [lon, lat]
                    coords = geometry[-1].get("coordinates", [0, 0])
                    lon, lat = coords[0], coords[1]
                    
                    # Filtrage géographique strict sur la Bounding Box CEMAC
                    if (8.0 <= lon <= 24.0) and (-6.0 <= lat <= 14.0):
                        events_filtered.append({
                            "id": e.get("id"),
                            "title": e.get("title"),
                            "type": "Inondation" if "flood" in str(e.get("categories")).lower() else "Glissement de terrain",
                            "lon": lon,
                            "lat": lat,
                            "date": geometry[-1].get("date")[:10],
                            "link": e.get("sources", [{}])[0].get("url", "#")
                        })
            
            with open("climate_events_cache.json", "w", encoding="utf-8") as f:
                json.dump(events_filtered, f, indent=4)
            print(f"✅ Cache EONET mis à jour ({len(events_filtered)} événements détectés).")
    except Exception as e:
        print(f"❌ Échec EONET : {e}")

def dynamize_water_stress():
    print("🌾 NASA POWER : Calcul de l'indice d'humidité des sols en temps réel...")
    # Vos 5 points anthropologiques de tensions agro-pastorales
    strategic_points = [
        {"pays": "Chad (Zone Sahélienne)", "lon": 16.05, "lat": 12.82, "radius": 90000},
        {"pays": "Chad (Salamat / Sud)", "lon": 19.20, "lat": 10.15, "radius": 70000},
        {"pays": "Cameroon (Extrême-Nord)", "lon": 14.25, "lat": 11.20, "radius": 50000},
        {"pays": "Central African Republic (Nord)", "lon": 19.95, "lat": 8.42, "radius": 60000},
        {"pays": "Congo (Bassin Côtier / Djéno)", "lon": 11.95, "lat": -4.80, "radius": 30000}
    ]
    
    # Définition des dates pour récupérer les données d'hier (format AAAAMMJJ)
    target_date = (datetime.now() - timedelta(days=2)).strftime("%Y%m%d")
    stress_matrix = []
    
    for pt in strategic_points:
        # GWETPROF = Profile Soil Moisture (Humidité du sol globale sur toute la section racinaire)
        url = f"https://power.larc.nasa.gov/api/temporal/daily/point?parameters=GWETPROF&community=ag&longitude={pt['lon']}&latitude={pt['lat']}&start={target_date}&end={target_date}&format=json"
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                data = res.json()
                # Extraction de l'humidité (comprise entre 0.0 et 1.0)
                all_values = data.get("properties", {}).get("parameter", {}).get("GWETPROF", {})
                
                # CORRECTION ICI : Syntaxe épurée et robuste sans walrus operator défectueux
                moisture = list(all_values.values())[0] if all_values else 0.5
                
                # Traduction de l'humidité en niveau de stress prospective
                if moisture < 0.25: level, idx = "Critique (Sécheresse)", 85.0
                elif moisture < 0.45: level, idx = "Élevé (Déficit Hydrique)", 65.0
                elif moisture < 0.65: level, idx = "Modéré / Normal", 35.0
                else: level, idx = "Saturé (Excès d'eau)", 10.0
                
                stress_matrix.append({
                    "pays": pt["pays"], "level": level, "index": idx,
                    "moisture_sat": round(moisture * 100, 1),
                    "lon": pt["lon"], "lat": pt["lat"], "radius": pt["radius"]
                })
            time.sleep(1) # Courtoisie avec l'API de la NASA
        except Exception:
            # Fallback par défaut si l'API POWER coupe
            stress_matrix.append({
                "pays": pt["pays"], "level": "Donnée Satellite Indisponible", "index": 50.0,
                "moisture_sat": 40.0, "lon": pt["lon"], "lat": pt["lat"], "radius": pt["radius"]
            })
            
    with open("climate_stress_cache.json", "w", encoding="utf-8") as f:
        json.dump(stress_matrix, f, indent=4)
    print("✅ Matrice de stress hydrique mise à jour via NASA POWER.")

if __name__ == "__main__":
    collect_thermal_anomalies()
    collect_eonet_events()
    dynamize_water_stress()
