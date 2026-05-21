# collect_gdelt.py
import requests
import pandas as pd
import zipfile
import io
import json
from datetime import datetime, timedelta

def evaluate_geopolitical_impact(code, location_name):
    """
    Analyse de criticité et de sentiment géopolitique inspirée de Shadowbroker.
    Attribue un score d'impact (1 à 5) et ajuste dynamiquement l'opacité et le rayon.
    """
    code_str = str(code)
    text_upper = location_name.upper()
    
    # 1. Classification de base par code CAMEO
    if code_str.startswith(('19')):  # Combats armés, affrontements militaires
        base_score = 5
        category = "Majeur : Affrontement Armé"
        color = [211, 47, 47, 220]  # Rouge très sombre / opaque
    elif code_str.startswith('18'):  # Assauts, dynamitages, sabotages
        base_score = 4
        category = "Critique : Incident Sécuritaire"
        color = [244, 67, 54, 200]  # Rouge vif
    elif code_str.startswith('20'):  # Crises humanitaires, exodes
        base_score = 5
        category = "Majeur : Crise Humanitaire"
        color = [123, 31, 162, 220]  # Violet foncé
    elif code_str.startswith('14'):  # Mouvements sociaux, grèves, manifs
        base_score = 2
        category = "Modéré : Mouvement Social"
        color = [255, 152, 0, 160]   # Orange standard
    elif code_str.startswith(('11', '12', '13', '16')):  # Tensions politiques / diplomatiques
        base_score = 1
        category = "Faible : Tension Politique"
        color = [251, 192, 45, 140]  # Jaune / Ambre
    else:
        return None, None, None

    # 2. Raffinement du Sentiment / Criticité par analyse des mots-clés contextuels
    # Si des mots ultra-sensibles apparaissent dans le lieu ou le contexte
    critical_keywords = ["BORDER", "PORT", "MINING", "OIL", "REFINERY", "CAPITAL", "STRIKE", "ATTACK"]
    
    if any(kw in text_upper for kw in critical_keywords):
        base_score = min(5, base_score + 1) # Augmente la criticité d'un échelon
        # On assombrit la couleur pour marquer l'impact sur infrastructure stratégique
        color[3] = min(255, color[3] + 35) 

    return category, base_score, color

def fetch_gdelt_6h_sentiment():
    print("📡 GDELT Pipeline : Analyse de sentiment et criticité (Shadowbroker Engine)...")
    
    now = datetime.utcnow()
    now = now - timedelta(minutes=now.minute % 15, seconds=now.second, microseconds=now.microsecond)
    now = now - timedelta(hours=1)
    
    points = []
    success_downloads = 0
    
    for i in range(24):
        slot_time = now - timedelta(minutes=i * 15)
        slot_str = slot_time.strftime("%Y%m%d%H%M00") 
        url_zip = f"http://data.gdeltproject.org/gdeltv2/{slot_str}.export.CSV.zip"
        
        try:
            r_zip = requests.get(url_zip, timeout=12)
            if r_zip.status_code != 200: continue
                
            success_downloads += 1
            z = zipfile.ZipFile(io.BytesIO(r_zip.content))
            df = pd.read_csv(z.open(z.namelist()[0]), sep="\t", header=None, dtype=str)
            
            if df.shape[1] < 61: continue
                
            for _, row in df.iterrows():
                try:
                    if pd.isna(row[56]) or pd.isna(row[57]): continue
                    
                    lat = float(row[56])
                    lon = float(row[57])
                    
                    # Filtre Bounding Box Afrique Centrale / CEMAC
                    if (-10.0 <= lat <= 15.0) and (-5.0 <= lon <= 30.0):
                        code = str(row[26])
                        name = str(row[52]) if pd.notna(row[52]) else "Afrique Centrale"
                        
                        # Évaluation sémantique automatique
                        category, score, color = evaluate_geopolitical_impact(code, name)
                        
                        if category:
                            url = str(row[60]) if pd.notna(row[60]) else "#"
                            count = int(row[31]) if (pd.notna(row[31]) and str(row[31]).isdigit()) else 1
                            
                            # Le rayon dépend maintenant du score de criticité (plus c'est grave, plus le cercle est large)
                            calculated_radius = score * 20000 
                            
                            points.append({
                                "lon": lon,
                                "lat": lat,
                                "location_name": name,
                                "category": category,
                                "criticite_score": score, # Nouveau champ stocké
                                "color": color,
                                "radius": calculated_radius,
                                "url": url,
                                "sources": count
                            })
                except Exception:
                    continue
        except Exception:
            continue

    print(f"📊 Analyse terminée. {len(points)} alertes qualifiées par niveau d'impact.")
    
    with open("gdelt_alerts.json", "w", encoding="utf-8") as f:
        json.dump(points, f, indent=4)

if __name__ == "__main__":
    fetch_gdelt_6h_sentiment()
