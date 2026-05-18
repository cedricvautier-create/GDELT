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

def fetch_gdelt_6h_final():
    print("📡 GDELT Pipeline : Initialisation de la fenêtre de 6 heures (Schéma v2)...")
    
    now = datetime.utcnow()
    now = now - timedelta(minutes=now.minute % 15, seconds=now.second, microseconds=now.microsecond)
    # Recul de sécurité pour la réplication des serveurs de la NASA/GDELT
    now = now - timedelta(hours=1)
    
    points = []
    success_downloads = 0
    total_rows_processed = 0
    
    print(f"⏰ Horloge UTC de référence : {now.strftime('%Y-%m-%d %H:%M:%S')}")
    
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
            
            # Vérification de la présence des colonnes géographiques v2
            if df.shape[1] < 59:
                continue
                
            for _, row in df.iterrows():
                total_rows_processed += 1
                try:
                    # Index officiels GDELT v2 : 57 = ActionGeo_Lat, 58 = ActionGeo_Long
                    if pd.isna(row[57]) or pd.isna(row[58]):
                        continue
                        
                    lat = float(row[57])
                    lon = float(row[58])
                    
                    # Filtre strict Zone CEMAC / Afrique Centrale élargie
                    if (-10.0 <= lat <= 15.0) and (-5.0 <= lon <= 30.0):
                        code = str(row[26]) # EventCode
                        category, color = get_event_semantics(code)
                        
                        if category:
                            name = str(row[54]) if pd.notna(row[54]) else "Afrique Centrale"
                            url = str(row[61]) if (len(row) > 61 and pd.notna(row[61])) else "#"
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
    print(f"🔍 {total_rows_processed} lignes mondiales analysées au total.")
    
    with open("gdelt_alerts.json", "w", encoding="utf-8") as f:
        json.dump(points, f, indent=4)
    print(f"💾 Fichier gdelt_alerts.json écrit avec {len(points)} alertes qualifiées en Afrique Centrale.")

if __name__ == "__main__":
    fetch_gdelt_6h_final()
