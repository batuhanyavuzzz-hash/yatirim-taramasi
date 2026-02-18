import pandas as pd
import numpy as np

from src.indicators import ema, atr, rs_score
from src.risk import risk_plan


def run_screen(tickers, provider, start, end):
    benchmark = provider.history("SPY", start, end)
    if benchmark is None or benchmark.empty or "close" not in benchmark.columns:
        return pd.DataFrame()

    bench_close = benchmark["close"].dropna()
    if len(bench_close) < 260:
        return pd.DataFrame()

    results = []

    for t in tickers:
        df = provider.history(t, start, end)
        if df is None or df.empty:
            continue

        df = df.dropna()
        if len(df) < 260:
            continue

        need = {"open", "high", "low", "close", "volume"}
        if not need.issubset(set(df.columns)):
            continue

        close = df["close"].dropna()
        if len(close) < 260:
            continue

        df["ema50"] = ema(close, 50)
        df["ema150"] = ema(close, 150)
        df["ema200"] = ema(close, 200)
        df["atr14"] = atr(df, 14)

        last = df.iloc[-1]

        try:
            price = float(last["close"])
            ema50 = float(last["ema50"])
            ema150 = float(last["ema150"])
            ema200 = float(last["ema200"])
        except Exception:
            continue

        if not (np.isfinite(price) and np.isfinite(ema50) and np.isfinite(ema150) and np.isfinite(ema200)):
            continue

        # HARD: Trend template (aynı)
        if not (price > ema50 and ema50 > ema150 and ema150 > ema200):
            continue

        # HARD: EMA200 slope (aynı)
        try:
            ema200_now = float(df["ema200"].iloc[-1])
            ema200_prev = float(df["ema200"].iloc[-21])
        except Exception:
            continue

        if not (np.isfinite(ema200_now) and np.isfinite(ema200_prev)):
            continue
        if ema200_now <= ema200_prev:
            continue

        # HARD: Likidite (aynı)
        try:
            avg_vol20 = float(df["volume"].rolling(20).mean().iloc[-1])
        except Exception:
            continue
        if (not np.isfinite(avg_vol20)) or avg_vol20 < 1_000_000:
            continue

        # HARD: ATR% (aynı)
        try:
            atr14 = float(last["atr14"])
        except Exception:
            continue
        if not np.isfinite(atr14):
            continue
        atr_pct = (atr14 / price) * 100.0
        if (not np.isfinite(atr_pct)) or atr_pct < 2.0 or atr_pct > 10.0:
            continue

        # GEVŞETİLDİ: 52W high proximity %20 -> %30
        try:
            high_52w = float(df["high"].rolling(252).max().iloc[-1])
        except Exception:
            continue
        if not np.isfinite(high_52w) or high_52w <= 0:
            continue
        dist_pct = (high_52w - price) / high_52w * 100.0
        if (not np.isfinite(dist_pct)) or dist_pct > 30.0:
            continue

        # HARD: RS >= 0.10 (aynı)
        try:
            rs = float(rs_score(close, bench_close))
        except Exception:
            continue
        if (not np.isfinite(rs)) or rs < 0.10:
            continue

        # HARD: Breakout (aynı)
        try:
            pivot = float(df["high"].rolling(20).max().shift(1).iloc[-1])
        except Exception:
            continue
        if not np.isfinite(pivot) or pivot <= 0:
            continue
        if price <= pivot:
            continue

        # GEVŞETİLDİ: volume confirm 1.5x -> 1.2x
        try:
            vol_today = float(last["volume"])
        except Exception:
            continue
        if not np.isfinite(vol_today):
            continue
        if vol_today < 1.2 * avg_vol20:
            continue

        stop, tp1, tp2 = risk_plan(price, pivot)
        if stop is None or tp1 is None or tp2 is None:
            continue

        results.append({
            "Ticker": t,
            "Price": round(price, 2),
            "RS": round(rs, 3),
            "ATR %": round(atr_pct, 2),
            "52W Dist %": round(dist_pct, 2),
            "Avg Vol": int(avg_vol20),
            "Pivot": round(pivot, 2),
            "Stop": round(float(stop), 2),
            "TP1": round(float(tp1), 2),
            "TP2": round(float(tp2), 2),
        })

    if not results:
        return pd.DataFrame()

    out = pd.DataFrame(results)
    out = out.sort_values(by=["RS", "Avg Vol"], ascending=[False, False]).reset_index(drop=True)
    return out
