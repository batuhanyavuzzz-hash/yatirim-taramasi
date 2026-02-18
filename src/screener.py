import pandas as pd
import numpy as np

from src.indicators import ema, atr, rs_score
from src.risk import risk_plan


def run_screen(tickers, provider, start, end):

    benchmark = provider.history("SPY", start, end)
    if benchmark.empty:
        return pd.DataFrame()

    results = []

    for t in tickers:
        df = provider.history(t, start, end)

        if df.empty or len(df) < 260:
            continue

        close = df["close"]

        df["ema50"] = ema(close, 50)
        df["ema150"] = ema(close, 150)
        df["ema200"] = ema(close, 200)
        df["atr14"] = atr(df, 14)

        last = df.iloc[-1]
        price = float(last["close"])

        ema50 = float(last["ema50"])
        ema150 = float(last["ema150"])
        ema200 = float(last["ema200"])

        # 1️⃣ Trend Template
        if not (price > ema50 and ema50 > ema150 and ema150 > ema200):
            continue

        # 2️⃣ EMA200 slope
        ema200_now = float(df["ema200"].iloc[-1])
        ema200_prev = float(df["ema200"].iloc[-21])

        if ema200_now <= ema200_prev:
            continue

        # 3️⃣ Likidite
        avg_vol20 = float(df["volume"].rolling(20).mean().iloc[-1])
        if avg_vol20 < 1_000_000:
            continue

        # 4️⃣ Volatilite
        atr_pct = (float(last["atr14"]) / price) * 100
        if atr_pct < 2 or atr_pct > 10:
            continue

        # 5️⃣ 52W high proximity
        high_52w = float(df["high"].rolling(252).max().iloc[-1])
        dist_pct = (high_52w - price) / high_52w * 100
        if dist_pct > 20:
            continue

        # 6️⃣ Relative Strength
        rs = rs_score(close, benchmark["close"])
        if rs < 0.10:
            continue

        # 7️⃣ Breakout + Volume
        pivot = float(df["high"].rolling(20).max().shift(1).iloc[-1])
        if price <= pivot:
            continue

        if float(last["volume"]) < 1.5 * avg_vol20:
            continue

        stop, tp1, tp2 = risk_plan(price, pivot)

        results.append({
            "Ticker": t,
            "Price": round(price, 2),
            "RS": round(rs, 3),
            "ATR %": round(atr_pct, 2),
            "52W Dist %": round(dist_pct, 2),
            "Avg Vol": int(avg_vol20),
            "Stop": round(stop, 2),
            "TP1": round(tp1, 2),
            "TP2": round(tp2, 2),
        })

    if not results:
        return pd.DataFrame()

    df = pd.DataFrame(results)
    df = df.sort_values(by="RS", ascending=False).reset_index(drop=True)
    return df
