import pandas as pd

def _parse_manual(text: str):
    if not text:
        return []
    tickers = [t.strip().upper() for t in text.replace(",", "\n").split("\n") if t.strip()]
    return tickers

def load_universe(mode: str, uploaded_file=None, manual_text: str=""):
    if mode == "CSV upload" and uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        cols = [c.lower() for c in df.columns]
        # ticker kolonunu bul
        if "ticker" in cols:
            c = df.columns[cols.index("ticker")]
        elif "symbol" in cols:
            c = df.columns[cols.index("symbol")]
        else:
            # ilk kolonu dene
            c = df.columns[0]
        tickers = df[c].astype(str).str.upper().str.strip().tolist()
        return [t for t in tickers if t and t != "NAN"]

    if mode == "Repo'daki universe_us.csv":
        try:
            df = pd.read_csv("universe_us.csv")
            cands = [c.lower() for c in df.columns]
            if "ticker" in cands:
                col = df.columns[cands.index("ticker")]
            elif "symbol" in cands:
                col = df.columns[cands.index("symbol")]
            else:
                col = df.columns[0]
            tickers = df[col].astype(str).str.upper().str.strip().tolist()
            return [t for t in tickers if t and t != "NAN"]
        except Exception:
            return []

    # Manual
    return _parse_manual(manual_text)
