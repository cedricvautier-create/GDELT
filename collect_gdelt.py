# collect_market.py ou collect_gdelt.py (sur GitHub)
import requests
import pandas as pd
import zipfile
import io
import json
import math
from datetime import datetime, timedelta

# Liste blanche des domaines de confiance géopolitique mondiale et panafricaine
TRUSTED_DOMAINS = [
    "reuters.com", "afp.com", "jeuneafrique.com", "lemonde.fr", "bbc.com", 
    "bloomberg.com", "dw.com", "aljazeera.com", "rfi.fr", "africanews.com",
    "allafrica.com", "reutersagency.com", "france24.com", "apnews.com"
]

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calcule la distance en kilomètres entre deux coordonnées géographiques."""
    R = 6371.0
    rlat1, rlon1 = math.radians(lat1), math.radians(lon1)
    rlat2, rlon2 = math.radians(lat2), math.radians(lon2)
    
    dlat = rlat2 - rlat1
    dlon = rlon2 - rlon1
    
    a = math.sin(dlat / 2)**2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def evaluate_source_reliability(url):
    """Évalue la fiabilité du domaine média."""
    if not url or url == "#":
        return "Inconnue", 0
    
    url_lower = url.lower()
    if any(domain in url_lower for domain in TRUSTED_DOMAINS):
        return "Élevée (Média de Référence) 🟢", 2
    return "Standard (À corroborer) 🟡", 0

def evaluate_geopolitical_impact(code, location_name, url):
    """Analyse de criticité CAMEO enrichie par le score de confiance."""
    code_str = str(code)
    text_upper = location_name.upper()
    
    if code_str.startswith('19'):
        base_score, category, color = 5, "Majeur : Affrontement Armé", [211, 47, 47, 220]
    elif code_str.startswith('18'):
        base_score, category, color = 4, "Critique : Incident Sécuritaire", [244, 67, 54, 200]
    elif code_str.startswith('20'):
        base_score, category, color = 5, "Majeur : Crise Humanitaire", [123, 31, 162, 220]
    elif code_str.startswith('14'):
        base_score, category, color = 2, "Modéré : Mouvement Social", [255, 152, 0, 160]
    elif code_str.startswith(('11', '12', '13', '16')):
        base_score, category, color = 1, "Faible : Tension Politique", [251, 192, 45, 140]
    else:
        return None, None, None, None

    # Ajustement sémantique contextuel
    critical_keywords = ["BORDER", "PORT", "MINING", "OIL", "REFINERY", "CAPITAL", "STRIKE", "ATTACK"]
    if any(kw in text_upper for kw in critical_keywords):
        base_score = min(5, base_score + 1)
        color[3] = min(255, color[3] + 35)

    reliability_label, bonus = evaluate_source_reliability(url)
    base_score = min(5, base_score + bonus)
    
    return category, base_score, color, reliability_label

def fetch_gdelt_with_cross_verifications():
    print("📡 Lancement du pipeline GDELT avec verrous de confiance...")
    
    # 1. Téléchargement discret ou chargement du cache ACLED s'il existe sur le dépôt
    acled_events = []
    try:
        # Tente de charger le cache ACLED généré par votre autre script pour le croisement spatial
        if io.os.path.exists("acled_cache.csv"):
            df_acled = pd.read_csv("acled_cache.csv")
            if not df_acled.empty and 'latitude' in df_acled.columns:
                acled_events = df_acled[['latitude', 'longitude']].dropna().to_dict('records')
                print(f"✅ {len(acled_events)} points ACLED chargés pour le croisement spatial.")
    except Exception as e:
        print(f"⚠️ Impossible de croiser avec ACLED : {e}")

    now = datetime.utcnow()
    now = now - timedelta(minutes=now.minute % 15, seconds=now.second, microseconds=now.microsecond)
    now = now - timedelta(hours=1)
    
    points = []
    
    for i in range(24): # Analyse des dernières 6 heures
        slot_str = (now - timedelta(minutes=i * 15)).strftime("%Y%m%d%H%M00")
        url_zip = f"http://data.gdeltproject.org/gdeltv2/{slot_str}.export.CSV.zip"
        
        try:
            r_zip = requests.get(url_zip, timeout=10)
            if r_zip.status_code != 200: continue
            
            z = zipfile.ZipFile(io.BytesIO(r_zip.content))
            df = pd.read_csv(z.open(z.namelist()[0]), sep="\t", header=None, dtype=str)
            
            if df.shape[1] < 61: continue
                
            for _, row in df.iterrows():
                if pd.isna(row[56]) or pd.isna(row[57]): continue
                lat, lon = float(row[56]), float(row[57])
                
                # Zone d'intérêt Afrique Centrale (CEMAC)
                if (-10.0 <= lat <= 15.0) and (-5.0 <= lon <= 30.0):
                    url = str(row[60]) if pd.notna(row[60]) else "#"
                    name = str(row[52]) if pd.notna(row[52]) else "Zone CEMAC"
                    code = str(row[26])
                    count = int(row[31]) if (pd.notna(row[31]) and str(row[31]).isdigit()) else 1
                    
                    category, score, color, reliability = evaluate_geopolitical_impact(code, name, url)
                    
                    if category:
                        # VERROU 1 : Validation de proximité avec ACLED
                        validated_by_acled = False
                        for ev in acled_events:
                            dist = haversine_distance(lat, lon, float(ev['latitude']), float(ev['longitude']))
                            if dist <= 50.0: # Rayon de tolérance de 50 km
                                validated_by_acled = True
                                break
                        
                        verification_status = "🛡️ Validée par ACLED Terrain" if validated_by_acled else "📡 Signal Média Spéculatif"
                        
                        # FILTRE ANTI-BRUIT : On élimine les signaux faibles (score < 3) non confirmés et sans source de référence
                        if score < 3 and not validated_by_acled and "Reference" not in reliability:
                            continue
                            
                        points.append({
                            "lon": lon, "lat": lat, "location_name": name,
                            "category": category, "criticite_score": score,
                            "color": color, "radius": score * 20000, "url": url, "sources": count,
                            "reliability": reliability, "verification_status": verification_status
                        })
        except Exception:
            continue

    print(f"💾 Sauvegarde de {len(points)} alertes hautement qualifiées.")
    with open("gdelt_alerts.json", "w", encoding="utf-8") as f:
        json.dump(points, f, indent=4)

if __name__ == "__main__":
    fetch_gdelt_with_cross_verifications()
