import streamlit as st
import pandas as pd
from tradingview_ta import TA_Handler, Interval
import streamlit.components.v1 as components
import io
import requests

st.set_page_config(page_title="Alpha Screener Pro", layout="wide")

# --- YEDEK LİSTE (Wikipedia hata verirse devreye girer) ---
DEFAULT_TICKERS = ["AAPL", "NVDA", "TSLA", "AROC", "PLTR", "AMD", "MSFT", "META", "AMZN", "NFLX", "GOOGL", "AVGO", "SMCI"]

@st.cache_data(ttl=3600)
def get_tickers():
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        html = requests.get(url, timeout=5).text
        df = pd.read_html(io.StringIO(html))[0]
        return df['Symbol'].tolist()
    except Exception as e:
        st.warning(f"Wikipedia bağlantı hatası, yedek liste kullanılıyor: {e}")
        return DEFAULT_TICKERS

def analyze_engine(symbol):
    """Teknik analiz motoru - Trend + Hacim + VCP"""
    try:
        # TradingView üzerinden verileri çek
        handler = TA_Handler(
            symbol=symbol,
            screener="america",
            exchange="AMERICA", # Geniş tarama için AMERICA kullanılır
            interval=Interval.INTERVAL_1_DAY
        )
        ind = handler.get_analysis().indicators
        
        # 1. Trend Template Filtreleri
        price = ind["close"]
        ma50, ma150, ma200 = ind["SMA50"], ind["SMA100"], ind["SMA200"]
        
        is_uptrend = price > ma150 and price > ma200 and ma150 > ma200
        
        # 2. Hacim Onayı Kontrolü (Hacim Patlaması)
        curr_vol = ind.get("volume", 0)
        avg_vol = ind.get("average_volume_10d", 1) # Sıfıra bölme hatasını önlemek için 1
        vol_ratio = curr_vol / avg_vol
        
        # 3. Momentum (RSI)
        rsi = ind.get("RSI", 0)

        # Sadece Trendi Güçlü Olanları Döndür
        if is_uptrend:
            status = "🔥 HACİMLİ ONAY" if vol_ratio > 1.2 else "✅ UYGUN"
            return {
                "Hisse": symbol,
                "Fiyat": round(price, 2),
                "Hacim Gücü": f"%{round((vol_ratio-1)*100, 1)}",
                "RSI": round(rsi, 1),
                "Durum": status
            }
    except:
        return None

# --- ARAYÜZ ---
st.title("🦅 Stratejik Borsa Radarı")

tab1, tab2 = st.tabs(["🔍 Canlı Tarama", "📊 Detaylı Grafik"])

with tab1:
    col1, col2 = st.columns([1, 4])
    with col1:
        scan_limit = st.slider("Tarama Hızı (Hisse Sayısı)", 20, 500, 50)
        start_button = st.button("🚀 Radarı Çalıştır")
    
    if start_button:
        all_symbols = get_tickers()
        selected_symbols = all_symbols[:scan_limit] # İlk aşamada limiti düşük tutabiliriz
        
        results = []
        progress_text = st.empty()
        bar = st.progress(0)
        
        for i, sym in enumerate(selected_symbols):
            progress_text.text(f"Analiz ediliyor: {sym}")
            res = analyze_engine(sym)
            if res:
                results.append(res)
            bar.progress((i + 1) / len(selected_symbols))
            
        if results:
            st.success(f"{len(results)} potansiyel fırsat bulundu.")
            st.dataframe(pd.DataFrame(results), use_container_width=True)
        else:
            st.error("Kriterlere uyan hisse bulunamadı. Filtreler çok sert olabilir.")

with tab2:
    target = st.text_input("İncelemek istediğiniz hisse:", "AROC").upper()
    tv_html = f"""
    <div style="height:550px;"><script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
    <script type="text/javascript">
    new TradingView.widget({{"autosize": true,"symbol": "{target}","interval": "D","timezone": "America/New_York","theme": "dark","style": "1","locale": "tr","container_id": "tv_v4"}});
    </script><div id="tv_v4" style="height:100%;"></div></div>
    """
    components.html(tv_html, height=560)
