import streamlit as st
import pandas as pd
from tradingview_ta import TA_Handler, Interval
import streamlit.components.v1 as components
import requests
import io

st.set_page_config(page_title="Alpha Scoring Terminal", layout="wide")

# --- ANAYASAL PUANLAMA MOTORU ---
def analyze_with_score(symbol):
    try:
        handler = TA_Handler(symbol=symbol, screener="america", exchange="AMERICA", interval=Interval.INTERVAL_1_DAY)
        ind = handler.get_analysis().indicators
        
        # Veriler
        price = ind["close"]
        ma50, ma100, ma200 = ind["SMA50"], ind["SMA100"], ind["SMA200"]
        rsi = ind["RSI"]
        vol_ratio = ind["volume"] / ind.get("average_volume_10d", ind["volume"])
        
        score = 0
        details = []

        # 1. Kriter: Fiyat Ortalamaların Üstünde mi?
        if price > ma100 and price > ma200:
            score += 1
            details.append("✅ Trend")
        
        # 2. Kriter: Dizilim Doğru mu? (MA100 > MA200)
        if ma100 > ma200:
            score += 1
            details.append("✅ Dizilim")

        # 3. Kriter: MA50 Momentum Var mı?
        if ma50 > ma100:
            score += 1
            details.append("✅ Momentum")

        # 4. Kriter: RSI Güçlü mü? (> 55)
        if rsi > 55:
            score += 1
            details.append("✅ RSI")

        # 5. Kriter: Hacimli Onay var mı? (> 1.2)
        if vol_ratio > 1.2:
            score += 1
            details.append("🔥 HACİM")

        return {
            "Hisse": symbol,
            "Puan": f"{score}/5",
            "Kriterler": ", ".join(details),
            "Fiyat": round(price, 2),
            "Hacim Gücü": f"%{round((vol_ratio-1)*100, 1)}",
            "RSI": round(rsi, 1),
            "Status": "🏆 MÜKEMMEL" if score == 5 else ("⭐ GÜÇLÜ" if score == 4 else "👀 TAKİP")
        }
    except:
        return None

# --- ARAYÜZ ---
st.title("🦅 Alpha US: Puanlama Tabanlı Stratejik Radar")

tab1, tab2 = st.tabs(["🔍 Okyanus Taraması", "📈 Grafik Analiz"])

with tab1:
    st.markdown("5'te 5 yapan hisse bulmak zordur. Bu panel kriterleri puanlayarak en yakın adayları listeler.")
    
    # Otomatik Liste Çekme (Yedekli)
    symbols = ["AAPL", "NVDA", "TSLA", "AROC", "PLTR", "AMD", "MSFT", "AMZN", "META", "GOOGL", "NFLX", "AVGO", "SMCI", "COIN", "MARA", "SHOP", "RIVN", "UBER"]
    
    if st.button("🚀 Puanlamalı Taramayı Başlat"):
        results = []
        bar = st.progress(0)
        for i, s in enumerate(symbols):
            res = analyze_with_score(s)
            if res: results.append(res)
            bar.progress((i + 1) / len(symbols))
        
        if results:
            df = pd.DataFrame(results).sort_values(by="Puan", ascending=False)
            # Görselleştirme
            def color_score(val):
                if "5/5" in val: return 'background-color: #1ed760; color: black; font-weight: bold'
                if "4/5" in val: return 'background-color: #f1c40f; color: black'
                return ''

            st.dataframe(df.style.applymap(color_score, subset=['Puan']), use_container_width=True)

with tab2:
    ticker = st.text_input("Grafik:", "AROC").upper()
    tv_html = f"""
    <div style="height:600px;"><script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
    <script type="text/javascript">new TradingView.widget({{"autosize": true,"symbol": "{ticker}","interval": "D","timezone": "America/New_York","theme": "dark","style": "1","locale": "tr","container_id": "tv_v10"}});</script>
    <div id="tv_v10" style="height:100%;"></div></div>
    """
    components.html(tv_html, height=600)
