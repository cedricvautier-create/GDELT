# collect_gdelt.py
import requests
import pandas as pd
import zipfile
import io
import json

def fetch_raw_gdelt_stream():
    print("📡 GDELT Pipeline : Accès au flux de production brut...")
    index_url = "http://data.gdeltproject.org/gdeltv2/lastupdate.txt"
    
    try:
        res = requests.get(index_url, timeout=15)
        if res.status_code != 200:
            print(f"❌ Impossible d'accéder à l'index GDELT (Code {res.status_code})")
            return
            
        lines = res.text.strip().split("\n")
        export_line = [l for l in lines if ".export.CSV.zip" in l][0]
        url_zip = export_line.split(" ")[2]
        print(f"📥 Téléchargement du bloc de 15 minutes : {url_zip}")
        
        r_zip = requests.get(url_zip, timeout=30)
        z = zipfile.ZipFile(io.BytesIO(r_zip.content))
        file_name = z.namelist()[0]
        
        # Chargement de la matrice
        df = pd.read_csv(z.open(file_name), sep="\t", header=None, dtype=str)
        
        # Alignement sur les index officiels GDELT 2.0
        # 56 = ActionGeo_Lat, 57 = ActionGeo_Long
        df = df.dropna(subset=[56, 57])
        
        points = []
        for _, row in df.iterrows():
            try:
                # Cast robuste avec les bons index
                lat = float(row[56])
                lon = float(row[57])
                code = str(row[26])  # EventCode
                name = str(row[52]) if pd.notna(row[52]) else "Lieu non spécifié" # ActionGeo_FullName
                url = str(row[60]) if pd.notna(row[60]) else "#" # SOURCEURL
                
                # Filtrage CAMEO (Crises, contestations, incidents)
                if code.startswith(('14', '18', '19', '20')):
                    points.append({
                        "lon": lon,
                        "lat": lat,
                        "name": f"Alerte ({code}) - {name}",
                        "count": 20,
                        "radius": 45000,
                        "url": url
                    })
            except (ValueError, IndexError):
                # Ignore les lignes mal formées sans bloquer le script
                continue
                
        with open("gdelt_alerts.json", "w", encoding="utf-8") as f:
            json.dump(points, f, indent=4)
        print(f"✅ Extraction réussie : {len(points)} alertes mondiales enregistrées.")
        
    except Exception as e:
        print(f"❌ Échec critique du traitement : {e}")

if __name__ == "__main__":
    fetch_raw_gdelt_stream()
