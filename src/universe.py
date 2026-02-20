import pandas as pd


def _normalize_tickers(tickers):
    return [str(t).upper().replace('.', '-') for t in tickers if str(t).strip()]


def load_universe(limit=120, fallback_csv='universe_us.csv'):
    """
    `universe_us.csv` dosyasından ticker listesini yükler.
    Bu yaklaşım Streamlit Cloud'da `lxml` gibi opsiyonel parser
    bağımlılıklarına ihtiyaç duymaz.
    """
    df = pd.read_csv(fallback_csv)
    col = 'ticker' if 'ticker' in df.columns else df.columns[0]
    tickers = _normalize_tickers(df[col].tolist())
    return tickers[:limit]
