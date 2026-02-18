import pandas as pd
import requests
import streamlit as st


class YahooProvider:
    def __init__(self):
        self.api_key = st.secrets.get("TWELVEDATA_API_KEY", None)

    def history(self, ticker, start, end):
        if not self.api_key:
            return pd.DataFrame()

        symbol = str(ticker).upper()

        # 🔴 KRİTİK DÜZELTME
        # ETF'ler için TwelveData formatı
        if symbol == "SPY":
            symbol = "SPY:NYSEARCA"

        url = "https://api.twelvedata.com/time_series"
        params = {
            "symbol": symbol,
            "interval": "1day",
            "outputsize": 2000,
            "apikey": self.api_key,
            "format": "JSON",
        }

        try:
            r = requests.get(url, params=params, timeout=20)
            js = r.json()
        except Exception:
            return pd.DataFrame()

        if not isinstance(js, dict) or js.get("status") == "error":
            return pd.DataFrame()

        values = js.get("values")
        if not values:
            return pd.DataFrame()

        df = pd.DataFrame(values)
        if df.empty:
            return pd.DataFrame()

        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
        df = df.dropna(subset=["datetime"]).set_index("datetime").sort_index()

        for c in ["open", "high", "low", "close", "volume"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")

        df = df[["open", "high", "low", "close", "volume"]].dropna()

        df = df.loc[(df.index.date >= start) & (df.index.date <= end)]
        return df
