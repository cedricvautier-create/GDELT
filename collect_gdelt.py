# collect_gdelt.py
import requests
import pandas as pd
import zipfile
import io
import json

def fetch_raw_gdelt_stream():
    print("📡 GDELT Pipeline : Accès au flux de production brut (Insensible aux pannes d'API)...")
    
    # URL de l'index mis à jour toutes les 15 minutes par GDELT
    index_url = "http://data.gdeltproject.org/gdeltv2/lastupdate.txt"
    
    try:
        res = requests.get(index_url, timeout=15)
        if res.status_code != 200:
            print(f"❌ Impossible d'accéder à l'index GDELT (Code {res.status_code})")
            return
            
        # Extraction de l'URL du dernier fichier d'export d'événements
        lines = res.text.strip().split("\n")
        export_line = [l for l in lines if ".export.CSV.zip" in l][0]
        url_zip = export_line.split(" ")[2]
        print(f"📥 Téléchargement du dernier bloc de 15 minutes : {url_zip}")
        
        # Téléchargement et décompression du ZIP directement en mémoire
        r_zip = requests.get(url_zip, timeout=30)
        z = zipfile.ZipFile(io.BytesIO(r_zip.content))
        file_name = z.namelist()[0]
        
        # Chargement de la matrice GDELT 2.0 (Tabulation, pas d'en-têtes, typé en chaînes)
        df = pd.read_csv(z.open(file_name), sep="\t", header=None, dtype=str)
        
        # Nettoyage : suppression des lignes sans coordonnées valides
        # Index 53 = ActionGeo_Lat, Index 54 = ActionGeo_Long dans le schéma GDELT 2.0
        df = df.dropna(subset=[53, 54])
        
        points = []
        for _, row in df.iterrows():
            try:
                lat = float(row[53])
                lon = float(row[54])
                code = str(row[26])  # EventCode (CAMEO)
                name = str(row[50]) if pd.notna(row[50]) else "Lieu non spécifié" # ActionGeo_FullName
                url = str(row[57]) if pd.notna(row[57]) else "#" # SOURCEURL
                
                # Filtrage tactique des codes CAMEO de crise :
                # 14 = Protestations/Grèves, 18 = Assauts, 19 = Combats tactiques, 20 = Crises humanitaires
                if code.startswith(('14', '18', '19', '20')):
                    points.append({
                        "lon": lon,
                        "lat": lat,
                        "name": f"Alerte ({code}) - {name}",
                        "count": 15, # Poids par défaut pour l'affichage de la bulle WebGL
                        "radius": 45000,
                        "url": url
                    })
            except (ValueError, IndexError):
                continue
                
        # Écriture du fichier JSON final pour votre application locale
        with open("gdelt_alerts.json", "w", encoding="utf-8") as f:
            json.dump(points, f, indent=4)
        print(f"✅ Succès : {len(points)} alertes critiques extraites du flux brut avec succès.")
        
    except Exception as e:
        print(f"❌ Échec critique du traitement du flux GDELT : {e}")

if __name__ == "__main__":
    fetch_raw_gdelt_stream()
