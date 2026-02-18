def risk_plan(entry, pivot):
    stop = pivot * 0.99
    r = entry - stop
    if r <= 0:
        return None, None, None
    return stop, entry + 2*r, entry + 3*r
