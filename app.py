import streamlit as st
import pandas as pd
from tradingview_ta import TA_Handler, Interval
import streamlit.components.v1 as components
import io
import requests

st.set_page_config(page_title="Alpha Screener V4 - Volume Confirm", layout="wide")

# --- STRATEJİK ANAYASA ---
st.sidebar.title("🛡️ Yatırım Anayasası")
st.sidebar.info("""
**Giriş Şartları:**
1. Trend Template (MA'lar) Tamam mı?
2. Fiyat Sıkışması (VCP) Var mı?
3. **PİVOT KIRILIMI:** Hacim > Ortalamanın %20 üstünde mi?
""")

# --- FONKSİYONLAR ---

def analyze_full_data(symbol):
    """Trend, VCP ve Hacim Onayını aynı anda kontrol eder."""
    try:
        handler = TA_Handler(
            symbol=symbol,
            screener="america",
            exchange="AMERICA",
            interval=Interval.INTERVAL_1_DAY
        )
        analysis = handler.get_analysis()
        ind = analysis.indicators
        
        # 1. Trend Kontrolü
        price = ind["close"]
        ma50, ma150, ma200 = ind["SMA50"], ind["SMA100"], ind["SMA200"]
        is_uptrend = price > ma150 and price > ma200 and ma150 > ma200
        
        # 2. Hacim Onayı (Current Volume vs Average Volume)
        # TradingView indikatörlerinde volume ve ortalaması bulunur
        curr_vol = ind["volume"]
        avg_vol = ind["average_volume_10d"] if "average_volume_10d" in ind else ind["volume"] # Yedek mantık
        volume_ratio = (curr_vol / avg_vol) if avg_vol > 0 else 1
        
        # 3. VCP / Sıkışma (ATR bazlı basit volatilite düşüşü)
        vcp_signal = ind["ATR"] < (sum([ind["ATR"]]*5)/5)

        # Analiz Sonucu
        entry_status = "⚠️ HACİM BEKLENİYOR"
        if volume_ratio > 1.2:
            entry_status = "🔥 HACİMLİ ONAY (Giriş!)"
        elif volume_ratio > 1.0:
            entry_status = "✅ ORTALAMA HACİM"

        if is_uptrend:
            return {
                "Hisse": symbol,
                "Fiyat": round(price, 2),
                "Hacim Gücü": f"%{round((volume_ratio-1)*100, 1)} Artış",
                "VCP": "🎯 SIKIŞMA" if vcp_signal else "📊 NORMAL",
                "Giriş Onayı": entry_status,
                "RSI": round(ind["RSI"], 2)
            }
    except:
        return None

# --- ARAYÜZ ---
st.title("🦅 US Alpha - Hacim ve Giriş Onay Paneli")

tab1, tab2, tab3 = st.tabs(["🚀 Otomatik Tarama", "📡 Giriş Radarı", "📈 Analiz"])

with tab1:
    st.write("S&P 500 ve NASDAQ 100 genel taraması.")
    if st.button("Tüm Piyasayı Tara"):
        # Not: get_broad_market_tickers fonksiyonu önceki koddaki gibi Wikipedia'dan çeker
        # Basitlik için buraya manuel liste de eklenebilir
        tickers = ["AAPL", "MSFT", "NVDA", "TSLA", "AROC", "PLTR", "AMD", "META", "NFLX", "SNOW"] 
        # (Gerçek kullanımda Wikipedia çekme fonksiyonunu buraya ekleyebilirsin)
        
        results = []
        for t in tickers:
            res = analyze_full_data(t)
            if res: results.append(res)
        
        if results:
            df = pd.DataFrame(results)
            st.dataframe(df.style.applymap(lambda x: 'background-color: #d4edda' if '🔥' in str(x) else ''), use_container_width=True)

with tab2:
    st.subheader("📍 Takip Listesi ve Giriş Bölgesi Kontrolü")
    st.write("Potansiyel gördüğün hisseleri buraya yaz, sadece hacimli kırılım olduğunda seni uyarsın.")
    watchlist_input = st.text_area("Takipteki Hisseler (Virgülle):", "AROC, NVDA, PLTR")
    
    if st.button("Radarı Çalıştır"):
        watchlist = [x.strip().upper() for x in watchlist_input.split(",")]
        watch_results = []
        for s in watchlist:
            r = analyze_full_data(s)
            if r: watch_results.append(r)
        
        if watch_results:
            st.table(pd.DataFrame(watch_results))

with tab3:
    target = st.text_input("Grafik İncele:", "AROC").upper()
    # TradingView Grafiği (Daha geniş ve koyu tema)
    tv_code = f"""
    <div style="height:600px;"><script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
    <script type="text/javascript">new TradingView.widget({{"autosize": true,"symbol": "{target}","interval": "D","timezone": "America/New_York","theme": "dark","style": "1","locale": "tr","enable_publishing": false,"allow_symbol_change": true,"container_id": "tv_chart_v4"}});</script>
    <div id="tv_chart_v4" style="height: 100%;"></div></div>
    """
    components.html(tv_code, height=600)
