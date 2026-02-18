import pandas as pd
from .indicators import ema, atr, rs_score

def run_screen(
    tickers, provider, start, end,
    min_avg_vol: int,
    atr_min: float,
    atr_max: float,
    vol_mult: float,
    near_52w_high_pct: int,
    benchmark: str="SPY",
):
    bench = provider.history(benchmark, start, end)
    if bench.empty:
        return pd.DataFrame()

    out = []
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
        avg_vol20 = df["volume"].rolling(20).mean().iloc[-1]
        if pd.isna(avg_vol20) or avg_vol20 < min_avg_vol:
            continue

        atr_pct = (last["atr14"] / last["close"]) * 100
        if pd.isna(atr_pct) or atr_pct < atr_min or atr_pct > atr_max:
            continue

        # Trend filtresi
        cond_trend = (
            last["close"] > last["ema50"] > last["ema150"] > last["ema200"]
        )
        ema200_slope = df["ema200"].iloc[-1] - df["ema200"].iloc[-21]
        if not cond_trend or ema200_slope <= 0:
            continue

        # 52W high proximity
        high_52w = df["high"].rolling(252).max().iloc[-1]
        dist_pct = (high_52w - last["close"]) / high_52w * 100
        if dist_pct > near_52w_high_pct:
            continue

        # Basit breakout: son 20 günün en yükseğini kırıyor mu?
        pivot = df["high"].rolling(20).max().shift(1).iloc[-1]
        breakout = last["close"] > pivot if pd.notna(pivot) else False

        # Hacim onayı
        vol_ok = last["volume"] >= vol_mult * avg_vol20

        # RS skor
        rs = rs_score(close, bench["close"])

        # Risk (örnek): stop = pivot altı %1 buffer
        stop = pivot * 0.99 if pd.notna(pivot) else float("nan")
        entry = last["close"]
        r = entry - stop if pd.notna(stop) else float("nan")
        tp1 = entry + 2*r if pd.notna(r) else float("nan")
        tp2 = entry + 3*r if pd.notna(r) else float("nan")

        out.append({
            "ticker": t,
            "price": round(entry, 2),
            "avg_vol20": int(avg_vol20),
            "atr_pct": round(atr_pct, 2),
            "dist_52w_high_pct": round(dist_pct, 2),
            "breakout": breakout,
            "vol_confirm": vol_ok,
            "rs_score": rs,
            "stop": round(stop, 2) if pd.notna(stop) else None,
            "tp1": round(tp1, 2) if pd.notna(tp1) else None,
            "tp2": round(tp2, 2) if pd.notna(tp2) else None,
        })

    if not out:
        return pd.DataFrame()

    res = pd.DataFrame(out)
    # Uygunluk sıralaması: breakout+vol_confirm önce, sonra rs_score
    res["setup_score"] = (
        res["breakout"].astype(int)*2 +
        res["vol_confirm"].astype(int)*2
    )
    res = res.sort_values(by=["setup_score","rs_score"], ascending=False).reset_index(drop=True)
    return res
