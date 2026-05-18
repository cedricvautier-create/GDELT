# collect_gdelt.py
import requests
import pandas as pd
import zipfile
import io
import json

def fetch_gdelt_6h_window():
    print("📡 GDELT Pipeline : Analyse des 6 dernières heures de flux mondial...")
    
    # Le fichier masterfilelist contient l'historique complet de tous les blocs de 15 min
    master_url = "http://data.gdeltproject.org/gdeltv2/masterfilelist.txt"
    
    try:
        res = requests.get(master_url, timeout=20)
        if res.status_code != 200:
            print("❌ Impossible d'accéder à la liste maîtresse GDELT.")
            return
            
        # On récupère les lignes et on filtre uniquement les fichiers d'export (.export.CSV.zip)
        lines = res.text.strip().split("\n")
        export_urls = [line.split(" ")[2] for line in lines if ".export.CSV.zip" in line]
        
        # On prend les 24 derniers fichiers (24 * 15 minutes = les 6 dernières heures)
        last_6h_urls = export_urls[-24:]
        print(f"📚 {len(last_6h_urls)} blocs de 15 min identifiés. Lancement du scan...")
        
        points = []
        
        # Boucle de téléchargement des 24 fichiers
        for url_zip in last_6h_urls:
            try:
                r_zip = requests.get(url_zip, timeout=15)
                if r_zip.status_code != 200:
                    continue
                    
                z = zipfile.ZipFile(io.BytesIO(r_zip.content))
                file_name = z.namelist()[0]
                
                # Lecture rapide du CSV
                df = pd.read_csv(z.open(file_name), sep="\t", header=None, dtype=str)
                df = df.dropna(subset=[56, 57]) # Sécurité coordonnées
                
                for _, row in df.iterrows():
                    code = str(row[26])
                    
                    # On cible uniquement les codes CAMEO de crise/instabilité
                    if code.startswith(('14', '18', '19', '20')):
                        lat = float(row[56])
                        lon = float(row[57])
                        
                        # --- FILTRE GÉOGRAPHIQUE STRATÉGIQUE ---
                        # Optionnel mais recommandé : On élargit légèrement la bounding box 
                        # pour être sûr de capter toute la CEMAC (Cameroun, Gabon, Congo, Tchad, RCA, Guinée Éq.)
                        if (-10.0 <= lat <= 25.0) and (-5.0 <= lon <= 30.0):
                            name = str(row[52]) if pd.notna(row[52]) else "Afrique Centrale"
                            url = str(row[60]) if pd.notna(row[60]) else "#"
                            
                            points.append({
                                "lon": lon,
                                "lat": lat,
                                "name": f"Alerte ({code}) - {name}",
                                "count": 30, # Un peu plus gros pour la carte
                                "radius": 50000,
                                "url": url
                            })
            except Exception:
                continue # Si un fichier échoue, on passe au suivant sans planter
                
        # Sauvegarde du fichier global cumulé
        with open("gdelt_alerts.json", "w", encoding="utf-8") as f:
            json.dump(points, f, indent=4)
        print(f"✅ Terminé : {len(points)} alertes localisées en Afrique Centrale sur les 6 dernières heures.")
        
    except Exception as e:
        print(f"❌ Échec critique du traitement : {e}")

if __name__ == "__main__":
    fetch_gdelt_6h_window()
