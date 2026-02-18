import pandas as pd
import requests


def load_universe():
    """
    1) Wikipedia'dan S&P500 çekmeyi dener (requests + User-Agent ile)
    2) Olmazsa repo'daki universe_us.csv'yi dener
    3) O da yoksa minimum default liste döner
    """

    # 1) Wikipedia (S&P500)
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.raise_for_status()

        # HTML string'inden tablo oku (urllib kullanmaz)
        tables = pd.read_html(r.text)
        df = tables[0]

        tickers = df["Symbol"].astype(str).str.upper().str.strip().tolist()
        # BRK.B -> BRK-B gibi (Stooq formatına uyum için)
        tickers = [t.replace(".", "-") for t in tickers]
        return tickers

    except Exception:
        pass

    # 2) Fallback: local CSV (repo'da varsa)
    try:
        df = pd.read_csv("universe_us.csv")
        col = df.columns[0]
        tickers = df[col].astype(str).str.upper().str.strip().tolist()
        tickers = [t.replace(".", "-") for t in tickers]
        return tickers
    except Exception:
        pass

    # 3) Son çare: küçük default (program tamamen çökmesin diye)
    return ["AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA", "AMD", "AVGO", "AMAT"]
