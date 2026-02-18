import pandas as pd
import requests


class YahooProvider:
    """
    Streamlit Cloud'da yfinance sık sık 0 data döndürüyor.
    Bu provider Stooq (HTTP CSV) üzerinden günlük veriyi çeker.
    ABD hisseleri için ticker formatı: AAPL, NVDA, AMAT...
    Stooq sembol formatı: aapl.us
    """

    def history(self, ticker, start, end):
        symbol = f"{str(ticker).strip().lower()}.us"
        url = f"https://stooq.com/q/d/l/?s={symbol}&i=d"

        try:
            r = requests.get(url, timeout=15)
            if r.status_code != 200:
                return pd.DataFrame()
            text = r.text
            if "Date,Open,High,Low,Close,Volume" not in text:
                return pd.DataFrame()
            df = pd.read_csv(pd.compat.StringIO(text))
        except Exception:
            # pandas compat değişebiliyor; fallback
            try:
                import io
                df = pd.read_csv(io.StringIO(text))
            except Exception:
                return pd.DataFrame()

        if df is None or df.empty:
            return pd.DataFrame()

        # kolonları normalize et
        df.columns = [c.strip().lower() for c in df.columns]
        need = {"date", "open", "high", "low", "close", "volume"}
        if not need.issubset(set(df.columns)):
            return pd.DataFrame()

        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"]).set_index("date").sort_index()

        # date aralığı uygula
        df = df.loc[(df.index.date >= start) & (df.index.date <= end)]

        df = df[["open", "high", "low", "close", "volume"]].dropna()
        return df
