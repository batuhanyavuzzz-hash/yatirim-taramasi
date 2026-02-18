import pandas as pd
import requests
import streamlit as st


class YahooProvider:
    """
    TwelveData üzerinden günlük OHLCV çeker.
    Streamlit Cloud'da çalışır (API key gerekir).
    """

    def __init__(self):
        self.api_key = None
        # Streamlit Secrets
        try:
            self.api_key = st.secrets.get("TWELVEDATA_API_KEY")
        except Exception:
            self.api_key = None

    def history(self, ticker, start, end):
        if not self.api_key:
            return pd.DataFrame()

        symbol = str(ticker).strip().upper()

        # TwelveData time_series endpoint
        url = "https://api.twelvedata.com/time_series"
        params = {
            "symbol": symbol,
            "interval": "1day",
            "outputsize": 5000,
            "apikey": self.api_key,
            "format": "JSON",
        }

        try:
            r = requests.get(url, params=params, timeout=20)
            if r.status_code != 200:
                return pd.DataFrame()
            js = r.json()
        except Exception:
            return pd.DataFrame()

        # error handling
        if isinstance(js, dict) and js.get("status") == "error":
            return pd.DataFrame()

        values = js.get("values")
        if not values:
            return pd.DataFrame()

        # values: list of dicts with datetime, open, high, low, close, volume
        df = pd.DataFrame(values)
        if df.empty:
            return pd.DataFrame()

        # normalize
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
        df = df.dropna(subset=["datetime"]).set_index("datetime").sort_index()

        for c in ["open", "high", "low", "close", "volume"]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")

        df = df[["open", "high", "low", "close", "volume"]].dropna()

        # date filter (start/end are datetime.date)
        df = df.loc[(df.index.date >= start) & (df.index.date <= end)]

        return df
