import pandas as pd
import yfinance as yf
from .provider import DataProvider

class YahooProvider(DataProvider):
    def history(self, ticker: str, start, end) -> pd.DataFrame:
        try:
            df = yf.download(
                ticker,
                start=start,
                end=end,
                auto_adjust=False,
                progress=False,
                threads=True
            )
        except Exception:
            return pd.DataFrame()

        if df is None or df.empty:
            return pd.DataFrame()

        df = df.rename(columns=str.lower)
        need = ["open", "high", "low", "close", "volume"]
        for c in need:
            if c not in df.columns:
                return pd.DataFrame()

        df = df[need].dropna()
        return df
