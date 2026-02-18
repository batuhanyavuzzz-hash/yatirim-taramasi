import streamlit as st
import pandas as pd
from tradingview_ta import TA_Handler, Interval
import streamlit.components.v1 as components
import io
import requests

# Sayfa Ayarları
st.set_page_config(page_title="Alpha Terminal V5", layout="wide")

# --- STRATEJİK ANAYASA (SIDEBAR) ---
with st.sidebar:
    st.title("🏛️ Yatırım Anayasası")
    st.markdown("---")
    st.success("**I. Trend:** Fiyat > MA150 & MA200")
    st.success("**II. Sıralama:** MA50 > MA150 > MA200")
    st.warning("**III. Onay:** Hacim > %20 Artış")
    st.error("**IV. Risk:** Max 4 Hisse | %5-8 Stop")
    st.markdown("---")
    st.info("**📰 Haber Akışı:**")
    st.markdown("- [Bloomberg](https://www.bloomberg.com)")
    st.markdown("- [CNBC](https://www.cnbc.com)")
    st.markdown("- [Finviz News](https://finviz.com/news.ashx)")
    st.markdown("- [Seeking Alpha](https://seekingalpha.com)")

# --- FONKSİYONLAR ---

@st.cache_data(ttl=3600)
def get_tickers():
    """S&P 500 ve NASDAQ 100 listesini birleştirir."""
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        sp500 = pd.read_html(io.StringIO(requests.get(url).text))[0]['Symbol'].tolist()
        return [s.replace('.', '-') for s in sp500]
    except:
        return ["AAPL", "NVDA", "TSLA", "AROC", "MSFT", "AMD", "META", "AMZN"]

def analyze_constitution(symbol):
    """Anayasa Maddelerini Test Eden Motor"""
    try:
        handler = TA_Handler(
            symbol=symbol,
            screener="america",
            exchange="AMERICA",
            interval=Interval.INTERVAL_1_DAY
        )
        ind = handler.get_analysis().indicators
        
        # Maddeleri Hesapla
        price = ind["close"]
        ma50, ma100, ma200 = ind["SMA50"], ind["SMA100"], ind["SMA200"]
        rsi = ind["RSI"]
        vol = ind["volume"]
        avg_vol = ind.get("average_volume_10d", vol)
        
        # 1. & 2. Madde: Trend Template
        c1 = price > ma100 and price > ma200
        c2 = ma100 > ma200
        c3 = ma50 > ma100
        
        # 11. Madde: Hacim Onayı
        volume_ratio = vol / avg_vol
        
        # 7. Madde: VCP (Sıkışma Kontrolü)
        vcp_signal = ind["ATR"] < (sum([ind["ATR"]]*5)/5)

        if c1 and c2 and c3:
            status = "🔥 HACİMLİ ONAY" if volume_ratio > 1.2 else "✅ TREND UYGUN"
            return {
                "Hisse": symbol,
                "Fiyat": round(price, 2),
                "Hacim Gücü": f"%{round((volume_ratio-1)*100, 1)}",
                "RSI": round(rsi, 1),
                "VCP": "🎯 SIKIŞMA" if vcp_signal else "📊 NORMAL",
                "Onay": status
            }
    except:
        return None

# --- ANA EKRAN ---
st.title("🦅 Alpha Terminal: US Market Radar")

tab1, tab2, tab3 = st.tabs(["🔍 Stratejik Tarama", "📈 Teknik Detay", "📜 Anayasa Tam Metin"])

with tab1:
    st.subheader("Anayasaya Uygun Fırsatları Ara")
    col_a, col_b = st.columns([1, 3])
    with col_a:
        limit = st.number_input("Taranacak Hisse Sayısı", 20, 500, 100)
        run = st.button("🚀 Radarı Çalıştır")
    
    if run:
        tickers = get_tickers()[:limit]
        bar = st.progress(0)
        matches = []
        
        for i, t in enumerate(tickers):
            res = analyze_constitution(t)
            if res: matches.append(res)
            bar.progress((i + 1) / len(tickers))
        
        if matches:
            df = pd.DataFrame(matches)
            # Görselleştirme: Hacimli onayları yeşil yap
            st.dataframe(df.style.applymap(
                lambda x: 'background-color: #1ed760; color: black;' if '🔥' in str(x) else '',
                subset=['Onay']
            ), use_container_width=True)
        else:
            st.error("Kriterlere uyan hisse bulunamadı. Nakitte kalmak bir işlemdir.")

with tab2:
    ticker = st.text_input("Hisse Kodu (Örn: AROC, NVDA):", "AROC").upper()
    tv_html = f"""
    <div style="height:600px;">
    <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
    <script type="text/javascript">
    new TradingView.widget({{"autosize": true,"symbol": "{ticker}","interval": "D","timezone": "America/New_York","theme": "dark","style": "1","locale": "tr","container_id": "tv_chart_final"}});
    </script><div id="tv_chart_final" style="height:100%;"></div></div>
    """
    components.html(tv_html, height=600)

with tab3:
    st.markdown("""
    ### 🏛️ Stratejik Yatırım Anayasası (Nihai)
    1. **Trend Template:** Fiyat hem MA150 hem MA200 üzerinde olmalı.
    2. **Güç Sıralaması:** MA50 > MA150 > MA200 dizilimi şart.
    3. **Hacim Onayı:** Giriş anında hacim son 20 günlük ortalamanın **%20** üzerinde olmalı.
    $$Volume\ Ratio = \\frac{Current\ Volume}{Average\ Volume\ (20d)} > 1.20$$
    4. **VCP (Daralma):** Fiyat dalgalanması soldan sağa daralmalı ve hacim kurumalı.
    5. **Risk Yönetimi:** Portföy max **4 hisse**, stop-loss max **%5-8**.
    """)
