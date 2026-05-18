import requests
import pandas as pd
import zipfile
import io
import json
from datetime import datetime, timedelta

def get_event_semantics(code):
    """Classification des codes CAMEO selon les catégories demandées."""
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

def fetch_gdelt_6h_clean():
    print("📡 GDELT Pipeline : Initialisation du scan de 6 heures...")
    
    # Configuration du décalage temporel pour coller aux serveurs GDELT
    now = datetime.utcnow()
    now = now - timedelta(minutes=now.minute % 15, seconds=now.second, microseconds=now.microsecond)
    now = now - timedelta(hours=1)
    
    points = []
    success_downloads = 0
    
    print(f"⏰ Heure de départ du scan (UTC) : {now.strftime('%Y-%m-%d %H:%M:%S')}")
    
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
            file_name = z.namelist()[0]
            
            # Lecture du fichier de production
            df = pd.read_csv(z.open(file_name), sep="\t", header=None, dtype=str)
            
            if df.shape[1] < 58:
                continue
                
            for _, row in df.iterrows():
                try:
                    # Extraction des coordonnées géographiques natives
                    lat_raw = row[53] if pd.notna(row[53]) else row[56]
                    lon_raw = row[54] if pd.notna(row[54]) else row[57]
                    
                    if pd.isna(lat_raw) or pd.isna(lon_raw):
                        continue
                        
                    lat = float(lat_raw)
                    lon = float(lon_raw)
                    
                    # Filtre géographique strict sur la zone Afrique Centrale / CEMAC
                    if (-10.0 <= lat <= 15.0) and (-5.0 <= lon <= 30.0):
                        code = str(row[26])
                        category, color = get_event_semantics(code)
                        
                        if category:
                            name = str(row[50]) if pd.notna(row[50]) else "Afrique Centrale"
                            url = str(row[57]) if pd.notna(row[57]) else "#"
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

    print(f"📊 Résumé : {success_downloads}/24 fichiers traités.")
    
    with open("gdelt_alerts.json", "w", encoding="utf-8") as f:
        json.dump(points, f, indent=4)
    print(f"💾 Fin du traitement. {len(points)} alertes enregistrées.")

if __name__ == "__main__":
    fetch_gdelt_6h_clean()
