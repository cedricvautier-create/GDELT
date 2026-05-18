# collect_gdelt.py
import requests
import pandas as pd
import zipfile
import io
import json
from datetime import datetime, timedelta

def get_event_semantics(code):
    """Classification des codes CAMEO selon les 4 catégories demandées."""
    code_str = str(code)
    if code_str.startswith(('18', '19')):
        return "Sécurité & Affrontement", [255, 0, 0, 180]        # Rouge
    elif code_str.startswith('14'):
        return "Mouvement Social (Grève, Manif)", [255, 140, 0, 180] # Orange
    elif code_str.startswith('20'):
        return "Crise Humanitaire", [147, 112, 219, 180]             # Violet
    elif code_str.startswith(('11', '12', '13', '16')):
        return "Tension Politique & Inter.", [255, 215, 0, 180]      # Jaune/Or
    return None, None

def fetch_gdelt_6h_smart():
    print("📡 GDELT Pipeline : Génération de la fenêtre glissante de 6 heures...")
    
    # Récupération du moment actuel en UTC (Heure de référence GDELT)
    now = datetime.utcnow()
    # Arrondi à la tranche de 15 minutes inférieure
    now = now - timedelta(minutes=now.minute % 15, seconds=now.second, microseconds=now.microsecond)
    
    points = []
    blocks_scanned = 0
    
    print("📥 Début du scan des 24 derniers blocs de production...")
    for i in range(24):
        slot_time = now - timedelta(minutes=i * 15)
        # Formatage du nom de fichier requis par GDELT (les secondes sont toujours 00)
        slot_str = slot_time.strftime("%Y%m%d%H%M00") 
        url_zip = f"http://data.gdeltproject.org/gdeltv2/{slot_str}.export.CSV.zip"
        
        try:
            r_zip = requests.get(url_zip, timeout=10)
            if r_zip.status_code != 200:
                continue # Fichier non encore généré ou manquant, on passe au suivant
                
            blocks_scanned += 1
            z = zipfile.ZipFile(io.BytesIO(r_zip.content))
            file_name = z.namelist()[0]
            
            # Lecture brute de la matrice
            df = pd.read_csv(z.open(file_name), sep="\t", header=None, dtype=str)
            
            # Index officiels GDELT : 53=Latitude, 54=Longitude
            df = df.dropna(subset=[53, 54])
            
            block_matches = 0
            for _, row in df.iterrows():
                try:
                    lat = float(row[53])
                    lon = float(row[54])
                    
                    # --- FILTRE GÉOGRAPHIQUE AFRIQUE CENTRALE (ZONE CEMAC EXTENDED) ---
                    if (-10.0 <= lat <= 15.0) and (-5.0 <= lon <= 30.0):
                        code = str(row[26]) # Code CAMEO de l'action
                        category, color = get_event_semantics(code)
                        
                        if category:
                            name = str(row[50]) if pd.notna(row[50]) else "Afrique Centrale"
                            url = str(row[57]) if pd.notna(row[57]) else "#"
                            count = int(row[31]) if pd.notna(row[31]) else 1 # Nombre de mentions (Index 31)
                            
                            points.append({
                                "lon": lon,
                                "lat": lat,
                                "location_name": name,
                                "category": category,
                                "color": color,
                                "radius": min(120000, max(25000, count * 3500)),
                                "url": url,
                                "sources": count
                            })
                            block_matches += 1
                except (ValueError, IndexError):
                    continue
            
            if block_matches > 0:
                print(f"   -> Bloc {slot_str} : {block_matches} alertes qualifiées identifiées.")
                
        except Exception:
            continue

    print(f"📊 Fin de l'analyse. {blocks_scanned} paquets inspectés.")
    
    # Écriture finale sécurisée
    with open("gdelt_alerts.json", "w", encoding="utf-8") as f:
        json.dump(points, f, indent=4)
    print(f"💾 Fichier sauvegardé avec {len(points)} alertes pour l'Afrique Centrale.")

if __name__ == "__main__":
    fetch_gdelt_6h_smart()
