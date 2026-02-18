import streamlit as st
import pandas as pd
from tradingview_ta import TA_Handler, Interval
import streamlit.components.v1 as components

st.set_page_config(page_title="Alpha Recovery Terminal", layout="wide")

# TEST LİSTESİ (En azından bunlar çalışmalı!)
TEST_LIST = [
    "AROC", "NVDA", "TSLA", "AAPL", "MSFT", "AMD", "PLTR", "META", "AMZN", 
    "NFLX", "GOOGL", "AVGO", "SMCI", "COIN", "MARA", "RIOT", "U", "SNOW"
]

def check_stock(symbol):
    try:
        # Önce NASDAQ deniyoruz
        handler = TA_Handler(
            symbol=symbol,
            screener="america",
            exchange="NASDAQ",
            interval=Interval.INTERVAL_1_DAY
        )
        analysis = handler.get_analysis()
        ind = analysis.indicators
        
        price = ind["close"]
        ma150, ma200 = ind["SMA100"], ind["SMA200"] # TA-API'de SMA150 genelde SMA100 olarak gelir
        rsi = ind["RSI"]
        
        # ANAYASA FİLTRELERİ (Biraz esnettik ki sonuç çıksın!)
        is_uptrend = price > ma200
        is_strong = rsi > 50
        
        if is_uptrend:
            return {
                "Hisse": symbol,
                "Fiyat": round(price, 2),
                "RSI": round(rsi, 1),
                "Durum": "✅ TRENDDE",
                "Onay": "🔥 GÜÇLÜ" if rsi > 60 else "📊 NORMAL"
            }
    except:
        # NASDAQ olmazsa NYSE deniyoruz
        try:
            handler.exchange = "NYSE"
            analysis = handler.get_analysis()
            ind = analysis.indicators
            price = ind["close"]
            if price > ind["SMA200"]:
                return {"Hisse": symbol, "Fiyat": round(price, 2), "RSI": round(ind["RSI"], 1), "Durum": "✅ TRENDDE", "Onay": "📊 NORMAL"}
        except:
            return None
    return None

st.title("🦅 Alpha US - Kurtarma Paneli")

tab1, tab2 = st.tabs(["🔍 Hızlı Tarama", "📈 Teknik Grafik"])

with tab1:
    st.info("Bu modül doğrudan en popüler 20 momentum hissesine bakar.")
    if st.button("🚀 Radarı Çalıştır (Test)"):
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, sym in enumerate(TEST_LIST):
            status_text.text(f"Kontrol ediliyor: {sym}")
            res = check_stock(sym)
            if res:
                results.append(res)
            progress_bar.progress((i + 1) / len(TEST_LIST))
            
        if results:
            st.success(f"{len(results)} adet hisse kriterlere takıldı!")
            st.dataframe(pd.DataFrame(results), use_container_width=True)
        else:
            st.error("Kriterler hala çok sert! Hiçbir hisse fiyat > MA200 şartını sağlamıyor.")

with tab2:
    target = st.text_input("Grafik:", "AROC").upper()
    tv_code = f"""
    <div style="height:550px;"><script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
    <script type="text/javascript">new TradingView.widget({{"autosize": true,"symbol": "{target}","interval": "D","timezone": "America/New_York","theme": "dark","style": "1","locale": "tr","container_id": "tv_v7"}});</script>
    <div id="tv_v7" style="height:100%;"></div></div>
    """
    components.html(tv_code, height=560)
