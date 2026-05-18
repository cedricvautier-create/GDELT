import requests
import pandas as pd
import zipfile
import io
import json
from datetime import datetime, timedelta

def get_event_semantics(code):
    """Classification stricte des codes CAMEO."""
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

def fetch_gdelt_6h_fixed():
    print("📡 GDELT Pipeline : Alignement sur les index natifs v2 (56/57)...")
    
    now = datetime.utcnow()
    now = now - timedelta(minutes=now.minute % 15, seconds=now.second, microseconds=now.microsecond)
    # Recul de sécurité d'une heure pour la mise à disposition des fichiers
    now = now - timedelta(hours=1)
    
    points = []
    success_downloads = 0
    
    print(f"⏰ Horloge UTC cible : {now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    for i in range(24):
        slot_time = now - timedelta(minutes=i * 15)
        slot_str = slot_time.strftime("%Y%m%d%H%M00") 
        url_zip = f"http://data.gdeltproject.org/gdeltv2/{slot_str}.export.CSV.zip"
        
        try:
            r_zip = requests.get(url_zip, timeout=12)
            if r_zip.status_code != 200:
                continue
                
            success_downloads += 1
            z = zipfile.ZipFile(io.BytesIO(r_zip.content))
            df = pd.read_csv(z.open(z.namelist()[0]), sep="\t", header=None, dtype=str)
            
            # Vérification de sécurité sur la taille de la matrice v2 (61 colonnes au total)
            if df.shape[1] < 61:
                continue
                
            for _, row in df.iterrows():
                try:
                    # Index GDELT 2.0 réels : 56 = Latitude, 57 = Longitude
                    if pd.isna(row[56]) or pd.isna(row[57]):
                        continue
                        
                    lat = float(row[56])
                    lon = float(row[57])
                    
                    # Filtre géographique Zone CEMAC élargie
                    if (-10.0 <= lat <= 15.0) and (-5.0 <= lon <= 30.0):
                        code = str(row[26]) # EventCode
                        category, color = get_event_semantics(code)
                        
                        if category:
                            name = str(row[52]) if pd.notna(row[52]) else "Afrique Centrale"
                            url = str(row[60]) if pd.notna(row[60]) else "#"
                            count = int(row[31]) if (pd.notna(row[31]) and str(row[31]).isdigit()) else 1
                            
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
                except Exception:
                    continue
                    
        except Exception:
            continue

    print(f"📊 Analyse terminée : {success_downloads}/24 blocs téléchargés.")
    
    with open("gdelt_alerts.json", "w", encoding="utf-8") as f:
        json.dump(points, f, indent=4)
    print(f"💾 Fichier écrit avec succès. Nombre d'alertes trouvées : {len(points)}")

if __name__ == "__main__":
    fetch_gdelt_6h_fixed()
