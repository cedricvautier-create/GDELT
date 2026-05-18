# collect_gdelt.py
import requests
import pandas as pd
import zipfile
import io
import json

def get_event_semantics(code):
    """Associe un code CAMEO à une catégorie et une couleur spécifique."""
    if code.startswith(('18', '19')):
        return "Sécurité & Affrontement", [255, 0, 0, 180]        # Rouge
    elif code.startswith('14'):
        return "Mouvement Social (Grève, Manif)", [255, 140, 0, 180] # Orange
    elif code.startswith('20'):
        return "Crise Humanitaire", [147, 112, 219, 180]             # Violet
    elif code.startswith(('11', '12', '13', '16')):
        return "Tension Politique & Inter.", [255, 215, 0, 180]      # Jaune/Or
    return None, None

def fetch_gdelt_6h_classified():
    print("📡 GDELT Pipeline : Analyse sémantique des 6 dernières heures...")
    master_url = "http://data.gdeltproject.org/gdeltv2/masterfilelist.txt"
    
    try:
        res = requests.get(master_url, timeout=20)
        if res.status_code != 200: return
            
        lines = res.text.strip().split("\n")
        export_urls = [line.split(" ")[2] for line in lines if ".export.CSV.zip" in line]
        
        # Scan des 6 dernières heures (24 blocs de 15 min)
        last_6h_urls = export_urls[-24:]
        points = []
        
        for url_zip in last_6h_urls:
            try:
                r_zip = requests.get(url_zip, timeout=15)
                if r_zip.status_code != 200: continue
                    
                z = zipfile.ZipFile(io.BytesIO(r_zip.content))
                df = pd.read_csv(z.open(z.namelist()[0]), sep="\t", header=None, dtype=str)
                df = df.dropna(subset=[56, 57])
                
                for _, row in df.iterrows():
                    code = str(row[26])
                    category, color = get_event_semantics(code)
                    
                    # Si l'événement correspond à l'une de vos 4 catégories
                    if category:
                        lat = float(row[56])
                        lon = float(row[57])
                        
                        # Bounding box élargie Afrique Centrale
                        if (-10.0 <= lat <= 25.0) and (-5.0 <= lon <= 30.0):
                            name = str(row[52]) if pd.notna(row[52]) else "Lieu non spécifié"
                            url = str(row[60]) if pd.notna(row[60]) else "#"
                            count = int(row[34]) if pd.notna(row[34]) else 1 # Nombre de mentions
                            
                            points.append({
                                "lon": lon,
                                "lat": lat,
                                "location_name": name,
                                "category": category,
                                "color": color, # La couleur est stockée ici
                                "radius": min(120000, max(25000, count * 3000)),
                                "url": url,
                                "sources": count
                            })
            except Exception:
                continue
                
        with open("gdelt_alerts.json", "w", encoding="utf-8") as f:
            json.dump(points, f, indent=4)
        print(f"✅ Analyse terminée : {len(points)} alertes qualifiées et colorées.")
        
    except Exception as e:
        print(f"❌ Échec critique : {e}")

if __name__ == "__main__":
    fetch_gdelt_6h_classified()
