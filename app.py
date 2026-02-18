import streamlit as st
import pandas as pd
from datetime import date, timedelta

from src.data.yahoo import YahooProvider
from src.universe import load_universe
from src.screener import run_screen
from src.storage import load_approved, save_approved, approve_ticker, unapprove_ticker

st.set_page_config(page_title="Minervini Swing Screener", layout="wide")

st.title("Minervini Swing Screener (ABD)")

provider = YahooProvider()
APPROVED_PATH = "approved.json"

# Sidebar
st.sidebar.header("Piyasa & Evren")
market = st.sidebar.selectbox("Market", ["USA"], index=0)

universe_mode = st.sidebar.radio(
    "Universe kaynağı",
    ["CSV upload", "Repo'daki universe_us.csv", "Manuel ticker listesi"],
    index=0
)

uploaded = None
manual_text = ""
if universe_mode == "CSV upload":
    uploaded = st.sidebar.file_uploader("CSV yükle (kolon: ticker veya Symbol)", type=["csv"])
elif universe_mode == "Repo'daki universe_us.csv":
    # nothing
    pass
else:
    manual_text = st.sidebar.text_area(
        "Tickers (virgül ya da satır satır)",
        value="NVDA, AMAT, CLS, VRT, PLTR, DDOG, META, AAPL, TSLA, AMD",
        height=180
    )

st.sidebar.divider()
st.sidebar.header("Filtreler (Likidite/Volatilite)")

min_avg_vol = st.sidebar.number_input("Min 20g Ortalama Hacim", value=800_000, step=100_000)
min_price = st.sidebar.number_input("Min fiyat ($)", value=10.0, step=1.0)

atr_min = st.sidebar.slider("ATR% min", 0.5, 20.0, 2.0)
atr_max = st.sidebar.slider("ATR% max", 0.5, 20.0, 12.0)

st.sidebar.divider()
st.sidebar.header("Strateji (Skor)")

near_52w_high_pct = st.sidebar.slider("52W high'a max uzaklık (%) [skora katkı]", 5, 60, 30)
vol_mult = st.sidebar.slider("Breakout hacim çarpanı (>=) [skora katkı]", 1.0, 3.0, 1.5, 0.1)

top_n = st.sidebar.slider("Top N sonuç", 10, 200, 50)
lookback_days = st.sidebar.slider("Lookback (trading gün)", 200, 600, 420)

debug = st.sidebar.checkbox("Debug (veri kontrol tablosu)", value=False)
show_only_approved = st.sidebar.checkbox("Sadece ONAYLI hisseler", value=False)

st.sidebar.divider()
run_btn = st.sidebar.button("Taramayı Çalıştır", type="primary")

# Load universe
tickers = load_universe(mode=universe_mode, uploaded_file=uploaded, manual_text=manual_text)

# Approved storage
approved = load_approved(APPROVED_PATH)

if run_btn:
    end = date.today()
    # trading days -> calendar buffer
    start = end - timedelta(days=int(lookback_days * 1.9))

    with st.spinner("Tarama çalışıyor..."):
        results, dbg = run_screen(
            tickers=tickers,
            provider=provider,
            start=start,
            end=end,
            benchmark="SPY",
            min_avg_vol=min_avg_vol,
            min_price=min_price,
            atr_min=atr_min,
            atr_max=atr_max,
            near_52w_high_pct=near_52w_high_pct,
            vol_mult=vol_mult,
            approved_map=approved,
        )

    if debug:
        st.subheader("Debug – Veri Kontrol (ilk 200 satır)")
        st.dataframe(pd.DataFrame(dbg).head(200), use_container_width=True)

    if results.empty:
        st.warning("Kriterlere uyan sonuç yok. (Universe dar olabilir veya filtreler sıkı olabilir.)")
        st.stop()

    if show_only_approved:
        results = results[results["approved"] == True].copy()

    st.subheader(f"Sonuçlar (Top {min(top_n, len(results))})")
    results_top = results.head(top_n).copy()
    st.dataframe(results_top, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Detay & Onay Yönetimi")

    col1, col2 = st.columns([1, 2], gap="large")

    with col1:
        sel = st.selectbox("Hisse seç", results_top["ticker"].tolist())
        row = results[results["ticker"] == sel].iloc[0].to_dict()

        st.markdown("### Setup Özeti")
        st.write({
            "Ticker": row["ticker"],
            "Price": row["price"],
            "Score": row["score"],
            "Breakout": row["breakout"],
            "Vol Confirm": row["vol_confirm"],
            "RS Score": row["rs_score"],
            "52W High Dist %": row["dist_52w_high_pct"],
            "ATR %": row["atr_pct"],
            "AvgVol20": row["avg_vol20"],
            "Trend": row["trend_template"],
        })

        st.markdown("### Risk Planı (örnek)")
        st.write({
            "Entry (approx)": row["price"],
            "Stop": row["stop"],
            "TP1 (2R)": row["tp1"],
            "TP2 (3R)": row["tp2"],
        })

        st.markdown("### Onay")
        note = st.text_input("Not (opsiyonel)", value=approved.get(sel, {}).get("note", ""))

        c1, c2 = st.columns(2)
        if c1.button("✅ ONAYLA / Güncelle"):
            approved = approve_ticker(approved, sel, note=note)
            save_approved(APPROVED_PATH, approved)
            st.success(f"{sel} onaylandı / güncellendi.")

        if c2.button("🗑️ ONAYI KALDIR"):
            approved = unapprove_ticker(approved, sel)
            save_approved(APPROVED_PATH, approved)
            st.info(f"{sel} onayı kaldırıldı.")

    with col2:
        st.markdown("### Fiyat Grafiği (Close + EMA)")
        # yeniden çekip grafikte gösterelim
        df = provider.history(sel, start=start, end=end)
        if df is None or df.empty:
            st.warning("Grafik için veri yok.")
        else:
            import plotly.graph_objects as go
            from src.indicators import ema

            df = df.copy()
            df["ema21"] = ema(df["close"], 21)
            df["ema50"] = ema(df["close"], 50)
            df["ema200"] = ema(df["close"], 200)

            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=df.index, open=df["open"], high=df["high"], low=df["low"], close=df["close"],
                name="OHLC"
            ))
            fig.add_trace(go.Scatter(x=df.index, y=df["ema21"], mode="lines", name="EMA21"))
            fig.add_trace(go.Scatter(x=df.index, y=df["ema50"], mode="lines", name="EMA50"))
            fig.add_trace(go.Scatter(x=df.index, y=df["ema200"], mode="lines", name="EMA200"))
            fig.update_layout(height=520, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Soldan universe seç → parametreleri ayarla → **Taramayı Çalıştır**")
