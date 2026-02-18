import pandas as pd
import numpy as np

from .indicators import ema, atr, rs_score
from .risk import risk_plan

def run_screen(
    tickers,
    provider,
    start,
    end,
    benchmark="SPY",
    min_avg_vol=800_000,
    min_price=10.0,
    atr_min=2.0,
    atr_max=12.0,
    near_52w_high_pct=30,
    vol_mult=1.5,
    approved_map=None,
):
    approved_map = approved_map or {}
    dbg = []

    bench = provider.history(benchmark, start, end)
    if bench is None or bench.empty or "close" not in bench.columns:
        return pd.DataFrame(), [{"error": "Benchmark data missing"}]

    out = []

    for t in tickers:
        df = provider.history(t, start, end)

        if df is None or df.empty:
            dbg.append({"ticker": t, "rows": 0, "reason": "no_data"})
            continue

        if len(df) < 260:
            dbg.append({"ticker": t, "rows": len(df), "reason": "too_short"})
            continue

        close = df["close"]
        df["ema21"] = ema(close, 21)
        df["ema50"] = ema(close, 50)
        df["ema150"] = ema(close, 150)
        df["ema200"] = ema(close, 200)
        df["atr14"] = atr(df, 14)

        last = df.iloc[-1]
        price = float(last["close"])

        if price < float(min_price):
            dbg.append({"ticker": t, "rows": len(df), "reason": "min_price"})
            continue

        avg_vol20 = float(df["volume"].rolling(20).mean().iloc[-1])
        if np.isnan(avg_vol20) or avg_vol20 < float(min_avg_vol):
            dbg.append({"ticker": t, "rows": len(df), "reason": "min_avg_vol"})
            continue

        atr_pct = float((last["atr14"] / last["close"]) * 100.0)
        if np.isnan(atr_pct) or atr_pct < float(atr_min) or atr_pct > float(atr_max):
            dbg.append({"ticker": t, "rows": len(df), "reason": "atr_pct"})
            continue

        # 52W high proximity
        high_52w = float(df["high"].rolling(252).max().iloc[-1])
        dist_pct = float((high_52w - price) / high_52w * 100.0) if high_52w else float("nan")

        # Trend checks
        ema200_slope = float(df["ema200"].iloc[-1] - df["ema200"].iloc[-21])
        template_strict = bool(price > last["ema50"] > last["ema150"] > last["ema200"] and ema200_slope > 0)
        template_soft = bool(price > last["ema50"] and last["ema50"] > last["ema200"] and ema200_slope > 0)

        # Breakout (20d pivot)
        pivot = df["high"].rolling(20).max().shift(1).iloc[-1]
        breakout = bool(pd.notna(pivot) and price > float(pivot))
        vol_confirm = bool(breakout and float(last["volume"]) >= float(vol_mult) * avg_vol20)

        # RS score vs benchmark
        rs = rs_score(close, bench["close"])
        if np.isnan(rs):
            dbg.append({"ticker": t, "rows": len(df), "reason": "rs_nan"})
            continue

        # Score (0..)
        score = 0
        # trend
        score += 3 if template_strict else (2 if template_soft else 0)
        # 52w high proximity (closer = better)
        if pd.notna(dist_pct):
            if dist_pct <= near_52w_high_pct:
                score += 2
            elif dist_pct <= near_52w_high_pct * 1.5:
                score += 1
        # breakout & vol
        score += 2 if breakout else 0
        score += 2 if vol_confirm else 0
        # rs bucket
        if rs > 0.20:
            score += 3
        elif rs > 0.10:
            score += 2
        elif rs > 0.00:
            score += 1

        # Risk plan
        stop, tp1, tp2 = risk_plan(price, float(pivot) if pd.notna(pivot) else None)

        out.append({
            "ticker": t,
            "price": round(price, 2),
            "score": int(score),
            "trend_template": "strict" if template_strict else ("soft" if template_soft else "no"),
            "avg_vol20": int(avg_vol20),
            "atr_pct": round(atr_pct, 2),
            "dist_52w_high_pct": round(dist_pct, 2) if pd.notna(dist_pct) else None,
            "breakout": breakout,
            "vol_confirm": vol_confirm,
            "rs_score": round(float(rs), 4),
            "pivot": round(float(pivot), 2) if pd.notna(pivot) else None,
            "stop": round(float(stop), 2) if stop is not None else None,
            "tp1": round(float(tp1), 2) if tp1 is not None else None,
            "tp2": round(float(tp2), 2) if tp2 is not None else None,
            "approved": t in approved_map,
        })

        dbg.append({"ticker": t, "rows": len(df), "reason": "ok", "score": int(score)})

    if not out:
        return pd.DataFrame(), dbg

    res = pd.DataFrame(out)

    # Sıralama: score desc, sonra RS desc, sonra vol_confirm/breakout
    res = res.sort_values(
        by=["score", "rs_score", "vol_confirm", "breakout", "avg_vol20"],
        ascending=[False, False, False, False, False]
    ).reset_index(drop=True)

    return res, dbg
