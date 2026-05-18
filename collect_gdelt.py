# collect_gdelt.py
import requests
import pandas as pd
import zipfile
import io
import json
from datetime import datetime, timedelta

def get_event_semantics(code):
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

def fetch_gdelt_6h_diagnostique():
    print("📡 GDELT Pipeline : Initialisation du scan de 6 heures...")
    
    # Heure actuelle UTC
    now = datetime.utcnow()
    # Arrondi strict à la tranche de 15 minutes précédente
    now = now - timedelta(minutes=now.minute % 15, seconds=now.second, microseconds=now.microsecond)
    
    # Décryptage de sécurité : On recule d'une heure supplémentaire au départ 
    # pour pallier les retards fréquents de réplication des serveurs GDELT
    now = now - timedelta(hours=1)
    
    points = []
    success_downloads = 0
    
    print(f"⏰ Heure de départ du scan (UTC) : {now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    for i in range(24):
        slot_time = now - timedelta(minutes=i * 15)
        slot_str = slot_time.strftime("%Y%m%d%H%M00") 
        url_zip = f"http://data.gdeltproject.org/gdeltv2/{slot_str}.export.CSV.zip"
        
        print(f"🔍 [Bloc {i+1}/24] Requête : {url_zip}")
        
        try:
            r_zip = requests.get(url_zip, timeout=12)
            print(f"    -> Statut HTTP : {r_zip.status_code}")
            
            if r_zip.status_code != 200:
                continue
                
            success_downloads += 1
            z = zipfile.ZipFile(io.BytesIO(r_zip.content))
            file_name = z.namelist()[0]
            
            # Lecture ultra-tolérante (sans dropna initial pour éviter les KeyErrors)
            df = pd.read_csv(z.open(file_name), sep="\t", header=None, dtype=str)
            
            # Sécurité : Vérification que le fichier possède bien les colonnes nécessaires
            if df.shape[1] < 58:
                print(f"    ⚠️ Structure incorrecte ({df.shape[1]} colonnes détectées).")
                continue
                
            block_matches = 0
            for _, row in df.iterrows():
                try:
                    # Index de repli dynamique (on teste 53/54, sinon 56/57)
                    lat_raw = row[53] if pd.notna(row[53]) else row[56]
                    lon_raw = row[54] if pd.notna(row[54]) else row[57]
                    
                    if pd.isna(lat_raw) or pd.isna(lon_raw):
                        continue
                        
                    lat = float(lat_raw)
                    lon = float(lon_raw)
                    
                    # --- FILTRE AFRIQUE CENTRALE ---
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
                            block_matches += 1
                except Exception:
                    continue
            
            if block_matches > 0:
                print(f"    🎯 OK : {block_matches} alertes extraites de ce bloc.")
                
        except Exception as e_bloc:
            print(f"    ❌ Erreur de traitement sur ce bloc : {e_bloc}")
            continue

    print(f"📊 Résumé : {success_downloads}/24 fichiers téléchargés avec succès.")
    
    # Écriture forcée, même si la liste est vide pour éviter le crash de Git
    with open("gdelt_alerts.json", "w", encoding="utf-8") as f:
        json.dump(points, f, indent=4)
    print(f"💾 Fin du script. {len(points)} alertes totales poussées dans gdelt_alerts.json.")

if __name__ == "__main__":
    fetch_gdelt_6h_diagnostique()
            
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
