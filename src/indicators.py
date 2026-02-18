import pandas as pd
import numpy as np

def ema(s: pd.Series, span: int) -> pd.Series:
    return s.ewm(span=span, adjust=False).mean()

def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([(high-low), (high-prev_close).abs(), (low-prev_close).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()

def rs_score(asset_close: pd.Series, bench_close: pd.Series) -> float:
    # 3/6/12 ay relatif performans: (asset - benchmark)
    def ret(s: pd.Series, d: int):
        if len(s) <= d:
            return None
        return (s.iloc[-1] / s.iloc[-d] - 1.0)

    periods = [63, 126, 252]  # ~3m, 6m, 12m
    weights = [0.4, 0.3, 0.3]

    score = 0.0
    for p, w in zip(periods, weights):
        a = ret(asset_close, p)
        b = ret(bench_close, p)
        if a is None or b is None:
            return float("nan")
        score += w * (a - b)

    return float(score)

def pct(x: float, y: float) -> float:
    # (x - y) / y * 100
    if y == 0 or pd.isna(y) or pd.isna(x):
        return float("nan")
    return float((x - y) / y * 100.0)
