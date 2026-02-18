import streamlit as st
import pandas as pd
from tradingview_ta import TA_Handler, Interval
import streamlit.components.v1 as components

st.set_page_config(page_title="Alpha Diagnostic Terminal", layout="wide")

def get_detailed_analysis(symbol):
    try:
        handler = TA_Handler(symbol=symbol, screener="america", exchange="AMERICA", interval=Interval.INTERVAL_1_DAY)
        ind = handler.get_analysis().indicators
        
        price = ind["close"]
        ma50, ma100, ma200 = ind["SMA50"], ind["SMA100"], ind["SMA200"]
        rsi = ind["RSI"]
        
        # ANAYASA TESTLERİ
        results = {
            "Hisse": symbol,
            "Fiyat > MA200": "✅" if price > ma200 else "❌",
            "MA150 > MA200": "✅" if ma100 > ma200 else "❌",
            "MA50 > MA150": "✅" if ma50 > ma100 else "❌",
            "RSI > 55": "✅" if rsi > 55 else "❌",
            "Sonuç": "UYGUN"
        }
        
        # Eğer tek bir tane bile ❌ varsa sonuç başarısızdır
        if "❌" in results.values():
            results["Sonuç"] = "ELENDİ"
            
        return results, ind
    except:
        return None, None

st.title("🦅 Alpha US: Teşhis ve Tarama Paneli")

tab1, tab2 = st.tabs(["🔍 Hızlı Teşhis (Tek Hisse)", "📡 Geniş Tarama"])

with tab1:
    st.subheader("Bir Hisse Neden Eleniyor?")
    check_sym = st.text_input("Hisse Kodu Yazın (Örn: AROC, NVDA, TSLA):", "AROC").upper()
    if st.button("Anayasa Testine Sok"):
        res, ind = get_detailed_analysis(check_sym)
        if res:
            st.table(pd.DataFrame([res]))
            if res["Sonuç"] == "ELENDİ":
                st.error(f"Bu hisse anayasanın sert duvarlarına çarptı. Özellikle {list(res.keys())[list(res.values()).index('❌')]} kriteri sağlanmıyor.")
        else:
            st.warning("Veri çekilemedi. Sembolün doğru olduğundan emin olun.")

with tab2:
    st.subheader("Piyasa Taraması")
    # Buraya önceki geniş tarama kodunu ekleyebilirsin
    st.info("Hisse bulunamıyorsa 'Teşhis' sekmesinden favori hisseni kontrol et, sistemin neden elediğini gör.")
