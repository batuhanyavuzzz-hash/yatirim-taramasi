import pandas as pd

def risk_plan(entry: float, pivot: float | None):
    """
    Basit örnek:
    stop = pivot * 0.99 (pivot altı %1)
    TP1 = entry + 2R
    TP2 = entry + 3R
    """
    if pivot is None or pd.isna(pivot):
        return None, None, None

    stop = pivot * 0.99
    r = entry - stop
    if r <= 0:
        return stop, None, None

    tp1 = entry + 2 * r
    tp2 = entry + 3 * r
    return stop, tp1, tp2
