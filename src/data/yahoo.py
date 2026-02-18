import pandas as pd
import requests
import streamlit as st


class YahooProvider:
    """
    TwelveData provider (Streamlit Cloud uyumlu)
    SPY için exchange parametresi ZORUNLU
    """

    def __init__(self):
        try:
            self.api_key = st.secrets["TWELVEDATA_API_KEY"]
        except Exception:
            self.api_key = None

    def history(self, ticker, start, end):
        if not self.api_key:
            return pd.DataFrame()

        symbol = str(ticker).upper()

        params = {
            "symbol": symbol,
            "interval": "1day",
            "outputsize": 5000,
            "apikey": self.api_key,
            "format": "JSON",
        }

        # 🔴 KRİTİK: SPY için exchange belirt
        if symbol == "SPY":
            params["exchange"] = "NYSEARCA"

        url = "https://api.twelvedata.com/time_series"

        try:
            r = requests.get(url, params=params, timeout=20)
            js = r.json()
        except Exception:
            return pd.DataFrame()

        # API error
        if not isinstance(js, dict) or js.get("status") == "error":
            return pd.DataFrame()

        values = js.get("values")
        if not values:
            return pd.DataFrame()

        df = pd.DataFrame(values)
        if df.empty:
            return pd.DataFrame()

        # normalize
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
        df = df.dropna(subset=["datetime"]).set_index("datetime").sort_index()

        for c in ["open", "high", "low", "close", "volume"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")

        df = df[["open", "high", "low", "close", "volume"]].dropna()

        # tarih filtresi
        df = df.loc[(df.index.date >= start) & (df.index.date <= end)]

        return df
