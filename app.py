import streamlit as st
from datetime import date, timedelta

from src.data.yahoo import YahooProvider
from src.screener import run_screen
from src.universe import load_universe

st.set_page_config(page_title="Minervini Auto Screener", layout="wide")
st.title("🇺🇸 Minervini OTOMATİK Swing Screener")

provider = YahooProvider()

tickers = load_universe()
st.info(f"Universe yüklendi: **{len(tickers)} ticker**")

# 🔎 SPY diagnostic button
if st.button("🔎 SPY Test (diagnostic)"):
    end = date.today()
    start = end - timedelta(days=365)
    _ = provider.history("SPY", start, end)
    st.write("### TwelveData SPY Diagnostic")
    st.write(provider.last_diag)
    st.stop()

run_btn = st.button("🚀 OTOMATİK TARAMAYI ÇALIŞTIR", type="primary")

if run_btn:
    end = date.today()
    start = end - timedelta(days=900)

    with st.spinner("Tarama çalışıyor..."):
        df, stats = run_screen(tickers=tickers, provider=provider, start=start, end=end)

    st.write("### Tarama İstatistikleri")
    st.write(stats)

    if stats.get("error") == "SPY data missing":
        st.error("SPY verisi gelmedi. Önce 'SPY Test (diagnostic)' butonuna basıp sonucu buraya yapıştır.")
        st.stop()

    if df.empty:
        st.warning("❌ Bugün Minervini kriterlerine uyan hisse yok.")
    else:
        st.success(f"✅ {len(df)} adet ONAYLI hisse bulundu")
        st.dataframe(df, use_container_width=True)
