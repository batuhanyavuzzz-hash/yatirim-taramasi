import streamlit as st
import pandas as pd
from tradingview_ta import TA_Handler, Interval
import streamlit.components.v1 as components
import requests
import io

st.set_page_config(page_title="Alpha V12 - Market Ocean", layout="wide")

# --- DİNAMİK LİSTE ÇEKİCİ (S&P 500 + NASDAQ 100) ---
@st.cache_data(ttl=86400) # Listeyi 24 saatte bir günceller
def get_massive_watchlist():
    try:
        # S&P 500 Listesi
        sp500_url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        sp500 = pd.read_html(io.StringIO(requests.get(sp500_url).text))[0]['Symbol'].tolist()
        # NASDAQ 100 Listesi
        ndx_url = 'https://en.wikipedia.org/wiki/Nasdaq-100'
        ndx = pd.read_html(io.StringIO(requests.get(ndx_url).text))[4]['Ticker'].tolist()
        
        # Listeleri birleştir ve temizle (noktaları tire yap: BRK.B -> BRK-B)
        full_list = list(set(sp500 + ndx))
        return [s.replace('.', '-') for s in full_list]
    except:
        # Hata olursa yedek güvenli liste
        return ["AAPL", "NVDA", "TSLA", "AROC", "PLTR", "AMD", "MSFT", "META"]

def analyze_engine(symbol):
    """Anayasa Puanlama Motoru"""
    for ex in ["NASDAQ", "NYSE", "AMERICA"]:
        try:
            handler = TA_Handler(symbol=symbol, screener="america", exchange=ex, interval=Interval.INTERVAL_1_DAY)
            ind = handler.get_analysis().indicators
            if not ind: continue

            price = ind["close"]
            ma50, ma100, ma200 = ind["SMA50"], ind["SMA100"], ind["SMA200"]
            rsi, vol = ind["RSI"], ind["volume"]
            avg_vol = ind.get("average_volume_10d", vol)

            # --- 5 MADDELİK ANAYASA PUANLAMASI ---
            score = 0
            if price > ma200: score += 1      # 1. Trend
            if ma100 > ma200: score += 1      # 2. Dizilim
            if ma50 > ma100: score += 1       # 3. Momentum
            if rsi > 55: score += 1           # 4. Güç
            if vol > (avg_vol * 1.2): score += 1 # 5. Hacim Onayı

            if score >= 3: # En az 3 puan alanları göster (kalabalığı önlemek için)
                return {
                    "Hisse": symbol,
                    "Puan": f"{score}/5",
                    "Fiyat": round(price, 2),
                    "Hacim": f"%{round(((vol/avg_vol)-1)*100, 1)}",
                    "RSI": round(rsi, 1),
                    "VCP": "🎯 DARALMA" if ind["ATR"] < (sum([ind["ATR"]]*5)/5) else "NORMAL"
                }
        except: continue
    return None

# --- ARAYÜZ ---
st.title("🌊 Alpha Market Ocean: S&P 500 & Nasdaq 100")

tab1, tab2 = st.tabs(["🔍 Dev Tarama", "📊 Teknik Analiz"])

with tab1:
    all_tickers = get_massive_watchlist()
    st.write(f"Sistemde yüklü toplam hisse: **{len(all_tickers)}**")
    
    col1, col2 = st.columns(2)
    with col1:
        batch_size = st.slider("Tarama Aralığı (Hisse Sayısı)", 50, len(all_tickers), 100)
    with col2:
        start_from = st.number_input("Kaçıncı hisseden başlasın?", 0, len(all_tickers), 0)

    if st.button("🚀 Okyanusu Tara"):
        subset = all_tickers[start_from : start_from + batch_size]
        results = []
        bar = st.progress(0)
        status = st.empty()
        
        for i, s in enumerate(subset):
            status.text(f"Analiz ediliyor ({i+1}/{len(subset)}): {s}")
            res = analyze_engine(s)
            if res: results.append(res)
            bar.progress((i + 1) / len(subset))
        
        if results:
            df = pd.DataFrame(results).sort_values(by="Puan", ascending=False)
            st.success(f"Kriterlere yakın {len(results)} hisse bulundu!")
            st.dataframe(df, use_container_width=True)
        else:
            st.error("Bu aralıkta anayasaya uyan hisse bulunamadı. Filtreler çok sert!")

with tab2:
    check_sym = st.text_input("Hisse Kodu:", "AROC").upper()
    tv_html = f"""<div style="height:600px;"><script src="https://s3.tradingview.com/tv.js"></script>
    <script>new TradingView.widget({{"autosize": true,"symbol": "{check_sym}","interval": "D","theme": "dark","style": "1","locale": "tr","container_id": "v12"}});</script>
    <div id="v12" style="height:100%;"></div></div>"""
    components.html(tv_html, height=620)
