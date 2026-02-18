import pandas as pd
import requests


def load_universe():
    """
    S&P500 içinden likit ilk 120 hisseyi alır
    (TwelveData free plan için güvenli)
    """
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    r = requests.get(url, headers=headers, timeout=20)
    tables = pd.read_html(r.text)
    df = tables[0]

    tickers = df["Symbol"].astype(str).str.upper().tolist()

    # TwelveData uyumu
    tickers = [t.replace(".", "-") for t in tickers]

    # 🔴 KRİTİK: SADECE İLK 120
    return tickers[:120]
