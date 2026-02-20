import pandas as pd
import requests
import streamlit as st
import time
import os


@st.cache_data(ttl=60 * 60 * 6)  # 6 saat cache
def _fetch(symbol, api_key):
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": symbol,
        "interval": "1day",
        "outputsize": 300,
        "apikey": api_key,
        "format": "JSON",
    }
    r = requests.get(url, params=params, timeout=20)
    js = r.json()
    if js.get("status") == "error":
        return None
    return js.get("values")


class YahooProvider:
    def __init__(self, api_key=None):
        try:
            secrets_key = st.secrets["TWELVEDATA_API_KEY"]
        except Exception:
            secrets_key = None

        env_key = os.getenv("TWELVEDATA_API_KEY")
        self.api_key = api_key or secrets_key or env_key

    def history(self, ticker, start, end):
        if not self.api_key:
            return pd.DataFrame()

        symbol = str(ticker).upper()
        if symbol == "SPY":
            symbol = "SPY:NYSEARCA"

        values = _fetch(symbol, self.api_key)
        time.sleep(0.6)  # 🔴 RATE-LIMIT KORUMASI

        if not values:
            return pd.DataFrame()

        df = pd.DataFrame(values)
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
        df = df.dropna(subset=["datetime"]).set_index("datetime").sort_index()

        for c in ["open", "high", "low", "close", "volume"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")

        df = df[["open", "high", "low", "close", "volume"]].dropna()
        df = df.loc[(df.index.date >= start) & (df.index.date <= end)]
        return df
