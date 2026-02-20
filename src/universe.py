 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/src/universe.py b/src/universe.py
index 686dda1a5a29a52b1d0337828174fd0b64c13935..5475286b9cbd10e3219d82e7be7386fa71444b81 100644
--- a/src/universe.py
+++ b/src/universe.py
@@ -1,25 +1,17 @@
 import pandas as pd
-import requests
 
 
-def load_universe():
-    """
-    S&P500 içinden likit ilk 120 hisseyi alır
-    (TwelveData free plan için güvenli)
-    """
-    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
-    headers = {
-        "User-Agent": "Mozilla/5.0"
-    }
-
-    r = requests.get(url, headers=headers, timeout=20)
-    tables = pd.read_html(r.text)
-    df = tables[0]
+def _normalize_tickers(tickers):
+    return [str(t).upper().replace('.', '-') for t in tickers if str(t).strip()]
 
-    tickers = df["Symbol"].astype(str).str.upper().tolist()
 
-    # TwelveData uyumu
-    tickers = [t.replace(".", "-") for t in tickers]
-
-    # 🔴 KRİTİK: SADECE İLK 120
-    return tickers[:120]
+def load_universe(limit=120, fallback_csv='universe_us.csv'):
+    """
+    `universe_us.csv` dosyasından ticker listesini yükler.
+    Bu yaklaşım Streamlit Cloud'da `lxml` gibi opsiyonel parser
+    bağımlılıklarına ihtiyaç duymaz.
+    """
+    df = pd.read_csv(fallback_csv)
+    col = 'ticker' if 'ticker' in df.columns else df.columns[0]
+    tickers = _normalize_tickers(df[col].tolist())
+    return tickers[:limit]
 
EOF
)
