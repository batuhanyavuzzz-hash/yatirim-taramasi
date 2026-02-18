import pandas as pd
import requests
import streamlit as st


class YahooProvider:
    """
    TwelveData provider with diagnostics.
    """

    def __init__(self):
        self.api_key = None
        try:
            # Secrets MUST be exactly this key
            self.api_key = st.secrets["TWELVEDATA_API_KEY"]
        except Exception:
            self.api_key = None

        # diagnostics holder
        self.last_diag = {}

    def _call(self, symbol: str):
        url = "https://api.twelvedata.com/time_series"
        params = {
            "symbol": symbol,
            "interval": "1day",
            "outputsize": 200,
            "apikey": self.api_key or "",
            "format": "JSON",
        }
        # try common exchanges for ETF
        if symbol == "SPY":
            params["exchange"] = "NYSEARCA"

        try:
            r = requests.get(url, params=params, timeout=20)
            self.last_diag = {
                "http_status": r.status_code,
                "url": r.url[:2000],  # just in case
            }
            js = r.json()
            self.last_diag["json_keys"] = list(js.keys()) if isinstance(js, dict) else str(type(js))
            self.last_diag["json_head"] = js if isinstance(js, dict) else {"raw": str(js)[:500]}
            return js
        except Exception as e:
            self.last_diag = {"exception": str(e)}
            return None

    def history(self, ticker, start, end):
        if not self.api_key:
            self.last_diag = {"error": "NO_API_KEY (TWELVEDATA_API_KEY missing in secrets)"}
            return pd.DataFrame()

        symbol = str(ticker).strip().upper()

        js = self._call(symbol)
        if js is None or not isinstance(js, dict):
            return pd.DataFrame()

        # API-level error
        if js.get("status") == "error":
            # keep the message in diag
            self.last_diag["api_error"] = js
            return pd.DataFrame()

        values = js.get("values")
        if not values:
            self.last_diag["no_values"] = True
            return pd.DataFrame()

        df = pd.DataFrame(values)
        if df.empty:
            self.last_diag["df_empty_after_values"] = True
            return pd.DataFrame()

        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
        df = df.dropna(subset=["datetime"]).set_index("datetime").sort_index()

        for c in ["open", "high", "low", "close", "volume"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")

        df = df[["open", "high", "low", "close", "volume"]].dropna()

        # date filter
        df = df.loc[(df.index.date >= start) & (df.index.date <= end)]
        return df
