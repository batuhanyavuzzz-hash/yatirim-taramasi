import yfinance as yf
import pandas as pd

class YahooProvider:
    def history(self, ticker, start, end):
        df = yf.download(ticker, start=start, end=end, progress=False)
        if df is None or df.empty:
            return pd.DataFrame()
        df = df.rename(columns=str.lower)
        return df[["open","high","low","close","volume"]].dropna()
