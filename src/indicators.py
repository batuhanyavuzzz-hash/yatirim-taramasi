import pandas as pd

def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def atr(df, n=14):
    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)
    return tr.rolling(n).mean()

def rs_score(asset, benchmark):
    r3  = asset.iloc[-1] / asset.iloc[-63]  - 1
    r6  = asset.iloc[-1] / asset.iloc[-126] - 1
    r12 = asset.iloc[-1] / asset.iloc[-252] - 1

    b3  = benchmark.iloc[-1] / benchmark.iloc[-63]  - 1
    b6  = benchmark.iloc[-1] / benchmark.iloc[-126] - 1
    b12 = benchmark.iloc[-1] / benchmark.iloc[-252] - 1

    return 0.4*(r3-b3) + 0.3*(r6-b6) + 0.3*(r12-b12)
