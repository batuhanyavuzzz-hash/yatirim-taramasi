import streamlit as st
import pandas as pd
from tradingview_ta import TA_Handler, Interval
import streamlit.components.v1 as components
import requests
import io

# Sayfa Ayarları
st.set_page_config(page_title="US Market Ocean Scanner", layout="wide")

# --- TÜM AMERİKA LİSTESİNİ ÇEKEN FONKSİYON ---
@st.cache_data(ttl=86400) # Listeyi günde bir kez günceller
def get_all_us_symbols():
    """Tüm US borsalarındaki aktif sembolleri çeker."""
    try:
        # NASDAQ ve NYSE listesini sağlayan güvenilir bir CSV kaynağı
        url = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/all_tickers.txt"
        response = requests.get(url)
        symbols = response.text.splitlines()
        # Temizlik: Gereksiz boşlukları ve çift isimleri temizle
        return [s.strip().upper() for s in symbols if len(s.strip()) > 0 and "^" not in s]
    except:
        return ["AAPL", "NVDA", "TSLA", "AROC", "PLTR", "AMD", "MSFT", "AMZN"]

def constitution_engine(symbol):
    """Anayasa Denetleyicisi: Trend + Hacim + RSI"""
    try:
        handler = TA_Handler(
            symbol=symbol,
            screener="america",
            exchange="AMERICA",
            interval=Interval.INTERVAL_1_DAY
        )
        ind = handler.get_analysis().indicators
        
        # Matematiksel Kriterler
        price = ind["close"]
        ma50, ma150, ma200 = ind["SMA50"], ind["SMA100"], ind["SMA200"]
        rsi = ind["RSI"]
        vol = ind["volume"]
        avg_vol = ind.get("average_volume_10d", vol)

        # 1. Trend Template (MA150 ve MA200 üstü, MA100 > MA200)
        is_trending = price > ma150 and price > ma200 and ma100 > ma200
        # 2. Hacim Onayı (%20 ve üzeri artış)
        vol_confirm = vol > (avg_vol * 1.2)
        # 3. Momentum (RSI 55 üstü)
        is_strong = rsi > 55

        if is_trending:
            status = "🔥 HACİMLİ ONAY" if vol_confirm and is_strong else ("✅ TREND UYGUN" if is_strong else "📊 İZLEMEDE")
            return {
                "Hisse": symbol,
                "Fiyat": round(price, 2),
                "Hacim Gücü": f"%{round(((vol/avg_vol)-1)*100, 1)}",
                "RSI": round(rsi, 1),
                "VCP": "🎯 SIKIŞMA" if ind["ATR"] < (sum([ind["ATR"]]*5)/5) else "NORMAL",
                "Sonuç": status
            }
    except:
        return None

# --- ARAYÜZ ---
st.title("🌊 US Market Ocean Scanner")
st.markdown("Amerikan Borsalarındaki (NYSE/NASDAQ/AMEX) tüm hisseleri anayasaya göre tarar.")

tab1, tab2 = st.tabs(["🔍 Dev Tarama", "📈 Grafik Detay"])

with tab1:
    col1, col2 = st.columns([1, 2])
    with col1:
        # Tarama Aralığı (Sistem donmasın diye bölümlere ayırıyoruz)
        all_symbols = get_all_us_symbols()
        st.write(f"Toplam Bulunan Hisse: **{len(all_symbols)}**")
        start_idx = st.number_input("Kaçıncı hisseden başlasın?", 0, len(all_symbols), 0)
        limit = st.slider("Kaç adet hisse taransın?", 50, 500, 100)
        
    if st.button("🚀 Okyanusa Ağı At"):
        subset = all_symbols[start_idx : start_idx + limit]
        progress_bar = st.progress(0)
        status_text = st.empty()
        matches = []

        for i, sym in enumerate(subset):
            status_text.text(f"Analiz ediliyor ({i+1}/{len(subset)}): {sym}")
            res = constitution_engine(sym)
            if res:
                matches.append(res)
            progress_bar.progress((i + 1) / len(subset))
        
        status_text.text("Tarama Tamamlandı!")
        
        if matches:
            df = pd.DataFrame(matches)
            # Sadece 'Trend Uygun' ve 'Hacimli Onay' olanları göster
            filtered_df = df[df['Sonuç'].str.contains("✅|🔥")]
            if not filtered_df.empty:
                st.success(f"Anayasa kriterlerine uyan {len(filtered_df)} fırsat yakalandı!")
                st.dataframe(filtered_df.style.applymap(
                    lambda x: 'background-color: #1ed760; color: black;' if '🔥' in str(x) else '',
                    subset=['Sonuç']
                ), use_container_width=True)
            else:
                st.warning("Bu aralıkta anayasaya tam uyan hisse bulunamadı.")
        else:
            st.error("Hiçbir hisse kriterlere takılmadı.")

with tab2:
    ticker = st.text_input("Grafik İncele:", "AROC").upper()
    tv_html = f"""
    <div style="height:600px;"><script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
    <script type="text/javascript">new TradingView.widget({{"autosize": true,"symbol": "{ticker}","interval": "D","timezone": "America/New_York","theme": "dark","style": "1","locale": "tr","container_id": "tv_v9"}});</script>
    <div id="tv_v9" style="height:100%;"></div></div>
    """
    components.html(tv_html, height=600)
