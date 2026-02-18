import streamlit as st
import pandas as pd
from datetime import date, timedelta

from src.screener import run_screen
from src.universe import DEFAULT_UNIVERSE
from src.data.provider import YahooProvider

st.set_page_config(page_title="Minervini Swing Screener", layout="wide")

st.title("Minervini Swing Screener (Streamlit)")

# Sidebar params
st.sidebar.header("Tarama Parametreleri")

universe = st.sidebar.text_area(
    "Ticker listesi (virgül veya satır satır)",
    value="\n".join(DEFAULT_UNIVERSE),
    height=200
)
tickers = [t.strip().upper() for t in universe.replace(",", "\n").split("\n") if t.strip()]

min_avg_vol = st.sidebar.number_input("Min 20g Ortalama Hacim", value=500_000, step=100_000)
atr_min = st.sidebar.slider("ATR% min", 0.5, 15.0, 2.0)
atr_max = st.sidebar.slider("ATR% max", 0.5, 15.0, 8.0)

vol_mult = st.sidebar.slider("Breakout hacim çarpanı (>=)", 1.0, 3.0, 1.5, 0.1)
near_52w_high = st.sidebar.slider("52W high'a max uzaklık (%)", 1, 40, 15)

lookback_days = st.sidebar.slider("Veri lookback (gün)", 150, 500, 300)

run_btn = st.sidebar.button("Taramayı Çalıştır")

provider = YahooProvider()

if run_btn:
    with st.spinner("Tarama çalışıyor..."):
        end = date.today()
        start = end - timedelta(days=int(lookback_days * 1.8))  # trading day vs calendar
        results = run_screen(
            tickers=tickers,
            provider=provider,
            start=start,
            end=end,
            min_avg_vol=min_avg_vol,
            atr_min=atr_min,
            atr_max=atr_max,
            vol_mult=vol_mult,
            near_52w_high_pct=near_52w_high,
        )

    if results.empty:
        st.warning("Kriterlere uyan hisse bulunamadı.")
    else:
        st.subheader("Sonuçlar")
        st.dataframe(results, use_container_width=True)

        st.subheader("Detay")
        sel = st.selectbox("Hisse seç", results["ticker"].tolist())
        row = results[results["ticker"] == sel].iloc[0]
        st.write(row.to_dict())
