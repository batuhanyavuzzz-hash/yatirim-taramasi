 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/src/screener.py b/src/screener.py
index d5f775d349ec2269573537df1e062b7fc0cf4108..3bc041fd1491825202a62d31d86aa9d5633010f6 100644
--- a/src/screener.py
+++ b/src/screener.py
@@ -1,39 +1,38 @@
 import pandas as pd
-import numpy as np
-
 from src.indicators import ema, atr
 from src.risk import risk_plan
 
 
 def run_screen(tickers, provider, start, end):
     stats = {
         "tickers_total": len(tickers),
         "data_ok": 0,
         "passed_trend": 0,
         "passed_breakout": 0,
         "final_pass": 0,
+        "skipped_invalid_risk": 0,
     }
 
     results = []
 
     for t in tickers:
         df = provider.history(t, start, end)
         if df is None or df.empty or len(df) < 260:
             continue
 
         df = df.dropna()
         if len(df) < 260:
             continue
 
         need = {"open", "high", "low", "close", "volume"}
         if not need.issubset(set(df.columns)):
             continue
 
         stats["data_ok"] += 1
 
         close = df["close"]
 
         # İndikatörler
         df["ema50"] = ema(close, 50)
         df["ema150"] = ema(close, 150)
         df["ema200"] = ema(close, 200)
@@ -69,49 +68,52 @@ def run_screen(tickers, provider, start, end):
         if atr_pct < 2 or atr_pct > 12:
             continue
 
         # 52W High proximity (%35)
         high_52w = df["high"].rolling(252).max().iloc[-1]
         dist_pct = (high_52w - price) / high_52w * 100
         if dist_pct > 35:
             continue
 
         # 🟡 BREAKOUT (YUMUŞATILDI)
         pivot = df["high"].rolling(20).max().shift(1).iloc[-1]
 
         breakout = price > pivot
         near_breakout = (pivot - price) / pivot <= 0.01   # %1 altında
 
         if not (breakout or near_breakout):
             continue
 
         # Hacim onayı (1.2x)
         if float(last["volume"]) < 1.2 * avg_vol20:
             continue
 
         stats["passed_breakout"] += 1
 
         stop, tp1, tp2 = risk_plan(price, pivot)
+        if stop is None:
+            stats["skipped_invalid_risk"] += 1
+            continue
 
         results.append({
             "Ticker": t,
             "Price": round(price, 2),
             "ATR %": round(atr_pct, 2),
             "52W Dist %": round(dist_pct, 2),
             "Avg Vol": int(avg_vol20),
             "Pivot": round(float(pivot), 2),
             "Breakout": breakout,
             "Near Breakout": near_breakout,
             "Stop": round(float(stop), 2),
             "TP1": round(float(tp1), 2),
             "TP2": round(float(tp2), 2),
         })
 
         stats["final_pass"] += 1
 
     if not results:
         stats["error"] = "No setups today"
         return pd.DataFrame(), stats
 
     out = pd.DataFrame(results)
     out = out.sort_values(by=["Avg Vol"], ascending=False).reset_index(drop=True)
     return out, stats
 
EOF
)
