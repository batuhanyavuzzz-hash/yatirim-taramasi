import pandas as pd


def load_universe():
    # S&P 500 tickers (Wikipedia)
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    tables = pd.read_html(url)
    df = tables[0]
    tickers = df["Symbol"].astype(str).str.upper().str.strip().tolist()

    # BRK.B gibi tickers Stooq'ta BRK-B şeklinde olur
    tickers = [t.replace(".", "-") for t in tickers]

    return tickers
