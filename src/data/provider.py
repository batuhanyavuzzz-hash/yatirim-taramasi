from dataclasses import dataclass
import pandas as pd

class DataProvider:
    def history(self, ticker: str, start, end) -> pd.DataFrame:
        raise NotImplementedError

@dataclass
class YahooProvider(DataProvider):
    def history(self, ticker: str, start, end) -> pd.DataFrame:
        import yfinance as yf
        df = yf.download(ticker, start=start, end=end, auto_adjust=False, progress=False)
        if df is None or df.empty:
            return pd.DataFrame()
        df = df.rename(columns=str.lower)
        # expected cols: open high low close volume
        return df[["open","high","low","close","volume"]].dropna()
