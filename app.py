import streamlit as st
from datetime import date, timedelta

from src.data.yahoo import YahooProvider
from src.screener import run_screen
from src.universe import load_universe

st.set_page_config(page_title="Minervini Auto Screener", layout="wide")
st.title("🇺🇸 Minervini OTOMATİK Swing Screener")

st.sidebar.header("Ayarlar")
sidebar_api_key = st.sidebar.text_input(
    "TwelveData API Key",
    type="password",
    help="İstersen Streamlit Secrets yerine buradan API key girebilirsin.",
)

provider = YahooProvider(api_key=sidebar_api_key.strip() if sidebar_api_key else None)

if not provider.api_key:
    st.warning("TwelveData API key gerekli. Aşağıya API key girerek devam edebilirsin.")
    page_api_key = st.text_input("TwelveData API Key (zorunlu)", type="password")
    provider = YahooProvider(api_key=page_api_key.strip() if page_api_key else None)

    if not provider.api_key:
        st.info("API key girildiğinde tarama ekranı otomatik aktif olur.")
        st.stop()

# Universe yükle
tickers = load_universe()
st.info(f"Universe yüklendi: **{len(tickers)} ticker**")

# Çalıştır
run_btn = st.button("🚀 OTOMATİK TARAMAYI ÇALIŞTIR", type="primary")

if run_btn:
    end = date.today()
    start = end - timedelta(days=900)

    with st.spinner("Tarama çalışıyor..."):
        df, stats = run_screen(
            tickers=tickers,
            provider=provider,
            start=start,
            end=end,
        )

    st.write("### Tarama İstatistikleri")
    st.write(stats)

    if df.empty:
        st.warning("❌ Bugün Minervini kriterlerine uyan hisse yok.")
    else:
        st.success(f"✅ {len(df)} adet ONAYLI hisse bulundu")
        st.dataframe(df, use_container_width=True)
