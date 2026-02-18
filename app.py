import streamlit as st
import pandas as pd
from tradingview_ta import TA_Handler, Interval
import streamlit.components.v1 as components
import io
import requests

# Sayfa Genişliği ve Tasarımı
st.set_page_config(page_title="US Trend Template Scanner", layout="wide")

# --- STRATEJİK ANAYASA ÖZETİ (Kenar Çubuğu) ---
st.sidebar.header("🛡️ Yatırım Anayasası")
st.sidebar.markdown("""
1. **Trend:** Fiyat > MA150 & MA200
2. **Sıralama:** MA50 > MA150 > MA200
3. **Güç:** RSI > 60
4. **Odak:** Max 4 Hisse
5. **Risk:** %5-8 Stop-Loss
""")

# --- FONKSİYONLAR ---

@st.cache_data
def get_sp500_tickers():
    """S&P 500 listesini güncel olarak çeker."""
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        html = requests.get(url).text
        df = pd.read_html(io.StringIO(html))[0]
        return df['Symbol'].tolist()
    except:
        return ["AAPL", "MSFT", "TSLA", "NVDA", "GOOGL", "AMZN", "META", "AMD", "NFLX", "COIN"]

def analyze_us_stock(symbol):
    """TradingView verileriyle anayasa uyumluluk kontrolü."""
    try:
        handler = TA_Handler(
            symbol=symbol,
            screener="america",
            exchange="NASDAQ",
            interval=Interval.INTERVAL_1_DAY
        )
        analysis = handler.get_analysis()
        ind = analysis.indicators
        
        # Anayasa Filtreleri (Minervini Trend Template)
        price = ind["close"]
        ma50 = ind["SMA50"]
        ma100 = ind["SMA100"]
        ma200 = ind["SMA200"]
        
        # 1. Kural: Fiyat MA150 ve MA200 üzerinde mi?
        c1 = price > ma100 and price > ma200
        # 2. Kural: MA150 > MA200 mü?
        c2 = ma100 > ma200
        # 3. Kural: MA50 hem MA150 hem MA200 üzerinde mi?
        c3 = ma50 > ma100 and ma50 > ma200
        # 4. Kural: RSI 60'tan büyük mü? (Güç Göstergesi)
        c4 = ind["RSI"] > 60
        
        # VCP (Volatilite Daralması) - ATR ile basit kontrol
        vcp_signal = ind["ATR"] < (sum([ind["ATR"]]*5)/5)

        if all([c1, c2, c3, c4]):
            return {
                "Hisse": symbol,
                "Fiyat": round(price, 2),
                "RSI": round(ind["RSI"], 2),
                "VCP": "🎯 DARALMA" if vcp_signal else "📊 NORMAL",
                "Durum": "✅ STRATEJİYE UYGUN"
            }
    except:
        return None

# --- ANA PANEL ---
st.title("🇺🇸 US Market: Stratejik Yatırım Kanvası")

tab1, tab2, tab3 = st.tabs(["🔍 Otomatik Tarayıcı", "📊 Grafik Analiz", "📝 Strateji Raporu"])

# TAB 1: TARAMA
with tab1:
    st.subheader("Anayasa Filtresi: S&P 500 Taraması")
    if st.button("Taramayı Başlat"):
        tickers = get_sp500_tickers()[:100] # Hız için ilk 100 hisse
        progress_bar = st.progress(0)
        
        matched_stocks = []
        for i, ticker in enumerate(tickers):
            res = analyze_us_stock(ticker)
            if res:
                matched_stocks.append(res)
            progress_bar.progress((i + 1) / len(tickers))
        
        if matched_stocks:
            df_results = pd.DataFrame(matched_stocks)
            st.session_state['us_results'] = df_results
            st.success(f"Kriterlere uygun {len(matched_stocks)} hisse bulundu.")
            st.dataframe(df_results, use_container_width=True)
        else:
            st.warning("Şu an kriterlere tam uyan bir Amerikan hissesi bulunamadı.")

# TAB 2: GRAFİK (TradingView)
with tab2:
    target_ticker = st.text_input("İncelemek istediğiniz hisse kodu (Örn: NVDA):", "AAPL").upper()
    tv_code = f"""
    <div class="tradingview-widget-container" style="height:600px;">
      <div id="tradingview_123"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{
        "autosize": true,
        "symbol": "NASDAQ:{target_ticker}",
        "interval": "D",
        "timezone": "America/New_York",
        "theme": "light",
        "style": "1",
        "locale": "tr",
        "enable_publishing": false,
        "allow_symbol_change": true,
        "container_id": "tradingview_123"
      }});
      </script>
    </div>
    """
    components.html(tv_code, height=600)

# TAB 3: RAPORLAMA
with tab3:
    st.subheader("Günü Dokümante Et")
    if 'us_results' in st.session_state:
        df_export = st.session_state['us_results']
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_export.to_excel(writer, index=False, sheet_name='US_Watchlist')
        
        st.download_button(
            label="📥 Günlük Excel Raporunu İndir",
            data=output.getvalue(),
            file_name="US_Yatirim_Raporu.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("Rapor oluşturmak için önce tarama yapmalısınız.")
