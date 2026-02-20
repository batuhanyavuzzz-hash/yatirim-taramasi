import pandas as pd
import requests


def _normalize_tickers(tickers):
    return [str(t).upper().replace(".", "-") for t in tickers if str(t).strip()]


def load_universe(limit=120, fallback_csv="universe_us.csv"):
    """
    Öncelik: S&P500 listesinden ticker çek.
    Hata olursa depodaki CSV dosyasına düş.
    """
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.raise_for_status()
        tables = pd.read_html(r.text)
        df = tables[0]
        tickers = _normalize_tickers(df["Symbol"].tolist())
        if tickers:
            return tickers[:limit]
    except Exception:
        pass

    df = pd.read_csv(fallback_csv)
    col = "ticker" if "ticker" in df.columns else df.columns[0]
    tickers = _normalize_tickers(df[col].tolist())
    return tickers[:limit]
