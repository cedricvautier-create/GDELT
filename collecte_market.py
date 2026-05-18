# collect_market.py
import yfinance as yf
import requests
import pandas as pd
import json
import io

def fetch_from_fred(series_id):
    """Télécharge et calcule l'historique d'une série macro FRED avec contournement du blocage User-Agent."""
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    
    # IMPÉRATIF : Simuler un navigateur pour éviter le blocage 403 de la FRED sur GitHub
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers, timeout=15)
    if response.status_code != 200:
        raise ValueError(f"FRED a rejeté la requête avec le code {response.status_code}")
        
    # Lecture du flux textuel décompressé en mémoire
    df = pd.read_csv(io.StringIO(response.text), parse_dates=['DATE'], index_col='DATE')
    
    # Sécurité : conversion numérique forcée (la FRED met des '.' pour les jours de fermeture)
    df[series_id] = pd.to_numeric(df[series_id], errors='coerce')
    df = df.dropna().sort_index()
    
    if df.empty:
        raise ValueError("Aucune donnée exploitable dans le fichier FRED après nettoyage.")
        
    val_actuel = float(df[series_id].iloc[-1])
    
    # Pivot 1 an (recherche de la date boursière la plus proche)
    target_1an = df.index[-1] - pd.DateOffset(years=1)
    idx_1an = df.index.get_indexer([target_1an], method="nearest")[0]
    val_1an = float(df[series_id].iloc[idx_1an])
    evo_1an = ((val_actuel - val_1an) / val_1an) * 100
    
    # Pivot 3 ans
    target_3ans = df.index[-1] - pd.DateOffset(years=3)
    idx_3ans = df.index.get_indexer([target_3ans], method="nearest")[0]
    val_3ans = float(df[series_id].iloc[idx_3ans])
    evo_3ans = ((val_actuel - val_3ans) / val_3ans) * 100
    
    return val_actuel, val_1an, evo_1an, val_3ans, evo_3ans

def fetch_market_trends_hybrid():
    print("📡 Extraction hybride des marchés (Yahoo Finance + FRED)...")
    
    market_items = [
        {"label": "🟡 Or ($/oz)", "source": "yahoo", "code": "GC=F", "prod": "RCA/Gabon (New York)"},
        {"label": "🪵 Indice Bois ($/1k bd ft)", "source": "yahoo", "code": "LBS=F", "prod": "Congo/Gabon/Cameroun"},
        {"label": "🏗️ Alu ($/t)", "source": "fred", "code": "PALUMUSDM", "prod": "Cameroun (FRED)"},
        {"label": "⛏️ Manganèse (Indice)", "source": "fred", "code": "WPU101707", "prod": "Gabon (FRED PPI)"},
        {"label": "🍫 Cacao ($/t)", "source": "yahoo", "code": "CC=F", "prod": "Cameroun (ICE)"},
        {"label": "☕ Café ($/lb)", "source": "yahoo", "code": "KC=F", "prod": "RCA/Cameroun"},
        {"label": "🛢️ Brent Crude ($/bbl)", "source": "yahoo", "code": "BZ=F", "prod": "Congo/Gabon/Tchad"}
    ]
    
    rows = []
    
    for item in market_items:
        try:
            if item["source"] == "yahoo":
                tk = yf.Ticker(item["code"])
                hist = tk.history(period="4y").sort_index()
                
                val_actuel = float(hist['Close'].iloc[-1])
                
                target_1an = hist.index[-1] - pd.DateOffset(years=1)
                idx_1an = hist.index.get_indexer([target_1an], method="nearest")[0]
                val_1an = float(hist['Close'].iloc[idx_1an])
                evo_1an = ((val_actuel - val_1an) / val_1an) * 100
                
                target_3ans = hist.index[-1] - pd.DateOffset(years=3)
                idx_3ans = hist.index.get_indexer([target_3ans], method="nearest")[0]
                val_3ans = float(hist['Close'].iloc[idx_3ans])
                evo_3ans = ((val_actuel - val_3ans) / val_3ans) * 100
                
            elif item["source"] == "fred":
                val_actuel, val_1an, evo_1an, val_3ans, evo_3ans = fetch_from_fred(item["code"])
                
            rows.append({
                "Matière Première": item["label"],
                "Principaux producteurs": item["prod"],
                "Cours Actuel": val_actuel,
                "Cours (Il y a 1 an)": val_1an,
                "Var. (1 an)": evo_1an,
                "Cours (Il y a 3 ans)": val_3ans,
                "Var. globale (3 ans)": evo_3ans
            })
            print(f"   -> {item['label']} mis à jour avec succès.")
            
        except Exception as e:
            print(f"   ⚠️ Échec sur {item['label']} : {e}")
            rows.append({
                "Matière Première": item["label"], "Principaux producteurs": item["prod"],
                "Cours Actuel": None, "Cours (Il y a 1 an)": None, "Var. (1 an)": None,
                "Cours (Il y a 3 ans)": None, "Var. globale (3 ans)": None
            })
            
    with open("market_data.json", "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=4)
    print("💾 Fichier historique complet market_data.json enregistré.")

if __name__ == "__main__":
    fetch_market_trends_hybrid()
