import streamlit as st
import pandas as pd
from datetime import date, timedelta

from src.data.yahoo import YahooProvider
from src.screener import run_screen
from src.universe import load_universe

st.set_page_config(page_title="Minervini Auto Screener", layout="wide")

st.title("🇺🇸 Minervini OTOMATİK Swing Screener")

st.markdown("""
Bu sistem **manuel filtreleme içermez**.  
Butona bas → **stratejiye UYAN hisseler** gelir.  
Boş liste = piyasada uygun setup yok.
""")

run_btn = st.button("🚀 OTOMATİK TARAMAYI ÇALIŞTIR", type="primary")

provider = YahooProvider()
tickers = load_universe()   # otomatik universe

if run_btn:
    end = date.today()
    start = end - timedelta(days=800)

    with st.spinner("ABD piyasası taranıyor..."):
        df = run_screen(
            tickers=tickers,
            provider=provider,
            start=start,
            end=end
        )

    if df.empty:
        st.warning("❌ Bugün Minervini kriterlerine uyan hisse yok.")
    else:
        st.success(f"✅ {len(df)} adet ONAYLI hisse bulundu")
        st.dataframe(df, use_container_width=True)
