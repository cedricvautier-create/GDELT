# collect_market.py (Sur GitHub)
import yfinance as yf
import pandas as pd
import json

def fetch_market_trends():
    print("📡 Extraction des tendances de marché via Yahoo Finance (Cloud)...")
    
    market_items = [
        {"label": "🛢️ Brent Crude ($/bbl)", "ticker": "BZ=F", "prod": "Congo/Gabon/Tchad"},
        {"label": "🟡 Or ($/oz)", "ticker": "GC=F", "prod": "RCA/Gabon"},
        {"label": "🪵 Indice Bois ($/1k bd ft)", "ticker": "LBS=F", "prod": "Congo/Gabon/Cameroun"},
        {"label": "🍫 Cacao ($/t)", "ticker": "CC=F", "prod": "Cameroun"},
        {"label": "☕ Café ($/lb)", "ticker": "KC=F", "prod": "RCA/Cameroun"}
    ]
    
    rows = []
    for item in market_items:
        try:
            tk = yf.Ticker(item["ticker"])
            hist = tk.history(period="4y").sort_index()
            
            if not hist.empty and len(hist) > 20:
                val_actuel = float(hist['Close'].iloc[-1])
                
                target_1an = hist.index[-1] - pd.DateOffset(years=1)
                idx_1an = hist.index.get_indexer([target_1an], method="nearest")[0]
                val_1an = float(hist['Close'].iloc[idx_1an])
                evo_1an = ((val_actuel - val_1an) / val_1an) * 100
                
                target_3ans = hist.index[-1] - pd.DateOffset(years=3)
                idx_3ans = hist.index.get_indexer([target_3ans], method="nearest")[0]
                val_3ans = float(hist['Close'].iloc[idx_3ans])
                evo_3ans = ((val_actuel - val_3ans) / val_3ans) * 100
                
                rows.append({
                    "Matière Première": item["label"],
                    "Principaux producteurs": item["prod"],
                    "Cours Actuel": val_actuel,
                    "Cours (Il y a 1 an)": val_1an,
                    "Var. (1 an)": evo_1an,
                    "Cours (Il y a 3 ans)": val_3ans,
                    "Var. globale (3 ans)": evo_3ans
                })
        except Exception as e:
            print(f"⚠️ Échec sur {item['label']} : {e}")
            
    with open("market_data.json", "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=4)
    print("✅ Fichier partiel market_data.json sauvegardé.")

if __name__ == "__main__":
    fetch_market_trends()
